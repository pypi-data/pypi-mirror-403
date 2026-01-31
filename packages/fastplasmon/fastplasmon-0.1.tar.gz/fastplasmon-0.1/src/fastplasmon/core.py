import numpy as np
from scipy.linalg import eigh
from numba import njit, prange
import trimesh

class ArbitraryShapeDipolarSolver:
    """
    Fast dipolar solver for arbitrary nanoparticle geometries
    """
    
    def __init__(self, vertices, faces, epsilon, medium_epsilon=1.0, exact=False):

        self.eps = complex(epsilon)  # nanoparticle permittivity
        self.eps_m = complex(medium_epsilon) # medium permittivity

        self.M_matrix = None
        self.sigma = None  # surface charge distribution

        self.eps_eff_modes = None
        self.kappa_modes = None
        self.polarizability = None

        self.volume = None
        self.face_areas = None
        self.face_normals = None
        self.face_centers = None
        self.surface_area = None
        self.centroid = None
        self.rel_centers = None
        self.dimensions = None
        self.vertices = np.array(vertices)
        self.faces = np.array(faces)

        self.alpha_axis = None
        self.dipole_moments = None

        self.R = None  # rotation matrix from eigen decomposition
        self.L_eff = None  # effective depolarization factors

        self.E0 = None

        self._repair_and_orient_mesh()

        # Compute geometric properties
        self._compute_geometry()

    def _compute_geometry(self):
        """Compute geometric properties of the mesh"""
        # Face centers and areas
        face_vertices = self.vertices[self.faces]
        self.face_centers = np.mean(face_vertices, axis=1)
        
        # Face normals and areas using cross product
        v1 = face_vertices[:, 1] - face_vertices[:, 0]
        v2 = face_vertices[:, 2] - face_vertices[:, 0]
        face_normals = np.cross(v1, v2)
        self.face_areas = 0.5 * np.linalg.norm(face_normals, axis=1)
        
        # Normalize face normals
        norms = np.linalg.norm(face_normals, axis=1)
        norms[norms == 0] = 1  # Avoid division by zero
        self.face_normals = face_normals / norms[:, np.newaxis]
        
        # Total surface area and volume (using divergence theorem)
        self.surface_area = np.sum(self.face_areas)
        self.volume = np.abs(np.sum(self.face_centers * self.face_normals * 
                                   self.face_areas[:, np.newaxis])) / 3
        
        # Centroid
        self.centroid = np.sum(self.face_centers * self.face_areas[:, np.newaxis], axis=0) / self.surface_area

        # Center coordinates relative to centroid
        self.rel_centers = self.face_centers - self.centroid

        # characteristic lengths along x, y, z (nanoparticle extents)
        # Use the bounding box of all vertices
        mins = np.min(self.vertices, axis=0)  # (3,)
        maxs = np.max(self.vertices, axis=0)  # (3,)
        self.dimensions = maxs - mins         # lengths along x, y, z

        # Principal lengths along x,y,z (must be set elsewhere in the class)
        self.Lx, self.Ly, self.Lz = np.asarray(self.dimensions, float)

        
        print(f"Geometry computed:")
        print(f"  Faces: {len(self.faces)}")
        print(f"  Surface area: {self.surface_area:.6f}")
        print(f"  Volume: {self.volume:.6f}")
        print(f"  Centroid: [{self.centroid[0]:.3f}, {self.centroid[1]:.3f}, {self.centroid[2]:.3f}]")

    def _repair_and_orient_mesh(self):
        """
        Ensure the mesh is watertight and consistently oriented.
        This is critical for NP operator eigenvalues staying in (-1/2, 1/2).
        """
        mesh = trimesh.Trimesh(vertices=self.vertices, faces=self.faces, process=False)

        # Try to repair common issues
        mesh.update_faces(mesh.unique_faces())
        mesh.remove_unreferenced_vertices()

        # Attempt to make winding consistent and normals outward
        trimesh.repair.fix_winding(mesh)
        trimesh.repair.fix_normals(mesh)

        # If the mesh is not watertight, NP theory assumptions break.
        if not mesh.is_watertight:
            raise RuntimeError("Mesh is not watertight (closed). NP eigenvalues may be unphysical.")

        # Replace stored geometry with repaired mesh
        self.vertices = mesh.vertices.view(np.ndarray)
        self.faces = mesh.faces.view(np.ndarray)
            
    def compute_interaction_matrix(self):
        """
        Compute the 3x3 dipolar interaction matrix through geometric-moments approximation
        (fast, no Python loops)
        """

        rc = np.asarray(self.rel_centers, dtype=np.float64)   # (N,3)
        A  = np.asarray(self.face_areas,  dtype=np.float64)   # (N,)

        # M_ij = sum_k rc[k,i]*rc[k,j]*A[k]
        # => (rc^T * A) @ rc
        M = (rc.T * A) @ rc                                   # (3,3), float64
        self.M_matrix = M / (3.0 * self.volume)   # float64


    def compute_interaction_matrix_exact(self):
        """Compute exact interaction matrix - vectorized with blocking"""
        N = len(self.face_centers)
        M_matrix = np.zeros((3,3), dtype=complex)
        
        # Precompute all pairwise distances and vectors (memory intensive but fast)
        ra_grid, rb_grid = np.meshgrid(np.arange(N), np.arange(N), indexing='ij')
        R = self.face_centers[ra_grid] - self.face_centers[rb_grid]  # (N,N,3)
        dist = np.linalg.norm(R, axis=-1)  # (N,N)
        
        # Mask self-interactions
        mask = dist > 1e-15
        
        # Vectorized kernel computation
        R_masked = R[mask]
        dist_masked = dist[mask]
        nr_masked = self.face_normals[rb_grid[mask]]
        
        kernel = -3.0 * np.sum(nr_masked * R_masked, axis=-1) / (dist_masked ** 5)
        
        # Weighted contributions: ra[i] * kernel * rb[j] * Aa * Ab
        Aa_masked = self.face_areas[ra_grid[mask]]
        Ab_masked = self.face_areas[rb_grid[mask]]
        
        # ra_masked: (N*N_mask, 3), rb_masked: (N*N_mask, 3)
        ra_masked = self.face_centers[ra_grid[mask]]
        rb_masked = self.face_centers[rb_grid[mask]]
        
        contrib = kernel * Aa_masked * Ab_masked  # (N*N_mask,)
        
        # Outer products summed over all pairs: sum(ra * contrib * rb^T)
        for i in range(3):
            for j in range(3):
                M_matrix[i,j] = np.sum(ra_masked[:,i] * contrib * rb_masked[:,j])
        
        self.M_matrix = M_matrix / (3 * self.volume)
        
        print(f"M_full = ")
        for i in range(3):
            print(f"  [{self.M_matrix[i,0].real:8.4f} {self.M_matrix[i,1].real:8.4f} {self.M_matrix[i,2].real:8.4f}]")

    def solve_dipolar_coefficients(self, external_field, verbose=False):
        """
        Solve for dipolar coefficients
        """
        self.E0 = np.array(external_field, dtype=complex)


        # Real part only: Physical depolarization factors are defined from the geometric second-moment tensor,
        # which is purely real (position × position × area). Imaginary parts in M_matrix come from numerical
        # noise in the exact method, not physics. Using .real extracts the correct geometry

        evals, R = np.linalg.eigh(self.M_matrix.real) # returns the eigenvalues and rotation matrix

        self.R = R  # store rotation matrix
        self.L_eff = (1.0/evals) / np.sum((1.0/evals))   # effective depolarization factors


        E_loc = R @ self.E0

        eps_factor_axis = (self.eps - self.eps_m) / (self.eps_m + self.L_eff * (self.eps - self.eps_m))
        self.alpha_axis = 4 * np.pi * self.volume * eps_factor_axis   # 3 components

        if verbose:
            print(f'L_eff = [{self.L_eff[0]:.4f}, {self.L_eff[1]:.4f}, {self.L_eff[2]:.4f}]')

            print(f'Rotation matrix R = ')
            for i in range(3):
                print(f"  [{R[i,0].real:8.4f} {R[i,1].real:8.4f} {R[i,2].real:8.4f}]")

            print('alpha axis = ', self.alpha_axis)

        p_axis = self.alpha_axis * E_loc
        # rotate dipole back to lab frame
        self.dipole_moments = R.T @ p_axis
        
        return self.dipole_moments
    
    def surface_charge_distribution(self):
        """
        Reconstruct surface charge distribution
        """
        
        # σ(s) = (3/4πV) * p · r_rel  
        self.sigma = (3/(4*np.pi*self.volume)) * np.dot(self.rel_centers, self.dipole_moments.real)
        return self.sigma


    def projectK_modes(self, symmetrize_T=True, enforce_bounds=True):
        """
        Project K onto dipole subspace span{rx, ry, rz}.

        Produces 3 dipole-like modes (kappa_n) intrinsic to geometry:
            T c = kappa G c

        IMPORTANT NUMERICS / PHYSICS NOTES
        - For the electrostatic Neumann–Poincaré (NP) operator on a closed surface,
        physical eigenvalues satisfy -1/2 < kappa < 1/2 (in the standard convention).
        - A collocation BEM discretization can make the reduced 3x3 problem non-self-adjoint,
        which may produce spurious kappa > 1/2.
        Remedy: symmetrize the reduced matrix T in the same inner product:
            T <- (T + T^T)/2
        and solve the generalized symmetric eigenproblem.
        - Use centered coordinates in the basis (rel_centers) to avoid contamination.

        Stores:
        self.kappa_modes  (3,)
        self.C_modes      (3,3) columns are coeff vectors in basis {rx,ry,rz}
        self.p_modes      (3,3) columns are dipole moment vectors in lab frame
        self.R_dip        (3,3) columns are unit dipole directions (lab frame)
        self.w_dip        (3,)  oscillator-strength weights (normalized, sum=1)
        self.a_dip        (3,)  semi-extents along dipole directions (sorted)
        """
        # if self.K is None:
        #     raise RuntimeError("K not built. Call build_K() first.")
        
        if self.rel_centers is None:
            raise RuntimeError("rel_centers not set (need face centers minus centroid).")

        B = np.asarray(self.rel_centers, np.float64)
        W = np.asarray(self.face_areas,  np.float64)
        r = np.asarray(self.face_centers, np.float64)
        n = np.asarray(self.face_normals, np.float64)

        Kb = apply_K_to_B_numba(r, n, W, B)

        G = (B.T * W) @ B
        T = (B.T * W) @ Kb


        # Symmetrize the reduced operator to respect self-adjointness in the discrete inner product
        # This strongly suppresses spurious kappa outside (-1/2, 1/2).
        if symmetrize_T:
            T = 0.5 * (T + T.T)

        # Solve T c = kappa G c using a symmetric generalized eigensolver.
        # This assumes:
        #   (i) G is symmetric positive definite (area-weighted Gram matrix),
        #   (ii) T is symmetric in the same inner product.
        # In the continuous NP operator this symmetry is exact; in the discrete
        # collocation BEM we enforce it by explicit symmetrization of T above.

        try:
            kappa, C = eigh(T, G)                        # eigenvalues ascending
        except Exception:
            # Fallback: whitening via G^{-1/2} (still symmetric if T is symmetric)
            evals_G, evecs_G = np.linalg.eigh(G)
            if np.min(evals_G) <= 0:
                raise RuntimeError("G is not positive definite; check mesh/basis centering.")
            Gmhalf = (evecs_G * (1.0 / np.sqrt(evals_G))) @ evecs_G.T
            A = Gmhalf @ T @ Gmhalf
            kappa, U = np.linalg.eigh(A)
            C = Gmhalf @ U

        kappa = np.real(kappa)
        C = np.real(C)                                   # (3,3) columns are c_n

        # Optional: clip tiny numerical excursions (do NOT hide big violations)
        if enforce_bounds:
            # Only clip extremely small overshoots; large ones indicate K/diagonal convention is wrong.
            eps = 1e-8
            if np.any(kappa > 0.5 + 1e-3) or np.any(kappa < -0.5 - 1e-3):
                raise RuntimeError(
                    f"Unphysical kappa detected (outside (-1/2,1/2)): {kappa}. "
                    "Check K diagonal/jump term sign convention and near-field regularization."
                )
            kappa = np.clip(kappa, -0.5 + eps, 0.5 - eps)

        # ---- Build modal surface charges sigma_n = B c_n and their dipole moments p_n ----
        # p_n ~ ∫ r sigma dS ≈ Σ r_rel * sigma * A
        p_modes = np.zeros((3, 3), dtype=float)          # columns: p_n
        for n in range(3):
            sigma_n = B @ C[:, n]                         # (N,)
            p_n = np.sum(B * (sigma_n[:, None] * W[:, None]), axis=0)  # use B=rel_centers
            p_modes[:, n] = p_n

        # Unit dipole directions per mode (avoid QR mixing modes)
        R_dip = np.zeros((3, 3), dtype=float)
        for n in range(3):
            pn = p_modes[:, n]
            norm = np.linalg.norm(pn)
            if norm < 1e-30:
                # fallback direction if a mode has ~zero dipole moment (rare for dipole subspace)
                R_dip[:, n] = np.eye(3)[:, n]
            else:
                R_dip[:, n] = pn / norm

        # Oscillator-strength weights: squared dipole magnitudes
        w = np.sum(p_modes**2, axis=0)
        if np.sum(w) < 1e-30:
            w = np.ones(3)
        w = w / np.sum(w)

        # ---- Sort modes by semi-extent along their dipole directions (small -> large) ----
        rel_v = np.asarray(self.vertices, float) - np.asarray(self.centroid, float)[None, :]
        proj = rel_v @ R_dip                              # (Nv,3)
        a = np.max(np.abs(proj), axis=0)                  # (3,) semi-extents

        order = np.argsort(a)                             # small -> large (transverse first, longitudinal last)

        self.kappa_modes = kappa[order]
        self.C_modes = C[:, order]
        self.p_modes = p_modes[:, order]
        self.R_dip = R_dip[:, order]
        self.w_dip = w[order]
        self.a_dip = a[order]

        return self.kappa_modes, self.R_dip, self.a_dip, self.w_dip

    
    def eps_modes(self):
        """
        Convert projected-K eigenvalues kappa_n to permittivity eigenvalues eps_n.
        Stores:
        self.eps_eff_modes (3,) complex
        """
        if getattr(self, "kappa_modes", None) is None:
            raise RuntimeError("Dipole modes not computed. Call projectK_modes() first.")
        kappa = np.asarray(self.kappa_modes, float)
        self.eps_eff_modes = -self.eps_m * (1.0 + 2.0*kappa) / (1.0 - 2.0*kappa)
        return self.eps_eff_modes
    
    def mode_volumes(self):
        """
        Compute dipole-subspace effective mode volumes per mode (3 scalars):
        Vn = (V/4π) * |eps_n/eps_m - 1| * s_n
        where s_n is taken from dipole-subspace oscillator strength weights w_dip (sum=1).

        Stores:
        self.V_modes (3,) float
        """
        if getattr(self, "eps_eff_modes", None) is None:
            self.eps_modes()
        if getattr(self, "w_dip", None) is None:
            raise RuntimeError("Dipole modes not computed. Call projectK_modes() first.")

        s = np.asarray(self.w_dip, float)  # (3,), sum=1
        factor = (self.volume / (4.0*np.pi)) * np.abs(self.eps_eff_modes / self.eps_m - 1.0)

        """
        This is a scalar proxy for oscillator strength per dipole-subspace mode; tensorial V_eff is computed in compute_s_n()
        """
        self.V_modes = factor * s
        return self.V_modes

    # def _kappa_from_sigma(self):
    #     sigma = self.sigma.ravel().astype(float)
    #     num = sigma @ (self.K @ sigma)
    #     den = sigma @ sigma
    #     self.k_eff = num / den
    #     return self.k_eff

    # def _eps_from_kappa(self):
    #     kappa = np.asarray(self.k_eff, float)
    #     self.e_eff = -self.eps_m * (1.0 + 2.0*kappa) / (1.0 - 2.0*kappa)
    #     return self.e_eff


    def compute_polarizability_tensor(self, wavelength, eps_medium, eps_metal, use_mlwa=True):
        """
        3-mode dipole-subspace polarizability with optional MLWA.

        Diagonal in dipole-mode basis (R_dip):
        alpha0_n(λ) = V_n * (eps(λ)-eps_m(λ)) / (eps(λ)-eps_eff_n)

        MLWA per mode:
        alpha_n = alpha0_n / (1 - (k^2/a_n) alpha0_n - (2i/3) k^3 alpha0_n)

        Returns:
        alpha_lab (...,3,3)
        """
        wl = np.asarray(wavelength, float)           # (...,)
        eps = np.asarray(eps_metal, complex)         # (...,)
        eps_m = np.asarray(eps_medium, complex)      # (...,)

        # if self.K is None:
        #     self.build_K()
        if getattr(self, "kappa_modes", None) is None or getattr(self, "R_dip", None) is None:
            self.projectK_modes()
        if getattr(self, "eps_eff_modes", None) is None:
            self.eps_modes()
        if getattr(self, "V_modes", None) is None:
            self.mode_volumes()

        # wavevector in medium
        k = np.sqrt(eps_m) * 2.0 * np.pi / wl        # (...,)

        # quasistatic alpha0 per mode
        delta = eps - eps_m                           # (...,)
        alpha0 = np.zeros(delta.shape + (3,), dtype=complex)
        for n in range(3):
            base = (eps - self.eps_eff_modes[n])      # (...,)
            alpha0[..., n] = self.V_modes[n] * delta / base

        if use_mlwa:
            a = np.maximum(np.asarray(self.a_dip, float), 1e-18)   # (3,)
            dep = (k[..., None]**2) * alpha0 / a[None, :]          # (...,3)
            rad = (2.0j/3.0) * (k[..., None]**3) * alpha0          # (...,3)
            alpha = alpha0 / (1.0 - dep - rad)
        else:
            alpha = alpha0

        # assemble diagonal in dipole basis
        alpha_princ = np.zeros(alpha.shape[:-1] + (3,3), dtype=complex)
        alpha_princ[..., 0,0] = alpha[..., 0]
        alpha_princ[..., 1,1] = alpha[..., 1]
        alpha_princ[..., 2,2] = alpha[..., 2]

        # rotate back to lab
        R = self.R_dip.astype(complex)  # (3,3), columns are dipole directions
        alpha_lab = R @ alpha_princ @ R.T

        self.polarizability = alpha_lab
        return alpha_lab

    def compute_sigma_NP(self, mode="all", normalize=True,
                     near_factor=0.5, sign=-1.0,
                     symmetrize_T=True, enforce_bounds=True):
        """
        Compute dipole-subspace Neumann-Poincaré (K) surface charge mode(s)
        WITHOUT explicitly building the dense NxN K matrix.

        It projects the (principal-value) NP operator onto the dipole basis
        span{rx, ry, rz} and reconstructs the corresponding charge patterns:
            sigma_n(s) = B(s) @ c_n,   where B = rel_centers (N,3)

        Parameters
        ----------
        mode : str
            "dominant" -> returns the strongest/longitudinal dipolar mode (by semi-extent)
            "all"      -> returns all three dipole-subspace modes
        normalize : bool
            If True, normalize each sigma_n to unit area-weighted L2 norm: sum sigma^2 A = 1.  Default: True
        near_factor : float
            Regularization length scale multiplier (panel-size smoothing). Default: 0.5
        sign : float
            Sign convention for the kernel. Use sphere test to confirm. Default: -1.0
        symmetrize_T : bool
            Symmetrize the reduced 3x3 operator T to enforce discrete self-adjointness. Default: True
        enforce_bounds : bool
            Raise if kappa is far outside (-1/2, 1/2); clip tiny numerical excursions. Default: True

        Stores
        ------
        self.kappa_modes : (3,)
        self.C_modes     : (3,3)
        self.sigma_NP    : list[(N,)] or (N,)
        self.kappa_modes      : dominant kappa (if mode="dominant") else (3,)
        """

        if self.rel_centers is None or self.face_centers is None or self.face_normals is None:
            raise RuntimeError("Geometry not computed. Need face_centers, face_normals, rel_centers.")
        if self.face_areas is None:
            raise RuntimeError("Geometry not computed. Need face_areas.")

        # --- Dipole basis on faces (centered coordinates) ---
        B = np.asarray(self.rel_centers, dtype=np.float64)  # (N,3)
        W = np.asarray(self.face_areas,  dtype=np.float64)  # (N,)

        # --- Matrix-free application: K @ B ---
        r = np.asarray(self.face_centers, dtype=np.float64)  # (N,3)
        n = np.asarray(self.face_normals, dtype=np.float64)  # (N,3)
        Kb = apply_K_to_B_numba(r, n, W, B, near_factor=near_factor, sign=sign)  # (N,3)

        # --- Reduced matrices in area-weighted inner product <u,v> = Σ u v A ---
        G = (B.T * W) @ B          # (3,3)
        T = (B.T * W) @ Kb         # (3,3)

        # Symmetrize reduced operator to respect NP self-adjointness (discrete)
        if symmetrize_T:
            T = 0.5 * (T + T.T)

        # --- Solve generalized eigenproblem: T c = kappa G c ---
        try:
            from scipy.linalg import eigh
            kappa, C = eigh(T, G)  # ascending
        except Exception:
            # whitening fallback
            evals_G, evecs_G = np.linalg.eigh(G)
            if np.min(evals_G) <= 0:
                raise RuntimeError("G is not positive definite; check mesh/basis centering.")
            Gmhalf = (evecs_G * (1.0 / np.sqrt(evals_G))) @ evecs_G.T
            A = Gmhalf @ T @ Gmhalf
            kappa, U = np.linalg.eigh(A)
            C = Gmhalf @ U

        kappa = np.real(kappa)
        C = np.real(C)

        # Bounds sanity check for NP spectrum
        if enforce_bounds:
            if np.any(kappa > 0.5 + 1e-3) or np.any(kappa < -0.5 - 1e-3):
                raise RuntimeError(
                    f"Unphysical kappa detected (outside (-1/2,1/2)): {kappa}. "
                    "Check kernel sign/diagonal convention and near-field regularization."
                )
            kappa = np.clip(kappa, -0.5 + 1e-8, 0.5 - 1e-8)

        # --- Reconstruct sigma_n = B @ c_n ---
        sigmas = [B @ C[:, i] for i in range(3)]  # list of (N,)

        if normalize:
            for i in range(3):
                norm2 = np.sum(sigmas[i] * sigmas[i] * W)
                if norm2 > 0:
                    sigmas[i] /= np.sqrt(norm2)

        # --- Optional: sort modes by semi-extent along their dipole direction (transverse->longitudinal) ---
        # Compute dipole moments p_n ~ ∫ (r-rel) sigma dS ≈ Σ rel_centers * sigma * A
        p_modes = np.zeros((3, 3), dtype=np.float64)
        for i in range(3):
            p_modes[:, i] = np.sum(B * (sigmas[i][:, None] * W[:, None]), axis=0)

        # Unit dipole directions
        R_dip = np.zeros((3, 3), dtype=np.float64)
        for i in range(3):
            pn = p_modes[:, i]
            nn = np.linalg.norm(pn)
            R_dip[:, i] = pn / nn if nn > 1e-30 else np.eye(3)[:, i]

        # Semi-extent along each dipole direction, using vertex projections
        rel_v = np.asarray(self.vertices, dtype=np.float64) - np.asarray(self.centroid, dtype=np.float64)[None, :]
        proj = rel_v @ R_dip
        a = np.max(np.abs(proj), axis=0)
        order = np.argsort(a)  # small -> large (longitudinal last)

        kappa = kappa[order]
        C = C[:, order]
        sigmas = [sigmas[i] for i in order]

        # Store
        self.kappa_modes = kappa
        self.C_modes = C
        self.R_dip = R_dip[:, order]
        self.a_dip = a[order]

        if mode == "dominant":
            # by construction: longitudinal ~ largest semi-extent => last after sorting
            self.kappa_modes = float(kappa[-1])
            self.sigma_NP = sigmas[-1]
            return self.sigma_NP
        elif mode == "all":
            self.kappa_modes = kappa
            self.sigma_NP = sigmas
            return self.sigma_NP
        else:
            raise ValueError("mode must be 'dominant' or 'all'")

    
    def extinction(self, wavelength, eps_medium, eps_metal, E0=None, use_mlwa=True):
        """
        Extinction cross section for arbitrary polarization E0.
        Uses alpha_eff = e^† alpha e (proper complex quadratic form).
        """
        if E0 is None:
            E0 = self.E0 if self.E0 is not None else np.array([0,0,1.0], dtype=complex)

        e = np.asarray(E0, dtype=complex)
        e = e / (np.linalg.norm(e) + 1e-30)

        alpha = self.compute_polarizability_tensor(wavelength, eps_medium, eps_metal, use_mlwa=use_mlwa)
        alpha_eff = np.einsum('i,...ij,j->...', np.conj(e), alpha, e)

        wl = np.asarray(wavelength, float)
        eps_m = np.asarray(eps_medium, complex)
        C_ext = (8.0 * np.pi**2 / (np.sqrt(eps_m) * wl)) * np.imag(alpha_eff)

        # k = np.sqrt(eps_m) * 2.0 * np.pi / wl  # (...,) in 1/length
        # C_sca = (8.0 * np.pi / 3.0) * (np.abs(k)**4) * (np.abs(alpha_eff)**2) / (np.abs(eps_m)**2 + 1e-300)

        return C_ext.real
    
    def scattering(self, wavelength, eps_medium, eps_metal, E0=None, use_mlwa=True):
        """
        Scattering cross section C_sca(λ) for an arbitrary incident polarization E0.

        Uses the dipole formula in a homogeneous medium, written in a way that is
        consistent with this class's extinction() prefactor convention.

        Parameters
        ----------
        wavelength : float or array-like
            Wavelength(s) in same length unit as the mesh (e.g., nm).
        eps_medium : complex or array-like
            Permittivity of surrounding medium at wavelength(s).
        eps_metal : complex or array-like
            Permittivity of nanoparticle at wavelength(s).
        E0 : array-like (3,), optional
            Incident polarization vector. If None, uses self.E0 or z-polarized.
        use_mlwa : bool
            Whether to use MLWA-corrected polarizability.

        Returns
        -------
        C_sca : ndarray
            Scattering cross section in (length)^2 (e.g., nm^2).
        """
        if E0 is None:
            E0 = self.E0 if self.E0 is not None else np.array([0, 0, 1.0], dtype=complex)

        e = np.asarray(E0, dtype=complex)
        e = e / (np.linalg.norm(e) + 1e-30)

        alpha = self.compute_polarizability_tensor(wavelength, eps_medium, eps_metal, use_mlwa=use_mlwa)

        # polarization-resolved effective polarizability (scalar): alpha_eff = e^† α e
        alpha_eff = np.einsum('i,...ij,j->...', np.conj(e), alpha, e)

        wl = np.asarray(wavelength, float)
        eps_m = np.asarray(eps_medium, complex)

        # wave number in medium
        k = np.sqrt(eps_m) * 2.0 * np.pi / wl  # (...,) in 1/length

        # Dipole scattering (polarization-resolved):
        # We use a prefactor consistent with extinction() used in this class.
        # This choice makes C_abs = C_ext - C_sca numerically stable and physically sensible
        # when alpha includes radiative damping (e.g. MLWA).
        #
        # NOTE: Conventions vary across unit systems; the absolute prefactor may differ by a constant.
        # Relative spectra and peak positions are robust, which is the primary use here.
        C_sca = (8.0 * np.pi / 3.0) * (np.abs(k)**4) * (np.abs(alpha_eff)**2) / (np.abs(eps_m)**2 + 1e-300)

        return C_sca.real

    def absorption(self, wavelength, eps_medium, eps_metal, E0=None, use_mlwa=True):
        """
        Absorption cross section C_abs(λ) computed from energy conservation:
            C_abs = C_ext - C_sca
        """
        C_ext = self.extinction(wavelength, eps_medium, eps_metal, E0=E0, use_mlwa=use_mlwa)
        C_sca = self.scattering(wavelength, eps_medium, eps_metal, E0=E0, use_mlwa=use_mlwa)
        return C_ext - C_sca
    
