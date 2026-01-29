from SALib.sample import saltelli
import numpy as np
from typing import Union
from beartype import beartype
from psimpy.utility import check_bounds

class Saltelli:
    
    @beartype
    def __init__(
        self, ndim: int, bounds: Union[np.ndarray, None] = None,
        calc_second_order: bool = True, skip_values: Union[int, None] = None
        ) -> None:
        """Saltelli's version of Sobol' sampling.
        
        Parameters
        -------------
        ndim : int
            Dimension of parameters.
        bounds : numpy array, optional
            Upper and lower boundaries of each parameter. Shape :code:`(ndim, 2)`.
            `bounds[:, 0]` corresponds to lower boundaries of each parameter and
            `bounds[:, 1]` to upper boundaries of each parameter. 
        calc_second_order : bool, optional
            If `True`, calculate second-order Sobol' indices.
            If `False`, second-order Sobol' indices are not computed.
        skip_values : int, optional
            Number of points to skip in the Sobol' sequence. It should be 
            ideally a value of base :math:`2`.
        """
        if bounds is None:
            bounds = np.array([[0, 1] for i in range(ndim)])
        else:
            check_bounds(ndim, bounds)

        self.problem = {
            'num_vars': ndim,
            'names': [f"x{i}" for i in range(ndim)],
            'bounds': bounds
        }
        self.calc_second_order = calc_second_order
        self.skip_values = skip_values
    
    def sample(self, nbase: int) -> np.ndarray:
        """Draw samples using Saltelli's extension of the Sobol' sequence.
        
        Parameters
        ----------
        nbase : int
            Number of base samples. Correspond to the parameter ``N`` of 
            :py:func:`SALib.sample.saltelli.sample`.
        
        Returns
        -------
        samples : numpy array
            Shape of :code:`(nbase*(2*ndim+2), ndim)` if ``calc_second_order``
            is `True`. Shape of :code:`(nbase*(ndim+2), ndim)` if
            ``calc_second_order`` is `False`. 
        """
        samples = saltelli.sample(
            self.problem, nbase, calc_second_order=self.calc_second_order,
            skip_values=self.skip_values)
        
        return samples