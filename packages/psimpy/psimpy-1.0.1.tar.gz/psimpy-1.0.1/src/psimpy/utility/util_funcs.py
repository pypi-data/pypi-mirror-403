import numpy as np
from beartype import beartype

@beartype
def check_bounds(ndim: int, bounds: np.ndarray) -> None:
    """Check if bounds are valid.
    
    Parameters
    ----------
    ndim : int
        Parameter dimension.
    bounds: numpy array
        Bounds of the `ndim` parameters, where bounds[:, 0] and bounds[:, 1] 
        correspond to lower and upper bounds, respectively. Shape (ndim, 2).
    """
    if bounds.ndim != 2:
        raise ValueError("bounds must be a 2d numpy array")
    elif bounds.shape[0] != ndim or bounds.shape[1] != 2:
        raise ValueError("bounds must be of shape (ndim, 2)")
    
    lower_bounds = bounds[:,0]
    upper_bounds = bounds[:,1]
    if np.any(lower_bounds >= upper_bounds):
        raise ValueError(
            "Lower bounds must be smaller than corresponding upper bounds")

@beartype
def scale_samples(samples: np.ndarray, bounds: np.ndarray) -> np.ndarray:
    """Scale samples from a unit hypercube to arbitrary `bounds`.
    
    Parameters
    ----------
    samples : numpy array
        Samples of shape (nsamples, ndim) from a unit hypercube , where
        `nsamples` is the number of samples and `ndim` is the dimension (number)
        of parameters.
    bounds : numpy array
        Bounds of the `ndim` parameters, where bounds[:, 0] and bounds[:, 1] 
        correspond to lower and upper bounds, respectively. Shape (ndim, 2).
    
    Returns
    -------
    scaled_samples : np.ndarray (nsamples, ndim) 
    
    """
    if not samples.ndim == 2:
        raise ValueError("samples must be a 2D array")
        
    ndim = samples.shape[1]
    check_bounds(ndim, bounds)
   
    lower_bounds = bounds[:,0]
    upper_bounds = bounds[:,1]   
    scaled_samples = samples*(upper_bounds-lower_bounds) + lower_bounds
    
    return scaled_samples
    
    