@njit(cache=True, fastmath=True, parallel=True)
def apply_K_to_B_numba(r, n, A, B, near_factor=0.5, sign=-1.0):
    """
    Computes K@B without forming K.
    r: (N,3) face centers
    n: (N,3) face normals
    A: (N,) face areas
    B: (N,3) RHS vectors (dipole basis)
    returns Kb: (N,3)
    """
    N = r.shape[0]
    Kb = np.zeros((N, 3), dtype=np.float64)

    # panel-size smoothing length per source panel j
    h = np.sqrt(A / np.pi)  # (N,)

    for i in prange(N):
        ri0, ri1, ri2 = r[i, 0], r[i, 1], r[i, 2]
        s0 = 0.0; s1 = 0.0; s2 = 0.0

        for j in range(N):
            if j == i:
                continue

            dx = ri0 - r[j, 0]
            dy = ri1 - r[j, 1]
            dz = ri2 - r[j, 2]

            dist2 = dx*dx + dy*dy + dz*dz
            hj = near_factor * h[j]
            dist_reg2 = dist2 + hj*hj
            dist_reg = np.sqrt(dist_reg2)

            # n_j · (r_i - r_j)
            ndotr = n[j, 0]*dx + n[j, 1]*dy + n[j, 2]*dz

            # kernel * A_j
            # kernel = sign * ndotr / (4π dist^3)
            inv = 1.0 / (dist_reg2 * dist_reg)          # 1/dist^3
            kij = sign * ndotr * inv * (A[j] / (4.0*np.pi))

            # accumulate Kb[i,:] += kij * B[j,:]
            s0 += kij * B[j, 0]
            s1 += kij * B[j, 1]
            s2 += kij * B[j, 2]

        Kb[i, 0] = s0
        Kb[i, 1] = s1
        Kb[i, 2] = s2

    return Kb

