import numpy as np
import healpy as hp
from camb import model
import glass.shells
import glass.fields
import glass.observations
from glass import Cosmology
from multiprocessing import Pool
from functools import partial
import os
from scipy.stats import qmc  # For Latin Hypercube

class HIGenerator:
    def __init__(self, h=0.7, As=2e-9, Oc=0.25, Ob=0.05, 
                 nside=1024, z_min=0.4, z_max=0.45, nbins=1, sigmaz0=0.0001,
                 beam_deg=None, noise=True, noise_level=1.0, mask_file=None,
                 zebras=False, zebra_amplitude=0.1, zebra_width_deg=5.0, 
                 zebra_angle_deg=45.0, seed=1, n_jobs=4, batch_size=100):
        
        self.h = h
        self.As = As
        self.Oc = Oc
        self.Ob = Ob
        self.nside = nside
        self.z_min = z_min
        self.z_max = z_max
        self.nbins = nbins
        self.sigmaz0 = sigmaz0
        self.beam_deg = beam_deg
        self.noise = noise
        self.noise_level = noise_level
        self.mask_file = mask_file
        self.zebras = zebras
        self.zebra_amplitude = zebra_amplitude
        self.zebra_width_deg = zebra_width_deg
        self.zebra_angle_deg = zebra_angle_deg
        self.seed = seed  # Base seed (1 for LHS)
        self.n_jobs = n_jobs
        self.batch_size = batch_size
        
        self.rng = np.random.default_rng(seed)
        self.cosmo = self._setup_cosmology()
        self._preload_data()
    
    # ... _setup_cosmology, Tbar, b_HI unchanged ...
    
    def generate_single(self, custom_params=None):
        """SINGLE MAP at specific cosmology (your original mode)."""
        if custom_params:
            temp_params = self._copy_params()
            temp_params.update(custom_params)
            temp_gen = HIGenerator(**temp_params)
            return temp_gen._generate_single_map(0)
        return self._generate_single_map(0)
    
    def generate_lhs_suite(self, priors, n_samples=100, output_dir="lhs_maps", 
                          prefix="lhs_map", seed_base=1, log_seeds=True):
        """
        LHS SUITE: Vary priors across CPUs, seeds 1→N.
        
        priors = {
            'h': [0.65, 0.70],
            'As': [1.8e-9, 2.2e-9],
            'Oc': [0.24, 0.26]
        }
        """
        print(f"Generating {n_samples} LHS maps (seeds {seed_base}→{seed_base+n_samples-1})")
        
        # Generate Latin Hypercube
        sampler = qmc.LatinHypercube(d=len(priors))
        sample = sampler.random(n=n_samples)
        lhs_params = {}
        
        param_names = list(priors.keys())
        for i, name in enumerate(param_names):
            lhs_params[name] = (priors[name][0] + 
                              sample[:, i] * (priors[name][1] - priors[name][0]))
        
        # Save LHS hypercube
        np.savetxt(f"{output_dir}/{prefix}_hypercube.txt", 
                  np.column_stack([range(n_samples)] + 
                                 [lhs_params[name] for name in param_names]),
                  header="idx " + " ".join(param_names),
                  comments='')
        
        os.makedirs(output_dir, exist_ok=True)
        
        def single_lhs_map(args):
            idx, row = args
            params = self._copy_fixed_params()
            for name in param_names:
                params[name] = row[name]
            params['seed'] = seed_base + idx  # Seeds 1→N!
            gen = HIGenerator(**params)
            return gen._generate_single_map(0), row  # Returns map + params
        
        # Parallel generation
        with Pool(self.n_jobs) as pool:
            results = pool.map(single_lhs_map, 
                             [(i, dict(zip(param_names, lhs_params[name][i] 
                                         for name in param_names))) 
                              for i in range(n_samples)])
        
        # Save maps + log seeds (like your code)
        if log_seeds:
            self._log_seeds(n_samples, seed_base, output_dir)
        
        maps = [r[0] for r in results]
        for i, hi_map in enumerate(maps):
            np.save(f"{output_dir}/{prefix}_{i:06d}.npy", hi_map)
        
        print(f"Saved {n_samples} LHS maps + hypercube.txt to {output_dir}/")
        return maps, lhs_params
    
    def _copy_params(self):
        """Copy current parameters."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def _copy_fixed_params(self):
        """Copy non-varying parameters."""
        fixed = {k: v for k, v in self._copy_params().items() 
                if k not in ['h', 'As', 'Oc', 'Ob']}
        return fixed
    
    def _log_seeds(self, n_samples, seed_base, output_dir):
        """Log seeds like your usedseedsnew.txt."""
        import datetime
        with open(f"{output_dir}/used_seeds.txt", 'a') as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for i in range(n_samples):
                f.write(f"{seed_base+i} {timestamp} lhs_suite\n")
    

    def update_params(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.rng = np.random.default_rng(self.seed)
        self.cosmo = self._setup_cosmology()
        self._preload_data()
    
    def _setup_cosmology(self):
        pars = model.CAMBparams()
        pars.set_cosmology(H0=100*self.h, omch2=self.Oc*self.h**2, 
                          ombh2=self.Ob*self.h**2, tau=0.055, ns=0.965)
        pars.NonLinear = model.NonLinear.both
        return Cosmology.from_camb(pars)
    
    def _preload_data(self):
        """Precompute expensive static data."""
        self.z = np.linspace(0, self.z_max, 1000)
        self.zb = glass.shells.distance_grid(self.cosmo, self.z[0], self.z[-1], dx=50.)
        self.ws = glass.shells.linear_windows(self.zb)
        self.cls = glass.ext.camb.matter_cls(pars=None, lmax=3*self.nside-1, ws=self.ws)
        self.gls = glass.fields.lognormal_gls(self.cls)
        self.z_edges = glass.observations.equal_dens_z_bins(self.z, self.Tbar(self.z), nbins=self.nbins)
        self.tomo_THI = glass.observations.to_mon_z_gauss_err(self.z, self.Tbar(self.z), self.sigmaz0, self.z_edges)
    
    def Tbar(self, redshift):
        OHI = 4e-4 * (1 + redshift)**0.6
        return 189 * OHI * self.cosmo.h * (1 + redshift)**2 / self.cosmo.hf(redshift)
    
    def b_HI(self, redshift):
        return 0.6 + 0.3 * (1 + redshift)
    
    def _generate_single_map(self, seed_offset):
        """Single map generation (for multiprocessing)."""
        local_rng = np.random.default_rng(self.seed + seed_offset)
        matter = glass.fields.generate_lognormal(self.gls, self.nside, ncorr=5, rng=local_rng)
        
        HImap = np.stack([np.zeros(hp.nside2npix(self.nside)) for _ in range(self.nbins)], axis=0)
        for i, delta_i in enumerate(matter):
            for j in range(self.nbins):
                tomo_z_i, tomo_THI_i = glass.shells.restrict_z(self.tomo_THI[:,j], self.ws[i])
                HImap[j] += np.mean(tomo_THI_i) * self.b_HI(np.mean(tomo_z_i)) * delta_i
        
        fullskymap = HImap[0]
        
        if self.beam_deg:
            fullskymap = self._apply_beam(fullskymap)
        if self.mask_file:
            fullskymap = self._apply_mask(fullskymap)
        if self.zebras:
            fullskymap = self._add_zebras(fullskymap)
        if self.noise:
            fullskymap += self._add_noise(hp.nside2npix(self.nside), local_rng)
        
        return fullskymap
    
    def generate_map(self):
        """Generate single map."""
        return self._generate_single_map(0)
    
    def generate_batch(self, n_maps=100, output_dir="maps", prefix="hi_map"):
        """Generate batch of maps using all CPUs."""
        print(f"Generating {n_maps} maps on {self.n_jobs} CPUs...")
        
        os.makedirs(output_dir, exist_ok=True)
        gen_func = partial(self._generate_single_map)
        
        with Pool(self.n_jobs) as pool:
            maps = pool.map(gen_func, range(n_maps))
        
        # Save maps
        for i, hi_map in enumerate(maps):
            np.save(f"{output_dir}/{prefix}_{i:06d}.npy", hi_map)
        
        print(f"Saved {n_maps} maps to {output_dir}/")
        return maps
    
    def _apply_beam(self, map_data):
        fwhm_rad = np.radians(self.beam_deg)
        alm = hp.map2alm(map_data, lmax=2*self.nside-1)
        bl = hp.gauss_beam(fwhm=fwhm_rad, lmax=2*self.nside-1)
        alm *= bl
        return hp.alm2map(alm, self.nside)
    
    def _apply_mask(self, map_data):
        if self.mask_file.endswith('.npy'):
            mask = np.load(self.mask_file)
        else:
            mask = hp.read_map(self.mask_file, verbose=False)
        mask = np.logical_not(mask)
        return map_data * mask.astype(float)
    
    def _add_noise(self, npix, rng):
        return rng.normal(0.0, self.noise_level, size=npix)
    
    def _add_zebras(self, map_data):
        npix = len(map_data)
        theta, phi = hp.pix2ang(self.nside, np.arange(npix))
        x = np.sin(theta) * np.cos(phi)
        y = np.sin(theta) * np.sin(phi)
        angle_rad = np.radians(self.zebra_angle_deg)
        stripe_dir = x * np.cos(angle_rad) + y * np.sin(angle_rad)
        stripe_pattern = np.sin(2 * np.pi * stripe_dir / np.radians(self.zebra_width_deg))
        zebra_map = self.zebra_amplitude * stripe_pattern
        return map_data + zebra_map
