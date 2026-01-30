import numpy as np # type: ignore
from scipy.optimize import root_scalar # type: ignore
from scipy.integrate import simpson # type: ignore
import camb # type: ignore
from camb import model # type: ignore
import logging
from importlib import resources  
from pathlib import Path
from urllib import request
from appdirs import user_cache_dir
import skops.io as skio 

# Use relative imports to find the other modules in this package
from .cosmology import Cosmology
from .growth import GrowthCalculator

# Get a logger for this module
log = logging.getLogger(__name__)

class AletheiaEmu:
    """Emulator for the non-linear matter power spectrum.

    This class provides predictions for the non-linear matter power spectrum,
    P_NL(k), for a given cosmology and redshift. It is based on a set of
    Gaussian Process (GP) models trained on high-fidelity N-body simulations.

    The emulation method combines a de-wiggled linear power spectrum with a
    GP prediction for the non-linear boost factor, B(k), and a response
    function, dR/dxtide, that captures the effects of different growth of 
    structure histories.

    Attributes
    ----------
    gp_B : sklearn.gaussian_process.GaussianProcessRegressor
        The trained GP model for the non-linear boost factor.
    gp_dRdx : sklearn.gaussian_process.GaussianProcessRegressor
        The trained GP model for the response to xtilde.
    correction_function : scipy.interpolate.RectBivariateSpline
        A 2D spline object for correcting resolution effects in the prediction.
    planck_means : np.ndarray
        Mean values of [omega_b, omega_c, n_s] from Planck 2018.
    eigenvecs : np.ndarray
        Eigenvectors of the Planck 2018 covariance matrix.
    planck_sigmas : np.ndarray
        Standard deviations along each eigenvector direction.
    """
    # --- Define model URLs pointing to .skops files ---
    MODEL_URLS = {
        "gp_B": "https://gitlab.mpcdf.mpg.de/arielsan/aletheia/-/raw/main/src/aletheiacosmo/data/Aletheia_GP_B_skl1.7.skops?ref_type=heads&inline=false",
        "gp_dRdx": "https://gitlab.mpcdf.mpg.de/arielsan/aletheia/-/raw/main/src/aletheiacosmo/data/Aletheia_GP_dRdxt_skl1.7.skops?ref_type=heads&inline=false",
        "correction": "https://gitlab.mpcdf.mpg.de/arielsan/aletheia/-/raw/main/src/aletheiacosmo/data/resolution_correction_skl1.7.skops?ref_type=heads&inline=false"
    }
    # --- Define cache directory for downloaded models ---
    CACHE_DIR = Path(user_cache_dir("AletheiaCosmo", "AletheiaTeam"))
    # --- Define trusted types for skops loading ---
    TRUSTED_TYPES = ['numpy.ndarray',
                     'builtins.dict', 
                     'builtins.tuple', 
                     'builtins.list', 
                     'builtins.str', 
                     'numpy.float64', 
                     'numpy.random.mtrand.RandomState', 
                     'sklearn.gaussian_process.kernels.Matern', 
                     'sklearn.gaussian_process._gpr.GaussianProcessRegressor', 
                     'scipy.interpolate._fitpack2.RectBivariateSpline'
    ]                

    # --- Planck covariance matrix ---
    PLANCK_FILE = "planck_2018_lcdm_parcov.dat"
    
    def __init__(self):
        log.info("AletheiaEmu instance created. Checking for models...")
        # Ensure the cache directory exists
        # Use self.CACHE_DIR to access the class attribute
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # --- Define local file paths for LARGE models ---
        gp_b_path = self.CACHE_DIR / "Aletheia_GP_B_skl1.7.skops"
        gp_drdx_path = self.CACHE_DIR / "Aletheia_GP_dRdxt_skl1.7.skops"
        correction_path = self.CACHE_DIR / "resolution_correction_skl1.7.skops"

        # --- Download LARGE models if they are missing ---
        self._download_if_missing(self.MODEL_URLS["gp_B"], gp_b_path)
        self._download_if_missing(self.MODEL_URLS["gp_dRdx"], gp_drdx_path)
        self._download_if_missing(self.MODEL_URLS["correction"], correction_path)

        # --- Use skio.load to load emulator files and resolution correction ---
        self.gp_B = skio.load(gp_b_path, trusted=self.TRUSTED_TYPES)
        self.gp_dRdx = skio.load(gp_drdx_path, trusted=self.TRUSTED_TYPES)
        self.correction_function = skio.load(correction_path, trusted=self.TRUSTED_TYPES)

        # --- Load the bundled Planck data file ---
        try:
            # This uses importlib.resources to find the file *inside* the package
            with resources.files('aletheiacosmo.data').joinpath(self.PLANCK_FILE).open('rb') as f:
                covmat = np.loadtxt(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                "Planck covariance matrix file (planck_2018_lcdm_parcov.dat) was not found. "
                "This file should be bundled with the package. Please reinstall AletheiaCosmo."
            )
    
        # --- Construct Planck 2018 required data for parameter validation ---
        self.planck_means = np.array([0.02236164, 0.12071002, 0.96479956])
        eigenvals, eigenvecs = np.linalg.eigh(covmat)
        self.eigenvecs = eigenvecs
        self.planck_sigmas = np.sqrt(eigenvals)
        log.info("Emulator models and data loaded successfully.")

    def _download_if_missing(self, url, filepath):
        """Helper function to download an emulator skop file if it doesn't exist locally."""
        if not filepath.exists():
            log.warning(f"Data file not found. Downloading {filepath.name} to cache: {filepath}")
            try:
                opener = request.build_opener()
                opener.addheaders = [('User-agent', 'AletheiaCosmo-Downloader')]
                request.install_opener(opener)
                
                request.urlretrieve(url, filepath)
                log.info("Download complete.")
            except Exception as e:
                log.error(f"Failed to download model from {url}. Error: {e}")
                raise RuntimeError(f"Could not download model data. Please check your internet connection or the model URL.")

    def get_pnl(self, kvec, cospar, z):
        """Calculates the non-linear matter power spectrum.

        This is the main method of the emulator. It takes a set of wavenumbers,
        a cosmology, and a redshift, and returns the emulated P_NL(k).

        Parameters
        ----------
        kvec : array_like
            Array of wavenumbers, k, in units of **1/Mpc**.
            Must be within the emulator's valid range [0.006, 2.0] 1/Mpc.
        cospar : dict
            A dictionary of cosmological parameters such as the one created 
            by `create_cosmo_dict`.
        z : float
            The redshift at which to calculate the power spectrum.

        Returns
        -------
        np.ndarray
            The non-linear matter power spectrum, P_NL(k), in units of **Mpc^3**.
            
        Raises
        ------
        ValueError
            If any k-values in `kvec` are outside the emulator's valid
            training range [0.006, 2.0] 1/Mpc.
        ValueError
            If the input cosmology fails the validation checks (e.g., sigma12
            is out of range [0.2, 1.0] or shape parameters are out of
            the 5-sigma Planck box).
            
        Notes
        -----
        The calculation involves several steps:
        1.  Input parameters are validated (k-range, sigma12, shape).
        2.  A `Cosmology` object is created to compute linear spectra.
        3.  The non-linear boost `B(k)` and response `dR/dxi` are predicted by GPs.
        4.  The parameter `xtilde` is computed for the target and a reference cosmology.
        5.  All components are combined and a final resolution correction is applied.
        6.  A warning is logged if the resolution correction is > 1% at any scale.
        """
        log.info(f"Received request for P_nl at z={z:.2f}")
        kvec = np.atleast_1d(kvec)
        z = float(z)

        # --- k-vector validation (units are 1/Mpc) ---
        if np.any(kvec < 0.006) or np.any(kvec > 2.0):
            msg = (f"k-values are outside the valid emulator range [0.006, 2.0] 1/Mpc. "
                   f"Found min={np.min(kvec):.4f}, max={np.max(kvec):.4f}")
            log.error(msg)
            raise ValueError(msg)
        
        log.info("Initializing cosmology engine for target cosmology.")
        cosmology_engine = Cosmology(cospar)
        
        sigma12 = cosmology_engine.get_sigma12(z)
        self._validate_params(cospar, sigma12)

        # --- Correction factor for resolution effects ---
        correction = self.correction_function(kvec, sigma12).flatten()
        correction_factors = 1.0 / correction
        max_correction = np.max(correction_factors)
        
        if max_correction > 1.03:
            k_at_max_corr = kvec[np.argmax(correction_factors)]
            log.warning(f"Resolution correction is > 3% (max: {max_correction:.3f}x "
                        f"at k={k_at_max_corr:.2f} 1/Mpc). ")

        cosmology_engine.compute_all_spectra(sigma12)
        pdw_use = cosmology_engine.get_pdw(kvec)
        
        log.info("Computing emulator predictions from GPs.")
        x_combined = self._build_gp_input(kvec, cospar, sigma12)
        y_pred_B = self.gp_B.predict(x_combined)
        y_pred_dRdx = self.gp_dRdx.predict(x_combined)
        B = np.exp(y_pred_B)
        dRdx = y_pred_dRdx
    
        log.info("Computing xtilde for target and reference cosmologies.")
        xtilde = self._get_xtilde(z, cosmology_engine.growth)

        cospar_ref = cospar.copy()
        cospar_ref.update({'w_0':-1.0, 'w_a':0.0, 'A_s':2.101e-9, 'h':0.673})
        growth_ref = GrowthCalculator(cospar_ref)
        
        z0 = self._get_redshift(
            sigma12,            # The value to match
            growth_ref,         # The reference growth engine
            cosmology_engine,   # The target cosmology engine
            cospar_ref          # The reference parameter dict
        )
        
        xtilde_0 = self._get_xtilde(z0, growth_ref)
        log.debug(f"Target xtilde={xtilde:.4f}. Reference z0={z0:.4f}, xtilde_0={xtilde_0:.4f}")

        log.info("Combining components for final prediction.")
        dxtilde = xtilde - xtilde_0
        Pnl_uncorrected = pdw_use * B * (1. + dRdx * dxtilde)
        
        # Apply final resolution correction
        Pnl_final = Pnl_uncorrected * correction_factors

        log.info("P_nl calculation complete.")
        return Pnl_final
    
    def _build_gp_input(self, kvec, cospar, sigma12):
        """Constructs the 2D input array for the Gaussian Process models."""
        lkvec = np.log(kvec)
        # Reshape all inputs to be (N, 1) column vectors
        x1 = lkvec.reshape(-1, 1)
        x2 = np.full_like(x1, cospar['omega_b'])
        x3 = np.full_like(x1, cospar['omega_c'])
        x4 = np.full_like(x1, cospar['n_s'])
        x5 = np.full_like(x1, sigma12)
        return np.concatenate((x1, x2, x3, x4, x5), axis=1)

    def _validate_params(self, cospar, sigma12):
        """
        Checks if the input cosmology is within the valid range of the emulator.

        This function performs two checks:
        1.  It verifies if sigma12 falls within the emulator's trained range 
            of [0.2, 1.0].
        2.  It transforms the shape parameters (omega_b, omega_c, n_s) into the
            eigenvector basis of the Planck 2018 covariance matrix and checks
            that each projected component is within a +/- 5-sigma box.

        Args:
            cospar (dict): The input cosmology dictionary.
            sigma12 (array_like): The input value of sigma12 (as a 1-element array).

        Raises:
            ValueError: If any parameter falls outside the valid range.
        """
        log.info("Validating input parameters...")
        
        # Extract the scalar value for the check and logging
        sigma12_val = sigma12[0]
        
        # --- Validate sigma12 ---
        log.debug(f"Checking sigma12 = {sigma12_val:.4f}")
        if not (0.2 <= sigma12_val <= 1.0):
            raise ValueError(
                f"Validation failed: Calculated sigma12 ({sigma12_val:.4f}) is outside "
                f"the valid emulator range of [0.2, 1.0]."
            )
        # --- Use the scalar value for logging ---
        log.info(f"    sigma12 = {sigma12_val:.4f} (OK)")

        # --- Validate shape parameters in Planck eigenbasis ---
        log.debug("Checking shape parameters against Planck prior box...")
        input_params = np.array([cospar['omega_b'], cospar['omega_c'], cospar['n_s']])
        
        centered_params = input_params - self.planck_means
        projected_params = self.eigenvecs.T @ centered_params
        deviations = np.abs(projected_params) / self.planck_sigmas
        log.debug(f"Parameter deviations (in sigmas): {deviations}")

        if np.any(deviations > 5.0):
            failed_axis = np.argmax(deviations)
            msg = (
                f"Validation failed: Shape parameters are outside the 5-sigma Planck prior box.\n"
                f"  - Problem is in eigenvector direction {failed_axis}.\n"
                f"  - Deviation is {deviations[failed_axis]:.2f} sigma (limit is 5.0 sigma)."
            )
            log.error(msg)
            raise ValueError(msg)
        
        log.info("Shape parameters are within 5-sigma box (OK)")

    def _get_xtilde(self, z, growth_obj):
        """Calculates the smoothed growth-dependent parameter xtilde."""
        # ... (This logic is unchanged) ...
        eta = np.log(growth_obj.Dgrowth(z))
        eta_vec = np.linspace(eta-0.5, eta, 300)
        x_vec = growth_obj.X_tau(eta_vec)
        xtilde = simpson(AletheiaEmu.gaussian_kernel(eta, eta_vec, 0.12)*x_vec, eta_vec)
        return xtilde
        
    def _get_redshift(self, target_sigma12, growth_ref, cosmo_engine_target, cospar_ref):
        """Finds the redshift z0 in a reference cosmology with the same sigma12.

        This is an internal root-finding method. It finds the redshift `z0`
        at which a standard reference LCDM cosmology has a sigma_12 value
        equal to the `target_sigma12` of the user's input cosmology.

        Parameters
        ----------
        target_sigma12 : float
            The sigma_12 value of the target cosmology that we want to match.
        growth_ref : GrowthCalculator
            An initialized GrowthCalculator instance for the reference LCDM cosmology.
        cosmo_engine_target : Cosmology
            The initialized Cosmology instance for the target cosmology.
        cospar_ref : dict
            The cosmology dictionary for the reference LCDM cosmology.

        Returns
        -------
        float
            The redshift, z0, in the reference cosmology.
        """
        # Get D(z=0) for the reference cosmology
        D_ref_0 = growth_ref.Dgrowth(0.)
        
        # Calculate the expected sigma12 at z=0 for the reference cosmology.
        # This is done by taking the sigma12(z=0) from the target cosmology's CAMB run
        # and rescaling it by the ratio of sqrt(A_s) values.
        # The ratio of D(0) values is a small correction for different normalizations.
        sigma12_ref_0 = (cosmo_engine_target.sigma12_0 *
                         np.sqrt(cospar_ref['A_s'] / cosmo_engine_target.parameters.InitPower.As) *
                         (D_ref_0 / cosmo_engine_target.D0))
        
        # This nested function describes the evolution of sigma12 in the reference model
        def sig12_in_ref_cosmology(z):
            return sigma12_ref_0 * growth_ref.Dgrowth(z) / D_ref_0

        # The function whose root we want to find: f(z) = sigma12_ref(z) - target = 0
        def delta_sigma12(z):
            return sig12_in_ref_cosmology(z) - target_sigma12
        
        # Use a robust root-finding algorithm to find z0
        try:
            result = root_scalar(delta_sigma12, bracket=[-0.9, 4.4], method='brentq')
            if not result.converged:
                raise RuntimeError("Root-finding for z0 did not converge.")
            return result.root
        except ValueError as e:
            # This can happen if delta_sigma12 has the same sign at both ends of the bracket
            raise ValueError(f"Could not find a valid z0 for target sigma12={target_sigma12}. "
                             f"The value may be outside the solvable range. Original error: {e}")

    @staticmethod
    def gaussian_kernel(tau, tau_prime, tau_s):
        """Computes a normalized Gaussian kernel."""
        return np.exp(-((tau - tau_prime) ** 2) / (2 * tau_s ** 2)) *2./ (np.sqrt(2 * np.pi) * tau_s)

    @staticmethod
    def create_cosmo_dict(h, omega_b=None, omega_c=None, omega_k=0., Omega_b=None, Omega_c=None, 
                          Omega_k=0., A_s=2.1e-9, n_s=0.96, w_0=-1.0, w_a=0.0, 
                          model='LCDM', density_type='physical'):
        """
        Creates a standardized cosmology dictionary for the Aletheia Emulator.

        Args:
            h (float): The Hubble parameter. Required for all conversions.
            omega_b, omega_c, omega_k (float, optional): Physical baryon/CDM densities.
            Omega_b, Omega_c, Omega_nu (float, optional): Fractional baryon/CDM densities.
            ... (other parameters with defaults)
            model (str, optional): Cosmological model, e.g., 'LCDM' or 'w0waCDM'.
            density_type (str, optional): 'physical' (little omega) or 'fractional' (big Omega).

        Returns:
            dict: A validated dictionary ready for the emulator.
        """
        cospar = {}
        # --- Handle density parameter conversion ---
        if density_type == 'physical':
            if omega_b is None or omega_c is None:
                raise ValueError("For 'physical' density_type, 'omega_b', 'omega_c', and 'omega_k' must be provided.")
            cospar['omega_b'] = omega_b
            cospar['omega_c'] = omega_c
            cospar['omega_k'] = omega_k
            cospar['omega_nu'] = 0. # The current version assumes massless neutrinos
        elif density_type == 'fractional':
            if Omega_b is None or Omega_c is None:
                raise ValueError("For 'fractional' density_type, 'Omega_b', 'Omega_c', and 'Omega_k' must be provided.")
            cospar['omega_b'] = Omega_b * h**2
            cospar['omega_c'] = Omega_c * h**2
            cospar['omega_k'] = Omega_k * h**2
            cospar['omega_nu'] = 0. # The current version assumes massless neutrinos
        else:
            raise ValueError(f"Unknown density_type: '{density_type}'")

        # --- Compute derived parameters ---
        cospar['omega_de'] = h**2 - cospar['omega_c'] - cospar['omega_b'] - cospar['omega_k'] - cospar['omega_nu']

        # --- Set remaining parameters ---
        cospar['h'] = h
        cospar['A_s'] = A_s
        cospar['n_s'] = n_s
        
        # --- Handle model-specific defaults ---
        if model.upper() == 'LCDM':
            cospar['w_0'] = -1.0
            cospar['w_a'] = 0.0
        elif model.upper() == 'W0WACDM':
            cospar['w_0'] = w_0
            cospar['w_a'] = w_a
        else:
            raise ValueError(f"Unknown model: '{model}'")
                    
        return cospar

        