def calc_integral_decay_profile_vectorized(face_centers, face_normals, sigma, 
                                          distances, eps_h=1.0):
    """
    Calculate E-field decay profile for conformal coating layers.
    
    Uses vectorized Coulomb integration to compute field at all offset points
    simultaneously. 50-100x faster than loop-based computation.
    
    CONFORMAL COATING: Points offset along surface normals at distance d.
    
    Parameters
    ----------
    face_centers : (M, 3) array
        Face center positions R_k [nm]
    face_normals : (M, 3) array
        Outward-pointing unit normals at each face
    sigma : (M,) array
        Surface charge density [C/m²] or per-face charges q_k
    distances : array-like
        Offset distances d (coating thicknesses) [nm]
    eps_h : float or complex
        Host permittivity (default 1.0 for vacuum)
    
    Returns
    -------
    results : dict
        'distances': input distances
        'E_avg': (N_d,) mean field magnitude at each distance
        'E_std': (N_d,) std dev of field magnitude
        'E_max': (N_d,) maximum field magnitude
        'E_min': (N_d,) minimum field magnitude
        'E_field': (N_d, M, 3) full field array at each distance/point
    """
    
    # Type conversions
    face_centers = np.asarray(face_centers, dtype=float)
    face_normals = np.asarray(face_normals, dtype=float)
    sigma = np.asarray(sigma, dtype=complex)
    distances = np.atleast_1d(distances)
    eps_h = complex(eps_h)
    
    N_d = len(distances)
    
    results = {
        'distances': distances,
        'E_avg': np.zeros(N_d),
        'E_std': np.zeros(N_d),
        'E_max': np.zeros(N_d),
        'E_min': np.zeros(N_d),
        'E_field': []
    }
    
    # ========== VECTORIZED COULOMB INTEGRAL ==========
    # Compute field for all offset points at all distances simultaneously
    
    # Expand dimensions for broadcasting
    # shape: (1, 1, M, 3)
    centers_exp = face_centers[np.newaxis, np.newaxis, :, :]
    sigma_exp = sigma[np.newaxis, np.newaxis, :]  # (1, 1, M)

    

    
    # Simplify: loop over distances is still cleaner for memory
    # But do all M source points at once per distance
    
    for i_d, d in enumerate(distances):
        # Observation points at this distance
        # shape: (M, 3)
        points = face_centers + d * face_normals
        
        # ===== Vectorized Coulomb field computation =====
        # Expand for broadcasting
        points_exp = points[:, np.newaxis, :]        # (M, 1, 3) observation
        centers_exp = face_centers[np.newaxis, :, :]  # (1, M, 3) sources
        sigma_exp = sigma[np.newaxis, :]              # (1, M)
        
        # Relative vectors: R = r_obs - R_source
        # shape: (M, M, 3)
        R = points_exp - centers_exp
        
        # Distance squared: r²
        # shape: (M, M)
        dist_sq = np.sum(R * R, axis=-1)
        
        # Avoid singularity (observation point exactly on charge)
        dist_sq = np.maximum(dist_sq, 1e-2)  # Small cutoff (nm scale)
        
        # Distance: r = sqrt(r²)
        dist = np.sqrt(dist_sq)
        
        # Coulomb field: E_k = (q_k / 4πε_h) × R / r³
        # Distance cubed: r³
        dist_cubed = dist_sq * dist
        
        # Weight: q_k / r³
        # shape: (M, M)
        weight = sigma_exp / dist_cubed
        
        # Weighted contributions: weight × R / r³
        # shape: (M, M, 3)
        E_contributions = weight[:, :, np.newaxis] * R
        
        # Sum over all source charges (axis=1)
        # shape: (M, 3)
        E_scat = np.sum(E_contributions, axis=1)
        
        # Apply prefactor: 1 / (4π ε_h)
        prefac = 1.0 / (4.0 * np.pi * eps_h)
        E_scat = prefac * E_scat
        
        # ===== Calculate statistics =====
        E_mag = np.linalg.norm(E_scat, axis=1)  # (M,)
        
        results['E_avg'][i_d] = np.mean(E_mag)
        results['E_std'][i_d] = np.std(E_mag)
        results['E_max'][i_d] = np.max(E_mag)
        results['E_min'][i_d] = np.min(E_mag)
        results['E_field'].append(E_scat)
    
    return results

