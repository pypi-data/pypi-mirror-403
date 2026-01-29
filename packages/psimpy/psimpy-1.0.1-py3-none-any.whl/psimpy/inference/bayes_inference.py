import sys
import numpy as np
from abc import ABC
from abc import abstractmethod
from typing import Union
from beartype.typing import Callable
from beartype import beartype
from psimpy.sampler import MetropolisHastings
from psimpy.utility import check_bounds

_min_float = 10**(sys.float_info.min_10_exp)
_max_float = 10**(sys.float_info.max_10_exp)
_max_e = np.log(np.array(_max_float, dtype=float))

class BayesInferenceBase(ABC):

    @beartype
    def __init__(
        self,
        ndim: int,
        bounds: Union[np.ndarray, None] = None,
        prior: Union[Callable, None] = None,
        likelihood: Union[Callable, None] = None,
        ln_prior: Union[Callable, None] = None,
        ln_likelihood: Union[Callable, None] = None,
        ln_pxl: Union[Callable, None] = None,
        args_prior: Union[list, None] = None,
        kwgs_prior: Union[dict, None] = None,
        args_likelihood: Union[list, None] = None,
        kwgs_likelihood: Union[dict, None]=None,
        args_ln_pxl: Union[list, None] = None,
        kwgs_ln_pxl: Union[dict, None]=None) -> None:
        """
        Set up basic input for Bayesian inference.
    
        Parameters
        ----------
        ndim : int
            Dimension of parameter ``x``.
        bounds : numpy array
            Upper and lower boundaries of each parameter.
            Shape :code:`(ndim, 2)`. 
            `bounds[:, 0]` corresponds to lower boundaries of each parameter and
            `bounds[:, 1]` to upper boundaries of each parameter. 
        prior : Callable
            Prior probability density function.
            Call with :code:`prior(x, *args_prior, **kwgs_prior)`.
            Return the prior probability density value at ``x``, where ``x`` is
            a one dimension :class:`numpy.ndarray` of shape :code:`(ndim,)`.
        likelihood : Callable
            Likelihood function.
            Call with :code:`likelihood(x, *args_likelihood, **kwgs_likelihood)`.
            Return the likelihood value at ``x``.
        ln_prior : Callable
            Natural logarithm of prior probability density function.
            Call with :code:`ln_prior(x, *args_prior, **kwgs_prior)`.
            Return the value of natural logarithm of prior probability density
            at ``x``.
        ln_likelihood : Callable
            Natural logarithm of likelihood function.
            Call with :code:`ln_likelihood(x, *args_likelihood, **kwgs_likelihood)`.
            Return the value of natural logarithm of likelihood at ``x``.
        ln_pxl : Callable
            Natural logarithm of the product of prior and likelihood.
            Call with :code:`ln_pxl(x, *args_ln_pxl, **kwgs_ln_pxl)`.
            Return the value of natural logarithm of the product of prior and
            likelihood at ``x``.    
        args_prior : list, optional
            Positional arguments for ``prior`` or ``ln_prior``.
        kwgs_prior: dict, optional
            Keyword arguments for ``prior`` or ``ln_prior``.
        args_likelihood : list, optional
            Positional arguments for ``likelihood`` or ``ln_likelihood``.
        kwgs_likelihood : dict, optional
            Keyword arguments for ``likelihood`` or ``ln_likelihood``.
        args_ln_pxl : list, optional
            Positional arguments for ``ln_pxl``.
        kwgs_ln_pxl : dict, optional
            Keyword arguments for ``ln_pxl``.
        """
        self.ndim = ndim            
        self.bounds = bounds

        self.args_prior = () if args_prior is None else args_prior
        self.kwgs_prior = {} if kwgs_prior is None else kwgs_prior

        self.args_likelihood = () if args_likelihood is None else args_likelihood
        self.kwgs_likelihood = {} if kwgs_likelihood is None else kwgs_likelihood

        self.args_ln_pxl = () if args_ln_pxl is None else args_ln_pxl
        self.kwgs_ln_pxl = {} if kwgs_ln_pxl is None else kwgs_ln_pxl

        if ln_pxl is not None:
            self.ln_pxl = ln_pxl
        elif (ln_prior is not None) and (ln_likelihood is not None):
            self.ln_prior = ln_prior
            self.ln_likelihood = ln_likelihood
            self.ln_pxl = self._ln_pxl_1
            self.args_ln_pxl = ()
            self.kwgs_ln_pxl = {}
        elif (prior is not None) and (likelihood is not None):
            self.prior = prior
            self.likelihood = likelihood
            self.ln_pxl = self._ln_pxl_2
            self.args_ln_pxl = ()
            self.kwgs_ln_pxl = {}
        else:
            raise ValueError((
                "One of the following inputs is necessary:"
                " (1) `ln_pxl`"
                " (2) `ln_prior` and `ln_likelihood`"
                " (3) `prior` and `likelihood`"))
    
    def _ln_pxl_1(self, x: np.ndarray) -> float:
        """
        Construct ``ln_pxl``, given ``ln_prior`` and ``ln_likelihood``.
        """
        ln_pxl = self.ln_prior(x, *self.args_prior, **self.kwgs_prior) + \
            self.ln_likelihood(x, *self.args_likelihood, **self.kwgs_likelihood)

        return float(ln_pxl)
    
    def _ln_pxl_2(self, x: np.ndarray) -> float:
        """
        Construct ``ln_pxl``, given ``prior`` and ``likelihood``.
        """
        pxl = self.prior(x, *self.args_prior, **self.kwgs_prior) * \
            self.likelihood(x, *self.args_likelihood, **self.kwgs_likelihood)
        ln_pxl = np.log(np.maximum(pxl, _min_float))
        
        return float(ln_pxl)

    @abstractmethod
    def run(self, *args, **kwgs):
        pass


