import sys
import numpy as np
from typing import Union
from beartype.typing import Callable
from beartype import beartype
from psimpy.utility import check_bounds

_min_float = 10**(sys.float_info.min_10_exp)

class MetropolisHastings:
    
    @beartype
    def __init__(
        self,
        ndim: int,
        init_state: np.ndarray,
        f_sample: Callable,
        target: Union[Callable, None] = None,
        ln_target: Union[Callable, None] = None,
        bounds: Union[np.ndarray, None] = None,
        f_density: Union[Callable, None] = None,
        symmetric: bool = True,
        nburn: int = 0,
        nthin: int = 1,
        seed: Union[int, None] = None,
        args_target: Union[list, None] = None,
        kwgs_target: Union[dict, None] = None,
        args_f_sample: Union[list, None] = None, 
        kwgs_f_sample: Union[dict, None] = None,
        args_f_density: Union[list, None] = None,
        kwgs_f_density: Union[dict, None] =None) -> None:
        """
        Metropolis Hastings sampling.
    
        Parameters
        ----------
        ndim : int
            Dimension of parameter ``x``.
        init_state : numpy array
            Contains ``ndim`` numeric values representing the starting point of
            the Metropolis hastings chain. Shape :code:`(ndim,)`.
        f_sample : Callable
            A function which proposes a new state ``x'`` given a current state
            ``x``. Call with :code:`f_sample(x, *args_f_sample, **kwgs_f_sample)`.
            Return the proposed state ``x'`` as a :class:`numpy.ndarray` of
            shape :code:`(ndim,)`. If :math:`ndim=1`, ``f_sample`` may also
            return a scalar value.
        target : Callable, optional
            Target probability density function, up to a normalizing constant. 
            Call with :code:`target(x, *args_target, **kwgs_target)`.
            Return the probability density value at ``x``. 
            If ``target`` is not given, ``ln_target`` must be provided.
        ln_target : Callable, optional
            Natural logarithm of target probability density function.
            Call with :code:`ln_target(x, *args_target, **kwgs_target)`.
            Return the value of natural logarithm of target probability density
            value at ``x``.
            If ``ln_target`` is not given, ``target`` must be provided.
        bounds : numpy array, optional
            Upper and lower boundaries of each parameter. Shape :code:`(ndim, 2)`.
            `bounds[:, 0]` corresponds to lower boundaries of each parameter and
            `bounds[:, 1]` to upper boundaries of each parameter. 
        f_density : Callable, optional
            Call with :code:`f_density(x1, x2, *args_f_density, **kwgs_f_density)`.
            Return the probability density at state ``x1`` given state ``x2``.
            It must be provided if ``symmetric`` is set to `False`.
        symmetric : bool, optional
            Whether ``f_density`` is symmetric or asymmetric.
        nburn : int, optional
            Number of burnin. Default no burnin.
        nthin : int, optional
            Number of thining to reduce dependency. Default no thining.
        seed : int, optional
            Seed to initialize the pseudo-random number generator.
            Default `None`.
        args_target : list, optional
            Positional arguments for ``target`` or ``ln_target``.
        kwgs_target : dict, optional
            Keyword arguments for ``target`` or ``ln_target``.
        args_f_sample : list, optional
            Positional arguments for ``f_sample``.
        kwgs_f_sample : dict, optional
            Keyword arguments for ``f_sample``.
        args_f_density : list, optional
            Positional arguments for ``f_density``.
        kwgs_f_density : dict, optional
            Keyword arguments for ``f_density``.
        """
        if len(init_state) != ndim:
            raise ValueError(f"init_state must contain ndim={ndim} elements")
        
        if bounds is not None:
            check_bounds(ndim, bounds)

            if not all([
                init_state[i] >= bounds[i,0] and
                init_state[i] <= bounds[i,1]
                for i in range(ndim)
            ]):
                raise ValueError("init_state violates bounds")

        if (not symmetric) and (f_density is None):
            raise ValueError("f_density must be provided if asymmetric")

        self.ndim = ndim
        self.init_state = init_state
        self.f_sample = f_sample
        self.target = target
        self.ln_target = ln_target
        self.bounds = bounds
        
        self.f_density = f_density
        self.symmetric = symmetric
        self.nburn = nburn
        self.nthin = nthin

        self.rng = np.random.default_rng(seed)
        self.seed = seed

        self.args_target = () if args_target is None else args_target
        self.args_f_sample = () if args_f_sample is None else args_f_sample
        self.args_f_density = () if args_f_density is None else args_f_density

        self.kwgs_target = {} if kwgs_target is None else kwgs_target
        self.kwgs_f_sample = {} if kwgs_f_sample is None else kwgs_f_sample
        self.kwgs_f_density = {} if kwgs_f_density is None else kwgs_f_density        
    
    def sample(self, nsamples: int) -> tuple[np.ndarray, np.ndarray]:
        """Draw samples.
        
        Parameters
        ----------
        nsamples : int
            Number of samples to be drawn.
        
        Returns
        -------
        mh_samples : numpy array
            Samples drawn from ``target``. Shape :code:`(nsamples, ndim)`.
        mh_accept : numpy array
            Shape of :code:`(nsamples,)`. Each element indicates whether the
            corresponding sample is the proposed new state (value 1) or the old
            state (value 0). :code:`np.mean(mh_accept)` thus gives the overall
            acceptance ratio.
        """ 
        if (self.target is None) and (self.ln_target is None):
            raise ValueError(
                "Either target or ln_target must be provided before call the"
                " sample method")
                 
        if self.ln_target is None:
            init_t = self.target(
                self.init_state, *self.args_target, **self.kwgs_target)
            ln_init_t = np.log(np.maximum(init_t, _min_float))
        else:
            ln_init_t = self.ln_target(
                self.init_state, *self.args_target, **self.kwgs_target)

        iter = 0
        niter = self.nburn + (nsamples-1)*self.nthin + 1
        
        _samples = np.zeros((niter, self.ndim))
        _accept = np.zeros(niter)
        
        current_state = self.init_state
        ln_current_t = ln_init_t

        while iter < niter:

            candidate_state = self.f_sample(
                current_state, *self.args_f_sample, **self.kwgs_f_sample)
            candidate_state = np.array(candidate_state).reshape(-1)
            
            if self.bounds is not None:
                if not all([
                    candidate_state[i] >= self.bounds[i,0] and
                    candidate_state[i] <= self.bounds[i,1]
                    for i in range(self.ndim)
                ]):
                    _samples[iter, :] = current_state
                    _accept[iter] = 0
                    iter += 1
                    continue
            
            if self.ln_target is None:
                candidate_t = self.target(
                    candidate_state, *self.args_target, **self.kwgs_target)
                ln_candidate_t = np.log(np.maximum(candidate_t, _min_float))
            else:
                ln_candidate_t = self.ln_target(
                    candidate_state, *self.args_target, **self.kwgs_target)

            diff_ln_t = ln_candidate_t - ln_current_t

            if self.symmetric:
                ln_accept = np.min(diff_ln_t, 0)
            else:
                current_f = self.f_density(current_state, candidate_state,
                    *self.args_f_density, **self.kwgs_f_density)
                ln_current_f = np.log(np.maximum(current_f, _min_float))

                candidate_f = self.f_density(candidate_state, current_state,
                    *self.args_f_density, **self.kwgs_f_density)
                ln_candidate_f = np.log(np.maximum(candidate_f, _min_float))
                
                diff_ln_f = ln_candidate_f - ln_current_f 
                ln_accept = np.min(diff_ln_t - diff_ln_f, 0)
            
            if ln_accept >= np.log(np.maximum(self.rng.random(), _min_float)):
                current_state = candidate_state
                ln_current_t = ln_candidate_t

                _samples[iter, :] = candidate_state
                _accept[iter] = 1

            else:
                _samples[iter, :] = current_state
                _accept[iter] = 0

            iter += 1
        
        mh_samples = _samples[self.nburn:niter:self.nthin, :]
        mh_accept = _accept[self.nburn:niter:self.nthin]

        return mh_samples, mh_accept