@njit(cache=True, fastmath=True, parallel=True)
def efield_stats_conformal_numba(face_centers, face_normals, sigma, distances, eps_h=1.0, cutoff2=1e-2):
    """
    Returns:
      E_avg, E_std, E_max, E_min arrays of shape (Nd,)
    Notes:
      - sigma treated as real+imag separately only if needed; here assume real sigma for speed.
    """
    M = face_centers.shape[0]
    Nd = distances.shape[0]

    E_avg = np.zeros(Nd, dtype=np.float64)
    E_std = np.zeros(Nd, dtype=np.float64)
    E_max = np.zeros(Nd, dtype=np.float64)
    E_min = np.zeros(Nd, dtype=np.float64)

    prefac = 1.0 / (4.0 * np.pi * eps_h)

    for idd in range(Nd):
        d = distances[idd]

        # compute per-observation |E|
        Emag = np.zeros(M, dtype=np.float64)

        for i in prange(M):
            # observation point: r_i = c_i + d n_i
            ox = face_centers[i,0] + d*face_normals[i,0]
            oy = face_centers[i,1] + d*face_normals[i,1]
            oz = face_centers[i,2] + d*face_normals[i,2]

            ex = 0.0; ey = 0.0; ez = 0.0

            for j in range(M):
                dx = ox - face_centers[j,0]
                dy = oy - face_centers[j,1]
                dz = oz - face_centers[j,2]

                r2 = dx*dx + dy*dy + dz*dz
                if r2 < cutoff2:
                    r2 = cutoff2
                r = np.sqrt(r2)
                inv_r3 = 1.0 / (r2 * r)

                w = sigma[j] * inv_r3
                ex += w * dx
                ey += w * dy
                ez += w * dz

            ex *= prefac; ey *= prefac; ez *= prefac
            Emag[i] = np.sqrt(ex*ex + ey*ey + ez*ez)

        # stats
        s = 0.0
        s2 = 0.0
        mn = 1e300
        mx = -1e300
        for i in range(M):
            v = Emag[i]
            s += v
            s2 += v*v
            if v < mn: mn = v
            if v > mx: mx = v

        mean = s / M
        var = s2 / M - mean*mean
        if var < 0.0: var = 0.0

        E_avg[idd] = mean
        E_std[idd] = np.sqrt(var)
        E_min[idd] = mn
        E_max[idd] = mx

    return E_avg, E_std, E_max, E_min