class GridEstimation(BayesInferenceBase):
    
    @beartype
    def run(self, nbins: Union[int, list[int]]
        ) -> tuple[np.ndarray, list[np.ndarray]]:
        """
        Use Grid approximation to estimate the posterior.

        Parameters
        ----------
        nbins : int or list of ints
            Number of bins for each parameter.
            If `int`, the same value is used for each parameter.
            If `list of int`, it should be of length ``ndim``.
        
        Returns
        -------
        posterior : numpy array
            Estimated posterior probability density values at grid points.
            Shape of :code:`(nbins[0], nbins[1], ..., nbins[ndim])`.
        x_ndim : list of numpy array
            Contain ``ndim`` 1d :class:`numpy.ndarray` `x1`, `x2`, ... Each `xi`
            is a 1d array of length ``nbins[i]``, representing the 1d coordinate
            array along the i-th axis.

        """
        if isinstance(nbins, int):
            nbins = [nbins] * self.ndim
        elif len(nbins) != self.ndim:
            raise ValueError(
                "nbins must be an integer or a list of ndim integers")

        if self.bounds is None:
            raise ValueError("bounds must be provided for grid estimation")
        else:
            check_bounds(self.ndim, self.bounds)
        
        steps = (self.bounds[:,1] - self.bounds[:,0]) / np.array(nbins) 
        starts = steps/2 + self.bounds[:,0]
        stops = self.bounds[:,1]  
        
        x_ndim = [np.arange(starts[i], stops[i], steps[i])
            for i in range(self.ndim)]
        xx_matrices = np.meshgrid(*x_ndim, indexing='ij')
        grid_point_coords = np.hstack(
            tuple(matrix.reshape((-1,1)) for matrix in xx_matrices)
            )
        
        n = len(grid_point_coords)
        ln_unnorm_posterior = np.zeros(n)
        for i in range(n):
            point_i = grid_point_coords[i,:]
            ln_unnorm_posterior[i] = \
                self.ln_pxl(point_i, *self.args_ln_pxl, **self.kwgs_ln_pxl)
        
        ln_unnorm_posterior = ln_unnorm_posterior.reshape(xx_matrices[0].shape)
        ln_unnorm_posterior = np.where(
            ln_unnorm_posterior >= _max_e, _max_e, ln_unnorm_posterior)
        unnorm_posterior = np.exp(ln_unnorm_posterior)
        posterior = unnorm_posterior / np.sum(unnorm_posterior) / np.prod(steps)
        
        return posterior, x_ndim


class MetropolisHastingsEstimation(BayesInferenceBase):

    def run(self, nsamples: int, mh_sampler: MetropolisHastings) -> tuple[
        np.ndarray, np.ndarray]:
        """
        Use Metropolis Hastings sampling to draw samples from the posterior.

        Parameters
        ----------
        nsamples : int
            Number of samples to be drawn.
        mh_sampler : instance of :class:`.MetropolisHastings`
            Metropolis Hastings sampler.
        
        Returns
        -------
        mh_samples : numpy array
            Samples drawn from the posterior. Shape of :code:`(nsamples, ndim)`.
        mh_accept : numpy array
            Shape of :code:`(nsamples,)`. Each element indicates whether the
            corresponding sample is the proposed new state (value 1) or the old
            state (value 0). :code:`np.mean(mh_accept)` thus gives the overall
            acceptance ratio.
        """
        if mh_sampler.ndim != self.ndim:
            raise RuntimeError(
                "ndim of mh_sampler and ndim defined in this class must be"
                " consistent")
        
        if type(self.bounds) != type(mh_sampler.bounds):
            raise RuntimeError(
                "bounds of mh_sampler and bounds defined in this class must be"
                " consistent")
        elif isinstance(self.bounds, np.ndarray) and \
            not np.all(np.equal(self.bounds, mh_sampler.bounds)):
            raise RuntimeError(
                "bounds of mh_sampler and bounds defined in this class must be"
                " consistent")

        mh_sampler.ln_target = self.ln_pxl
        mh_sampler.args_target = self.args_ln_pxl
        mh_sampler.kwgs_target = self.kwgs_ln_pxl
        
        mh_samples, mh_accept = mh_sampler.sample(nsamples)

        return mh_samples, mh_accept
