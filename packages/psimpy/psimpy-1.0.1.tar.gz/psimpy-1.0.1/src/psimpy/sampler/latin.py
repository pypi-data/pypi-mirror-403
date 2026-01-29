import numpy as np
from scipy.spatial.distance import pdist
from typing import Union
from beartype import beartype
from psimpy.utility import check_bounds, scale_samples

class LHS:
    
    @beartype
    def __init__(
        self, ndim: int, bounds: Union[np.ndarray, None] = None,
        seed: Union[int, None] = None, criterion: str = 'random', 
        iteration: Union[int, None] = None) -> None:
        """Latin hypercube sampling.
    
        Parameters
        ----------
        ndim : int
            Dimension of parameters.
        bounds : numpy array
            Upper and lower boundaries of each parameter. Shape :code:`(ndim, 2)`.
            `bounds[:, 0]` corresponds to lower boundaries of each parameter and
            `bounds[:, 1]` to upper boundaries of each parameter.
        seed : int, optional
            Seed to initialize the pseudo-random number generator.
        criterion : str, optional
            Criterion for generating Latin hypercube samples.
            `'random'` - randomly locate samples in each bin.
            `'center'` - locate samples in bin centers.
            `'maximin'` - locate samples in each bin by maximizing their minimum
            distance.
            Default is `'random'`.
        iteration : int, optional
            Number of iterations if :code:`criterion='maximin'`.
        """
        self.ndim = ndim

        if bounds is not None:
            check_bounds(ndim, bounds)
        self.bounds = bounds
        
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        
        if criterion not in ('random', 'center', 'maximin'):
            raise NotImplementedError(
                f"criterion {criterion} is not implemented."
                f" Supported criterion includes: 'random', 'center', 'maximin'")
        self.criterion = criterion
        self.iteration = iteration
        
    
    def sample(self, nsamples: int) -> np.ndarray:
        """Draw Latin hypercube samples.
        
        Parameters
        ----------
        nsamples : int
            Number of samples to be drawn.
        
        Returns
        -------
        lhs_samples : numpy array
            Latin hypercube samples. Shape :code:`(nsamples, ndim)`.  
        """        
        self.nsamples = nsamples
        
        # create nsamples bins in the interval [0, 1]
        bin_edges = np.linspace(0, 1, nsamples+1)
        self._lower_edges = bin_edges[:nsamples]
        self._upper_edges = bin_edges[1 : nsamples+1]      
        
        if self.criterion == 'random':
            lhs_samples = self._random()
        elif self.criterion == 'center':
            lhs_samples = self._center()
        elif self.criterion == 'maximin':
            lhs_samples = self._maximin()     
        
        if self.bounds is not None:
            lhs_samples = scale_samples(lhs_samples, self.bounds)
        
        return lhs_samples
    
    def _random(self) -> np.ndarray:
        """"Draw samples by randomly picking points in each bin."""
        samples = self.rng.uniform(size=(self.nsamples, self.ndim))
        lhs_samples = np.zeros_like(samples)
        for j in range(self.ndim):
            samples[:,j] = samples[:,j]*(self._upper_edges-self._lower_edges) \
                + self._lower_edges
            lhs_samples[:,j] = self.rng.permutation(samples[:,j])
        return lhs_samples
    
    def _center(self) -> np.ndarray:
        """"Draw samples by picking points at the center of each bin."""
        self._center_points = (self._lower_edges + self._upper_edges) / 2
        lhs_samples = np.zeros((self.nsamples, self.ndim))
        for j in range(self.ndim):
            lhs_samples[:,j] = self.rng.permutation(self._center_points) 
        return lhs_samples

    def _maximin(self) -> np.ndarray:
        """"
        Draw samples by maximizing the minimum distance between samples.
        """
        if self.iteration is None:
            self.iteration = 100
        
        # max --> min?
        min_distance = 0
        lhs_samples = np.zeros((self.nsamples, self.ndim))
        for i in range(self.iteration):
            temp_samples = self._random()
            temp_distance = pdist(temp_samples)
            if np.min(temp_distance) > min_distance:
                min_distance = np.min(temp_distance)
                lhs_samples = temp_samples
        return lhs_samples