def calc_integral_decay_profile(face_centers, face_normals, sigma, distances, eps_h=1.0):
    fc = np.asarray(face_centers, np.float64)
    fn = np.asarray(face_normals, np.float64)
    dist = np.asarray(distances, np.float64)


    sig = np.asarray(sigma.real, np.float64)

    E_avg, E_std, E_max, E_min = efield_stats_conformal_numba(fc, fn, sig, dist, eps_h=eps_h)
    return dict(distances=dist, E_avg=E_avg, E_std=E_std, E_max=E_max, E_min=E_min)

def I_powerlaw(a, b, r0, n):
    """
    ∫_a^b w(z) dz  with w(z) = r0^n / (z+r0)^n
    """
    a = float(a)
    if np.isinf(b):
        b_term = 0.0
    else:
        b = float(b)
        b_term = (b + r0)**(1.0 - n)

    if np.isclose(n, 1.0):
        if np.isinf(b):
            raise ValueError("For n=1 the integral to infinity diverges; check fitted n.")
        return r0 * (np.log(b + r0) - np.log(a + r0))

    return (r0**n) * (b_term - (a + r0)**(1.0 - n)) / (1.0 - n)


def n_eff_layered_powerlaw_normalized(r0, n, n_water, layers_nm):
    """
    n_eff = (∫ eta(z) w(z) dz) / (∫ w(z) dz)
    Guarantees n_eff is bounded between min and max indices.
    """
    z0 = 0.0
    num = 0.0

    # finite layers
    for t, n_layer in layers_nm:
        z1 = z0 + float(t)
        num += n_layer * I_powerlaw(z0, z1, r0, n)
        z0 = z1

    # semi-infinite outer medium (water)
    num += n_water * I_powerlaw(z0, np.inf, r0, n)

    den = I_powerlaw(0.0, np.inf, r0, n)
    return num / den

