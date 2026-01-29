import sys
import numpy as np
from scipy import optimize
from typing import Union
from beartype.typing import Callable
from beartype import beartype
from psimpy.simulator import RunSimulator
from psimpy.sampler import LHS
from psimpy.emulator import ScalarGaSP
from psimpy.utility import check_bounds

_min_float = 10**(sys.float_info.min_10_exp)

class ActiveLearning:

    @beartype
    def __init__(
        self,
        ndim: int,
        bounds: np.ndarray,
        data: np.ndarray,
        run_sim_obj: RunSimulator,
        prior: Callable,
        likelihood: Callable, 
        lhs_sampler: LHS,
        scalar_gasp: ScalarGaSP,
        scalar_gasp_trend: Union[str, Callable[[np.ndarray], np.ndarray]] = 'constant',
        indicator: str = 'entropy',
        optimizer: Callable = optimize.brute,
        args_prior: Union[list, None] = None,
        kwgs_prior: Union[dict, None] = None,
        args_likelihood: Union[list, None] = None,
        kwgs_likelihood: Union[dict, None] = None,
        args_optimizer: Union[list, None] = None,
        kwgs_optimizer: Union[dict, None] = None) -> None:
        """
        Contruct a scalar GP emulator for natural logarithm  of the product of
        prior and likelihood (i.e. unnormalized posterior), via active learning. 

        Parameters
        ----------
        ndim : int
            Dimension of parameter ``x``.
        bounds : numpy array
            Upper and lower boundaries of each parameter. Shape :code:`(ndim, 2)`.
            `bounds[:, 0]` corresponds to lower boundaries of each parameter and
            `bounds[:, 1]` to upper boundaries of each parameter. 
        data : numpy array
            Observed data for parameter calibration.
        run_sim_obj : instance of class :class:`.RunSimulator`
            It has an attribute :py:attr:`simulator` and two methods to run 
            :py:attr:`simulator`, namely :meth:`.serial_run` and
            :meth:`.parallel_run`. For each simulation, :py:attr:`simulator`
            must return outputs ``y`` as a numpy array.
        prior : Callable
            Prior probability density function.
            Call with :code:`prior(x, *args_prior, **kwgs_prior)` and return
            the value of prior probability density at ``x``.
        likelihood : Callable
            Likelihood function constructed based on ``data`` and simulation
            outputs ``y`` evaluated at ``x``. Call with
            :code:`likelihood(y, data, *args_likelihood, **kwgs_likelihood)`
            and return the likelihood value at ``x``.
        lhs_sampler : instance of class :class:`.LHS`
            Latin hypercube sampler used to draw initial samples of ``x``.
            These initial samples are used to run initial simulations and build
            initial emulator.
        scalar_gasp : instance of class :class:`.ScalarGaSP`
            An object which sets up the emulator structure. Providing training
            data, the emulator can be trained and used to make predictions. 
        scalar_gasp_trend : str or Callable, optional
            Mean function of ``scalar_gasp`` emulator, which is used to
            determine the ``trend`` or ``testing_trend`` at given ``design`` or
            ``testing_input``.
            `'zero'` - trend is set to zero.
            `'constant'` - trend is set to a constant.
            `'linear'` - trend is linear to design or testing_input.
            Callable - a function takes design or testing_input as parameter
            and returns the trend.
            Default is `'constant'`.
        indicator : str, optional
            Indicator of uncertainty. `'entropy'` or `'variance'`. Default is
            `'entropy'`.
        optimizer : Callable, optional
            A function which finds the input point ``x`` that minimizes the
            uncertainty ``indicator`` at each iteration step.
            Call with :code:`optimizer(func, *args_optimizer, **kwgs_optimizer)`. 
            The objective function ``func`` is defined by the class method
            :meth:`_uncertainty_indicator` which have only one argument ``x``.
            The ``optimizer`` should return either the solution array, or a
            :class:`scipy.optimize.OptimizeResult` object which has the attribute
            :py:attr:`x` denoting the solution array.
            By default is set to :py:func:`scipy.optimize.brute`.
        args_prior : list, optional
            Positional arguments for ``prior``.
        kwgs_prior: dict, optional
            Keyword arguments for ``prior``.
        args_likelihood : list, optional
            Positional arguments for ``likelihood``.
        kwgs_likelihood : dict, optional
            Keyword arguments for ``likelihood``.
        args_optimizer : list, optional
            Positional arguments for ``optimizer``.
        kwgs_optimizer : dict, optional
            Keyword arguments for ``optimizer``.
        """
        if ndim != len(run_sim_obj.var_inp_parameter):
            raise RuntimeError("ndim and run_sim_obj are incompatible")
        if ndim != lhs_sampler.ndim:
            raise RuntimeError("ndim and lhs_sampler are incompatible")
        if ndim != scalar_gasp.ndim:
            raise RuntimeError("ndim and scalar_gasp are incompatible")
        self.ndim = ndim

        check_bounds(ndim, bounds)
        self.bounds = bounds           
        
        self.data = data

        self.run_sim_obj = run_sim_obj
        self.prior = prior
        self.likelihood = likelihood

        self.lhs_sampler = lhs_sampler
        self.lhs_sampler.bounds = bounds
        
        self.scalar_gasp = scalar_gasp

        if isinstance(scalar_gasp_trend, str):
            if scalar_gasp_trend not in ["zero","constant","linear"]:
                raise NotImplementedError(
                    f"unsupported scalar_gasp_trend {scalar_gasp_trend}"
                    f" please choose from 'zero', 'constant', and 'linear'"
                    f" or pass it as a function")            
        self.scalar_gasp_trend = scalar_gasp_trend
        
        if indicator not in ["entropy", "variance"]:
            raise NotImplementedError(
                f"unsupported indicator {indicator}. Please choose from"
                f" 'entropy' and 'variance'")
        self.indicator = indicator
    
        if optimizer is optimize.brute:
            ranges = tuple(tuple(bounds[i]) for i in range(ndim))
            args_optimizer = [ranges]
            if kwgs_optimizer is not None:
                allowed_keys = {"Ns", "workers"}
                if not set(kwgs_optimizer.keys()).issubset(allowed_keys):
                    raise ValueError(
                        "allowed keys are 'Ns' and 'workers' for"
                        " optimize.brute")
            else:
                kwgs_optimizer = {"Ns": 50}
            kwgs_optimizer.update({"finish": None})
        self.optimizer = optimizer

        self.args_prior = () if args_prior is None else args_prior
        self.kwgs_prior = {} if kwgs_prior is None else kwgs_prior

        self.args_likelihood = () if args_likelihood is None else args_likelihood
        self.kwgs_likelihood = {} if kwgs_likelihood is None else kwgs_likelihood

        self.args_optimizer=() if args_optimizer is None else args_optimizer
        self.kwgs_optimizer={} if kwgs_optimizer is None else kwgs_optimizer


    @beartype
    def initial_simulation(
        self,
        n0: int,
        prefixes: Union[list[str], None] = None,
        mode: str = 'serial',
        max_workers: Union[int, None] = None) -> tuple[np.ndarray, np.ndarray]:
        """
        Run ``n0`` initial simulations.

        Parameters
        ----------
        n0 : int
            Number of initial simulation runs.
        prefixes : list of str, optional
            Consist of ``n0`` strings. Each is used to name corresponding
            simulation output file(s).
            If `None`, `'sim0'`, `'sim1'`, ... are used.   
        mode : str, optional
            `'parallel'` or `'serial'`. Run `n0` simulations in parallel or
            in serial.
        max_workers : int, optional
            Controls the maximum number of tasks running in parallel.
            Default is the number of CPUs on the host.
        
        Returns
        -------
        init_var_samples: numpy array
            Variable input samples for ``n0`` initial simulations.
            Shape of :code:`(n0, ndim)`.
        init_sim_outputs : numpy array
            Outputs of ``n0`` intial simulations.
            :code:`init_sim_outputs.shape[0]` is ``n0``.
        """
        init_var_samples = self.lhs_sampler.sample(n0)

        if mode == 'parallel':
            self.run_sim_obj.parallel_run(init_var_samples, prefixes,
                append=False, max_workers=max_workers)
        elif mode == 'serial':
            self.run_sim_obj.serial_run(init_var_samples, prefixes,
                append=False)
        else:
            raise ValueError("mode must be 'parallel' or 'serial'")
        
        init_sim_outputs = np.array(self.run_sim_obj.outputs)

        return init_var_samples, init_sim_outputs
    
    @beartype
    def iterative_emulation(
        self,
        ninit: int,
        init_var_samples: np.ndarray,
        init_sim_outputs: np.ndarray,
        niter: int,
        iter_prefixes: Union[list[str], None] = None
        ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Sequentially pick ``niter`` new input points based on ``ninit``
        simulations.

        Parameters
        ----------
        niter : int
            Number of interative simulaitons.
        ninit : int
            Number of initial simulations.
        init_var_samples: numpy array
            Variable input samples for ``ninit`` simulations.
            Shape of :code:`(ninit, ndim)`.
        init_sim_outputs : numpy array
            Outputs of ``ninit`` simulations.
            :code:`init_sim_outputs.shape[0]` is ``ninit``. 
        iter_prefixes : list of str, optional
            Consist of ``niter`` strings. Each is used to name
            corresponding iterative simulation output file(s).
            If `None`, `'iter_sim0'`, `'iter_sim1'`, ... are used.

        Returns
        -------
        var_samples : numpy array
            Variable input samples of ``ninit`` simulations and ``niter``
            iterative simulations. Shape of :code:`(ninit+niter, ndim)`.
        sim_outputs : numpy array
            Outputs of ``ninit`` and ``niter`` simulations. 
            :code:`sim_outputs.shape[0]` is :math:`ninit+niter`.
        ln_pxl_values : numpy array
            Natural logarithm values of the product of prior and likelihood 
            at ``ninit`` and ``niter`` simulations. 
            Shape of :code:`(ninit+niter,)`.
        
        Notes
        -----
        If a duplicated iteration point is returned by the ``optimizer``, the
        iteration will be stopped right away. In that case, the first dimension
        of returned ``var_samples``, ``sim_outputs``, ``ln_pxl_values`` is smaller
        than :math:`ninit+niter`.
        """
        if init_var_samples.shape != (ninit, self.ndim):
            raise ValueError("init_var_samples must be of shape (ninit, ndim)")
        
        if init_sim_outputs.shape[0] != ninit:
            raise ValueError(
                "init_sim_outputs.shape[0] must equal to ninit")
        
        if iter_prefixes is None:
            iter_prefixes = [f'iter_sim{i}' for i in range(niter)]
        elif len(iter_prefixes) != niter:
            raise ValueError("iter_prefixes must have niter number of items")
        elif len(set(iter_prefixes)) != niter:
            raise ValueError("Each item of iter_prefixes must be unique")
        
        ln_pxl_values = [
            self._compute_ln_pxl(init_var_samples[i,:], init_sim_outputs[i])
            for i in range(ninit)
            ]
        var_samples = init_var_samples
        sim_outputs = init_sim_outputs
        
        for i in range(niter):
            
            self._emulate_ln_pxl(var_samples, np.array(ln_pxl_values))

            opt_res = self.optimizer(
                self._uncertainty_indicator,
                *self.args_optimizer,
                **self.kwgs_optimizer)
            if isinstance(opt_res, np.ndarray):
                next_var_sample = opt_res
            elif isinstance(opt_res, optimize.OptimizeResult):
                next_var_sample = opt_res.x
            else:
                raise RuntimeError(
                    "Optimizer must return a 1d numpy array representing the"
                    " solution or a OptimizeResult object having x attribute")
            
            next_var_sample = next_var_sample.reshape((1, self.ndim))
            temp_var_samples = np.vstack((var_samples, next_var_sample))

            if len(np.unique(temp_var_samples, axis=0)) != len(var_samples) + 1:
                print(
                    "Optimizer finds duplicated next_var_sample at"
                    " iteration {i}. The active learning process will"
                    " be terminated.")
                break

            var_samples = temp_var_samples

            self.run_sim_obj.serial_run(next_var_sample, [iter_prefixes[i]],
                append=False)
            next_sim_output = self.run_sim_obj.outputs[0]
            sim_outputs = np.vstack((sim_outputs, np.array([next_sim_output])))

            next_ln_pxl_value = self._compute_ln_pxl(
                next_var_sample.reshape(-1), next_sim_output)
            ln_pxl_values.append(next_ln_pxl_value)
        
        # train final scalar gasp
        self._emulate_ln_pxl(var_samples, np.array(ln_pxl_values))
        
        ln_pxl_values = np.array(ln_pxl_values)
        
        return var_samples, sim_outputs, ln_pxl_values

    @beartype
    def approx_ln_pxl(self, x: np.ndarray) -> float:
        """
        Approximate `ln_pxl` value at ``x`` based on the trained emulator.

        Parameters
        ----------
        x : numpy array
            One variable sample at which `ln_pxl` is to be approximated. Shape of
            :code:`(ndim,)`.
        
        Returns
        -------
        A float value which is the emulator-predicted `ln_pxl` value at ``x``.
        """
        predict = self._predict_ln_pxl(x)

        return float(predict[:,0])

    
    def _compute_ln_pxl(self, x: np.ndarray, y: np.ndarray) -> float:
        """Compute natural logarithm of the product of prior and likelihood.
        
        Parameters
        ----------
        x : numpy array
            Variable input of :py:func:`simulator`. Shape of :code:`(ndim,)`.
        y : numpy array
            Simulation outputs at ``x``.
        
        Returns
        -------
        ln_pxl_val : float
            Natural logarithm of the product of prior and likelihood at ``x``.
        """
        prior_val = self.prior(x, *self.args_prior, **self.kwgs_prior)
        likelihood_val = self.likelihood(y, self.data, *self.args_likelihood,
            **self.kwgs_likelihood)
        pxl_val = prior_val * likelihood_val
        
        return float(np.log(np.maximum(pxl_val, _min_float)))

    
    def _emulate_ln_pxl(self, var_samples: np.ndarray, ln_pxl_values: np.ndarray
        ) -> None:
        """
        Train scalar gasp emulator for natural lograthim of the product of prior
        and likelihood based on ``n`` simulations.

        Parameters
        ----------
        var_samples: numpy array
            Variable inputs samples for ``n`` simulations. Shape of
            :code:`(n, ndim)`.
        ln_pxl_values : numpy array
            Natural lograthim values of the product of prior and likelhood
            corresponding to ``n`` simulations. Shape of :code:`(n,)`.
        """
        n = len(var_samples) 

        if isinstance(self.scalar_gasp_trend, str):
            if self.scalar_gasp_trend == "zero":
                trend = np.zeros((n, 1))
            elif self.scalar_gasp_trend == "constant":
                trend = np.ones((n, 1))
            elif self.scalar_gasp_trend == "linear":
                trend = np.c_[np.ones(n), var_samples]
        else:
            trend = self.scalar_gasp_trend(var_samples)

        self.scalar_gasp.train(var_samples, ln_pxl_values, trend)
    
    def _predict_ln_pxl(self, x: np.ndarray) -> np.ndarray:
        """
        Make prediction of `ln_pxl` at ``x`` using the emulator.

        Parameters
        ----------
        x : numpy array
            One variable input point. Shape of :code:`(ndim,)`.
        
        Returns
        -------
        predict : numpy array
            Emulator-prediction at ``x``. Shape :code:`(1, 4)`.
            `predict[0, 0]` - mean,
            `predict[0, 1]` - low95,
            `predict[0, 2]` - upper95,
            `predict[0, 3]` - sd.
        """
        x = x.reshape((1, self.ndim))

        if isinstance(self.scalar_gasp_trend, str): 
            if self.scalar_gasp_trend == "zero":
                trend = np.zeros((1, 1))
            elif self.scalar_gasp_trend == "constant":
                trend = np.ones((1, 1))
            elif self.scalar_gasp_trend == "linear":
                trend = np.c_[np.ones(1), x]
        else:
            trend = self.scalar_gasp_trend(x)
        
        predict = self.scalar_gasp.predict(x, trend)

        return predict

    def _uncertainty_indicator(self, x: np.ndarray) -> float:
        """
        Indicator of uncertainty.

        Parameters
        ----------
        x : numpy array
            One variable input point. Shape of :code:`(ndim,)`.
        
        Returns
        -------
        neg_val : float
            Negative value of uncertainty indicator at ``x``.
        """
        predict = self._predict_ln_pxl(x)
        
        mean = predict[:, 0]
        std = predict[:, 3]

        if self.indicator == "entropy":
            neg_val = -mean - 0.5*np.log(
                np.maximum(2*np.pi*np.e*std**2, _min_float)
                )
        elif self.indicator == "variance":
            neg_val = -(2*mean + 2*std**2) - np.log(
                np.maximum(1-np.exp(-std**2), _min_float)
                )
        
        return float(neg_val)