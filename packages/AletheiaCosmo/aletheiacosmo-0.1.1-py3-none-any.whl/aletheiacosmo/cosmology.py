# Modules and libraries
import logging
import os
import numpy as np
from scipy.fftpack import dst, idst
from scipy.interpolate import splrep, splev
from scipy import integrate
import camb
from camb import model
from .growth import GrowthCalculator

# Get a logger specific to this module
log = logging.getLogger(__name__)

# Log the information instead of printing it
log.info('Cosmology: Using CAMB %s installed at %s', camb.__version__, os.path.dirname(camb.__file__))

class Cosmology:
    """Manages the computation of linear, no-wiggle, and de-wiggled power spectra.

    This class serves as a wrapper around CAMB to compute a baseline linear
    power spectrum at z=0. It uses the `GrowthCalculator` class to scale these
    spectra to different redshifts. It also contains methods to derive the
    smooth 'no-wiggle' and BAO-damped 'de-wiggled' power spectra, which are
    essential inputs for the emulator.

    The typical workflow is to initialize the class, then call the main
    `compute_all_spectra` method, which handles the internal chain of calculations.

    Parameters
    ----------
    cospar : dict
        A dictionary of cosmological parameters. Expected keys are:
        'h', 'omega_b', 'omega_c', 'n_s', 'A_s', 'w_0', 'w_a', 'omega_k'.

    Attributes
    ----------
    growth : GrowthCalculator
        An instance of the GrowthCalculator for this cosmology.
    plin_spline : tuple
        A spline representation (t, c, k) of the linear power spectrum.
    pnw_spline : tuple
        A spline representation of the no-wiggle power spectrum.
    pdw_spline : tuple
        A spline representation of the de-wiggled power spectrum.
    """
    def __init__(self, cospar, KMIN=1.e-4, KMAX=4., NPOINTS=700):
        log.info("Cosmology object created. Initializing CAMB.")
        pars = camb.CAMBparams()     
        pars.set_cosmology(H0=100*cospar['h'], ombh2=cospar['omega_b'], omch2=cospar['omega_c'], mnu=0.0, omk=0.0)
        pars.set_dark_energy(w=cospar['w_0'], wa=cospar['w_a'], dark_energy_model='ppf')
        pars.InitPower.set_params(ns=cospar['n_s'], As=cospar['A_s'])
        pars.NonLinear = model.NonLinear_none
        pars.set_matter_power(redshifts=[0.], kmax=4.)    
        self.parameters = pars
        self.results = camb.get_results(self.parameters)
        #compute sigma12 at z=0
        self.sigma12_0 = self.results.get_sigmaR(12.0, hubble_units=False)

        # Get the sound horizon at recombination
        self.rdrag = self.results.get_derived_params()['rdrag']
        
        log.info("Initializing GrowthCalculator.")
        self.growth = GrowthCalculator(cospar)
        self.D0 = self.growth.Dgrowth(0.)
        
        # Initialize attributes
        self.klin, self.plin, self.pnw, self.pdw = None, None, None, None
        self.plin_spline, self.pnw_spline, self.pdw_spline = None, None, None
        
        # Configuration for k-range
        self.kmin, self.kmax, self.npoints = KMIN, KMAX, NPOINTS

    def compute_all_spectra(self, target_sigma12_z0):
        """A method to run the full calculation pipeline.

        This function calls the internal methods in the correct order to generate
        the linear, no-wiggle, and de-wiggled power spectra.

        Parameters
        ----------
        target_sigma12_z0 : float
            The target amplitude for the z=0 linear power spectrum, specified
            by the value of sigma_12.
        """
        log.info(f"Generating all linear spectra for target sigma12(z=0)={target_sigma12_z0[0]:.3f}")
        self._compute_linear_pk_CAMB(target_sigma12_z0)
        self._compute_nonwiggle_pk()
        self._compute_dewiggled_pk()
        log.debug("All linear spectra computed and splines created.")

    def get_sigma12(self, z):
        """Scales the value of sigma_12(z=0) to a given redshift using the growth factor.

        Parameters
        ----------
        z : float
            The target redshift.

        Returns
        -------
        float
            The value of sigma_12 at redshift z.
        """
        sigma12 = self.sigma12_0 * self.growth.Dgrowth(z)/self.D0
        return sigma12
    
    def _compute_linear_pk_CAMB(self, sigma12):
        """Generates the z=0 linear P(k) from CAMB and rescales its amplitude.

        This internal method fetches the power spectrum shape from CAMB and then
        normalizes it to match the provided `target_sigma12_z0`.

        Parameters
        ----------
        target_sigma12_z0 : float
            The target sigma_12 value at z=0.
        """
        kh, _, pk = self.results.get_matter_power_spectrum(
            minkh=self.kmin, maxkh= self.kmax, npoints = self.npoints
        ) # Linear Matter Power Spectrum
        # Scale pk to match the desired sigma_12 at z=0
        # Note: pk is in units of (Mpc/h)^3, so we convert accordingly
        ratio_s12 = (sigma12 / self.sigma12_0)**2
        self.klin = kh.copy()*self.parameters.H0/100.
        self.plin = pk[0,:].copy()/(self.parameters.H0/100.)**3*ratio_s12
        # Build spline of linear power spectrum
        self.plin_spline = splrep(np.log(self.klin), np.log(self.plin))
        
    def _compute_nonwiggle_pk(self,NDST = 2**16,FMIN=150, FMAX=310, WMIN_LOW=180, WMIN_HIGH=210,
        WMAX=270, KRD_MIN=0.00673, KRD_MAX = 673.):
        """Computes a smooth 'no-wiggle' version of the linear power spectrum.

        This method uses a filtering technique in Fourier space (via a Discrete
        Sine Transform) to remove the Baryon Acoustic Oscillation (BAO) wiggles
        from the linear power spectrum.

        Notes
        -----
        This method requires `_generate_linear_pk` to be called first.
        The algorithm contains several parameter settings that define the
        filtering windows and frequencies, based on established prescriptions.
        """
        # Set up a grid of k * r_drag for the filtering
        delta_krd = (KRD_MAX - KRD_MIN) / (NDST - 1)
        kr = np.arange(KRD_MIN, KRD_MAX, delta_krd)

        # Evaluate P(k) on this grid
        pk_interp = self.get_plin(kr / self.rdrag)
        xvec = np.log(kr * pk_interp)  
        
        # Discrete Sine Transform
        xvec_dst = dst(xvec, type=1)

        # Identify wiggle frequencies and filter them out
        frec = np.arange(FMIN, FMAX, 2)
        even = xvec_dst[FMIN+1:FMAX+1:2]        
        
        weights = np.array([-1, 16, -30, 16, -1]) / 12.0 # Weights for 2nd derivative
        min_deriv, imin_deriv = 1000.0, WMIN_LOW
        for j in range(2, len(frec) - 2):
            if WMIN_LOW <= frec[j] <= WMIN_HIGH:
                deriv = np.dot(even[j-2:j+3], weights)
                if deriv < min_deriv:
                    min_deriv, imin_deriv = deriv, frec[j]

        wmin_use = imin_deriv - 22
        w1_idx = (wmin_use - FMIN) // 2
        w2_idx = (WMAX - FMIN) // 2

        frec_cut = np.concatenate((frec[:w1_idx], frec[w2_idx:]))
        odd_cut = np.concatenate((xvec_dst[FMIN:FMAX:2][:w1_idx], xvec_dst[FMIN:FMAX:2][w2_idx:]))
        even_cut = np.concatenate((even[:w1_idx], even[w2_idx:]))
        
        tck_odd = splrep(frec_cut, odd_cut)
        tck_even = splrep(frec_cut, even_cut)
        
        # Replace the wiggle region with the smoothed spline
        for j in range(len(frec)):
            if wmin_use < frec[j] <= WMAX:
                xvec_dst[FMIN + 2*j] = splev(frec[j], tck_odd)
                xvec_dst[FMIN + 2*j + 1] = splev(frec[j], tck_even)

        # Inverse Discrete Sine Transform
        xvec_filtered = idst(xvec_dst, type=1) / (2 * (len(xvec_dst) - 1))
        pnw_hires = np.exp(xvec_filtered) / kr
        k_hires = kr / self.rdrag

        # Interpolate the final no-wiggle spectrum back to the original k-grid
        pnw_spline_tmp = splrep(np.log(k_hires), np.log(pnw_hires))
        self.pnw = np.exp(splev(np.log(self.klin), pnw_spline_tmp))
        self.pnw_spline = splrep(np.log(self.klin), np.log(self.pnw))

    def _compute_dewiggled_pk(self):
        """Computes the de-wiggled power spectrum by damping the BAO features.

        This combines the linear and no-wiggle spectra using a Gaussian
        damping factor, which depends on the velocity dispersion sigma_v.

        Notes
        -----
        This method requires both the linear and no-wiggle spectra to have
        been computed first.
        """
        if self.plin is None or self.pnw is None:
            raise RuntimeError("Both P_lin and P_nw must be computed before de-wiggling.")
        # Calculate the 1D velocity dispersion sigma_v
        sigma_v2_integrand = self.plin / (6. * np.pi**2)
        sigma_v2 = integrate.simpson(sigma_v2_integrand, self.klin, axis=-1)
        sigma_v = np.sqrt(sigma_v2)

        # Compute the de-wiggled power spectrum
        damping_factor = np.exp(-(self.klin*sigma_v)**2)
        self.pdw = self.plin * damping_factor + self.pnw * (1. - damping_factor)
        self.pdw_spline = splrep(np.log(self.klin), np.log(self.pdw))
    
    def get_plin(self, k):
        """Interpolates the linear power spectrum P_lin(k) to any given k.

        Parameters
        ----------
        k : float or ndarray
            Wavenumber(s) in units of 1/Mpc.

        Returns
        -------
        float or ndarray
            The interpolated linear power spectrum in units of Mpc^3.
        """
        if self.plin_spline is None:
            raise RuntimeError("Linear P(k) has not been computed. Call 'compute_all_spectra' first.")
        return np.exp(splev(np.log(k), self.plin_spline))
        
    def get_pnw(self, k):
        """Interpolates the no-wiggle power spectrum P_nw(k) to any given k.

        Parameters
        ----------
        k : float or ndarray
            Wavenumber(s) in units of 1/Mpc.

        Returns
        -------
        float or ndarray
            The interpolated no-wiggle power spectrum in units of Mpc^3.
        """
        if self.pnw_spline is None:
            raise RuntimeError("No-wiggle P(k) has not been computed. Call 'compute_all_spectra' first.")
        return np.exp(splev(np.log(k), self.pnw_spline))

    def get_pdw(self, k):
        """Interpolates the de-wiggled power spectrum P_dw(k) to any given k.

        Parameters
        ----------
        k : float or ndarray
            Wavenumber(s) in units of 1/Mpc.

        Returns
        -------
        float or ndarray
            The interpolated de-wiggled power spectrum in units of Mpc^3.
        """
        if self.pdw_spline is None:
            raise RuntimeError("De-wiggled P(k) has not been computed. Call 'compute_all_spectra' first.")
        return np.exp(splev(np.log(k), self.pdw_spline))