def model_power(r, A, r0, n):
    return A / (r+r0)**n


def compute_field_plane_from_sigma_vectorized(
    centers,
    sigma,
    areas,
    eps_h,
    plane='xz',
    plane_origin=(0.0, 0.0, 0.0),
    dims=(50.0, 50.0),
    steps=(1.0, 1.0),
    E_ext=None,
    # --- substrate (optional) ---
    eps_substrate=None,
    substrate_plane_point=(0.0, 0.0, 0.0),
    substrate_plane_normal=(0.0, 0.0, 1.0),
    near_eps=1e-2
):
    """
    Compute E-field on a plane from reconstructed NP surface charges.

    Parameters
    ----------
    centers : (M,3)
        Face centers (physical coordinates).
    sigma : (M,)
        Surface charge density on faces (complex).
    areas : (M,)
        Face areas.
    eps_h : complex
        Host permittivity (e.g. water).
    plane : {'xy','xz','yz'}
        Observation plane.
    plane_origin : (3,)
        Point through which the plane passes.
    dims : (Lu, Lv)
        Half-extent along plane axes.
    steps : (du, dv)
        Grid spacing.
    E_ext : (3,) or None
        External field to add.
    eps_substrate : complex or None
        Substrate permittivity (if present).
    substrate_plane_point, substrate_plane_normal :
        Define substrate plane for image charges.
    near_eps : float
        Softening length^2 to avoid singularities.

    Returns
    -------
    u, v : 1D arrays
    E_tot : (Nu, Nv, 3) complex
    """

    centers = np.asarray(centers, float)
    sigma = np.asarray(sigma, complex)
    areas = np.asarray(areas, float)
    eps_h = complex(eps_h)

    # physical charges
    charges = sigma * areas

    # substrate reflection coefficient
    use_sub = eps_substrate is not None
    if use_sub:
        eps_s = complex(eps_substrate)
        beta = (eps_h - eps_s) / (eps_h + eps_s)
        n_hat = np.asarray(substrate_plane_normal, float)
        n_hat /= np.linalg.norm(n_hat)

        def mirror_pts(P):
            d = np.sum((P - substrate_plane_point) * n_hat, axis=-1)
            return P - 2.0 * d[:, None] * n_hat

        centers_img = mirror_pts(centers)

    # grid
    if np.isscalar(dims):
        dims = (dims, dims)
    if np.isscalar(steps):
        steps = (steps, steps)

    u = np.arange(-dims[0], dims[0] + steps[0], steps[0])
    v = np.arange(-dims[1], dims[1] + steps[1], steps[1])

    U, V = np.meshgrid(u, v, indexing='ij')

    # Map to 3D Cartesian coordinates based on plane (all must be same shape)
    X0, Y0, Z0 = plane_origin
    if plane == 'xy':
        X = U + X0
        Y = V + Y0
        Z = np.full_like(U, Z0)
    elif plane == 'xz':
        X = U + X0
        Z = V + Z0
        Y = np.full_like(U, Y0)
    elif plane == 'yz':
        Y = U + Y0
        Z = V + Z0
        X = np.full_like(U, X0)
    else:
        raise ValueError("plane must be 'xy','xz','yz'")

    points = np.stack((X, Y, Z), axis=-1)  # (Nu, Nv, 3)


    # vectorized Coulomb sum
    R = points[:, :, None, :] - centers[None, None, :, :]   # (Nu, Nv, M, 3)
    r2 = np.sum(R * R, axis=-1) + near_eps                   # (Nu, Nv, M)
    r3 = r2 * np.sqrt(r2)                                    # (Nu, Nv, M)

    # weight should be (Nu, Nv, M, 1)
    weight = (charges[None, None, :] / r3)[..., None]        # (Nu, Nv, M, 1)
    E = np.sum(weight * R, axis=2)                           # (Nu, Nv, 3)


    if use_sub:
        Rimg = points[:, :, None, :] - centers_img[None, None, :, :]  # (Nu, Nv, M, 3)
        r2i = np.sum(Rimg * Rimg, axis=-1) + near_eps                 # (Nu, Nv, M)
        r3i = r2i * np.sqrt(r2i)                                      # (Nu, Nv, M)

        weight_i = (charges[None, None, :] / r3i)[..., None]          # (Nu, Nv, M, 1)
        E += beta * np.sum(weight_i * Rimg, axis=2)                   # (Nu, Nv, 3)


    E *= 1.0 / (4.0 * np.pi * eps_h)

    if E_ext is not None:
        E = E + np.asarray(E_ext, complex)[None, None, :]

    return u, v, E
