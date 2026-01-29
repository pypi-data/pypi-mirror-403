from SALib.analyze import sobol
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from scipy.stats import norm
from typing import Union
from beartype import beartype

class SobolAnalyze:

    @beartype
    def __init__(
        self, ndim: int, Y: np.ndarray, calc_second_order: bool = True,
        nresamples: int = 100, conf_level: float = 0.95,
        seed: Union[int, None] = None) -> None:
        """
        Sobol' sensitivity analysis.
        This class is built based on :py:func:`SALib.analyze.sobol`.
        
        Parameters
        ----------
        ndim : int
            Dimension of parameter ``x``.
        Y : numpy array
            Model outputs evaluated at varaible input points drawn by Saltelli
            sampling. Shape of :code:`(nsaltelli, nrealizations)`. ``nsaltelli``
            is the number of Saltelli sample points, and ``nrealizations`` is
            the number of  realizations of model output at one input point.
            More specially: :math:`nrealizations=1` for a deterministic model
            which returns a scalar output at one input point,
            and :math:`nrealizations>1` for a stochastic model which returns
            multiple realizations of a scalar output at one input point (such
            as a Gaussian process model).
            If :math:`nrealizations=1`, an array of shape :code:`(nsaltelli,)`
            is also valid.
        calc_second_order : bool, optional
            If `True`, calculate secord order Sobol' indices.
        nresamples : int, optional
            Size of bootstrap sampling.
        conf_level : float, optional
            Confidence interval level. Must be a value within the range
            :math:`(0,1)`.
        seed : int, optional
            Seed to initialize the pseudo-random number generator.
        """

        self.ndim = ndim

        if not (Y.ndim == 1 or Y.ndim == 2):
            raise ValueError("Y must be a one or two dimensional numpy array")
        elif Y.ndim == 1:
            Y = Y.reshape((-1, 1))
        
        if calc_second_order and Y.shape[0] % (2 * ndim + 2) == 0:
            nbase = int(Y.shape[0] / (2 * ndim + 2))
        elif not calc_second_order and Y.shape[0] % (ndim + 2) == 0:
            nbase = int(Y.shape[0] / (ndim + 2))
        else:
            raise RuntimeError("Y does not match ndim and calc_second_order")
        
        self.Y = Y
        self.nbase = nbase
        self.nrealizations = Y.shape[1]

        self.calc_second_order = calc_second_order
        self.nresamples = nresamples
        
        if not (conf_level > 0 and conf_level < 1):
            raise ValueError("conf_level must be within 0 and 1")
        self.conf_level = conf_level
        
        self.rng = np.random.default_rng(seed)
        self.seed = seed
    
    @beartype
    def run(self, mode: Union[str, None] = None,
        max_workers: Union[int, None] = None) -> dict[str, np.ndarray]:
        """Perform Sobol' analysis.

        Parameters
        ----------
        mode : str, optional
            `'parallel'` or `'serial'`. Run sobol' analysis for each colomn of
            ``Y`` in parallel or in serial. Only relevant when
            :math:`nrealizations>1`.
        max_workers : int, optional
            The maximum number of tasks running in parallel.
            Default is the number of CPUs on the host.
            Only relevant when :math:`nrealizations>1`.
        
        Returns
        -------
        S_res : dict
            Sobol' sensitivity indices.
            `S_res['S1']` - :class:`numpy.ndarray` of shape :code:`(ndim, 3)`,
            first-order Sobol' index, its std, and conf_level for each parameter.
            `S_res['ST']` - :class:`numpy.ndarray` of shape :code:`(ndim, 3)`,
            total-effect Sobol' index, its std, and conf_level for each parameter.
            `S_res['S2']` - :class:`numpy.ndarray` of shape
            :code:`(ndim*(ndim-1)/2, 3)`, second-order Sobol' index, its std,
            and conf_level for each pair of parameters. 
            `S_res['S2']` is only available if ``calc_second_order`` is True.
        """
        if (mode is not None) and (mode not in ["parallel", "serial"]):
            raise ValueError(
                f"{mode} is not supported. Choose 'parallel' or 'serial'")

        if self.nrealizations == 1:
            S_all = self._base_analyze(self.Y[:,0])
        else:
            if mode == "parallel":
                S_all = self._parallel_run(max_workers)
            else:
                S_all = self._serial_run()    
                
        z = norm.ppf(0.5 + self.conf_level/2)

        S_res = {'S1' : np.zeros((self.ndim,3)), 'ST' : np.zeros((self.ndim,3))}

        S_res['S1'][:,0] = np.mean(S_all['S1'], axis=(1,2))
        S_res['S1'][:,1] = np.std(S_all['S1'], axis=(1,2))
        S_res['S1'][:,2] = S_res['S1'][:,1] * z
        
        S_res['ST'][:,0] = np.mean(S_all['ST'], axis=(1,2))
        S_res['ST'][:,1] = np.std(S_all['ST'], axis=(1,2))
        S_res['ST'][:,2] = S_res['ST'][:,1] * z

        if self.calc_second_order:
            S_res.update(
                {'S2' : np.zeros((int(self.ndim * (self.ndim - 1) / 2), 3))}
            )
            S_res['S2'][:,0] = np.mean(S_all['S2'], axis=(1,2))
            S_res['S2'][:,1] = np.std(S_all['S2'], axis=(1,2))
            S_res['S2'][:,2] = S_res['S2'][:,1] * z
        
        return S_res

    
    def _serial_run(self):
        """Run Sobol' analysis for each colomn of ``Y`` in serial."""
        S_all = self._create_S_dict(self.nrealizations)

        for nr in range(self.nrealizations):
            S = self._base_analyze(self.Y[:,nr])
            S_all['S1'][:,:,nr] = S['S1'][:,:,0]
            S_all['ST'][:,:,nr] = S['ST'][:,:,0]
            if self.calc_second_order:
                S_all['S2'][:,:,nr] = S['S2'][:,:,0]
        
        return S_all
            

    def _parallel_run(self, max_workers):
        """Run Sobol' analysis for each colomn of ``Y`` in parallel."""
        S_all = self._create_S_dict(self.nrealizations)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._base_analyze, self.Y[:,nr])
                for nr in range(self.nrealizations)]
            
            for nr in range(self.nrealizations):
                S = futures[nr].result()
                S_all['S1'][:,:,nr] = S['S1'][:,:,0]
                S_all['ST'][:,:,nr] = S['ST'][:,:,0]
                if self.calc_second_order:
                    S_all['S2'][:,:,nr] = S['S2'][:,:,0]
        
        return S_all

    
    def _base_analyze(self, y):
        """
        Perform Sobol' sensitivity analysis for a deterministic model.

        Parameters
        ----------
        y : numpy array
            Model outputs evaluated at varaible input points drawn by Saltelli
            sampling. 1d array of shape :code:`(nsaltelli, )`.
        
        Returns
        -------
        S: dict
            Sobol's sensitivity indices.
            `S['S1']` - :class:`numpy.ndarray` of shape
            :code:`(ndim, nresamples+1, 1)`, first-order Sobol' indices of
            each parameter.
            `S['ST']` - :class:`numpy.ndarray` of shape
            :code:`(ndim, nresamples+1, 1)`, total-effect Sobol' indices of
            each parameter.
            `S['S2']` - :class:`numpy.ndarray` of shape
            :code:`(ndim*(ndim-1)/2, nresamples+1, 1)`, second-order Sobol'
            indices for each pair of parameters.
            `S['S2']` is only available if ``calc_second_order`` is True.
        """
        S = self._create_S_dict(nrealizations=1)
        
        if y.std() == 0:
            return S
        else:
            y = (y - y.mean()) / y.std()
        
        A, B, AB, BA = sobol.separate_output_values(
            y, self.ndim, self.nbase, self.calc_second_order)
        r = self.rng.integers(self.nbase, size=(self.nbase, self.nresamples))

        for j in range(self.ndim):
            S['S1'][j,0,0] = sobol.first_order(A, AB[:, j], B)
            S['ST'][j,0,0] = sobol.total_order(A, AB[:, j], B)

            S['S1'][j,1:,0] = sobol.first_order(A[r], AB[r, j], B[r])
            S['ST'][j,1:,0] = sobol.total_order(A[r], AB[r, j], B[r])
        
        if self.calc_second_order:
            s2_sequence = 0
            for j in range(self.ndim):
                for k in range(j + 1, self.ndim):
                    S['S2'][s2_sequence,0,0] = sobol.second_order(
                        A, AB[:, j], AB[:, k], BA[:, j], B)
                    S['S2'][s2_sequence,1:,0] = sobol.second_order(
                        A[r], AB[r, j], AB[r, k], BA[r, j], B[r])
                    s2_sequence += 1
        
        return S

    def _create_S_dict(self, nrealizations):
        """Create dict to store results."""
        S = {
            'S1' : np.zeros((self.ndim, self.nresamples + 1, nrealizations)),
            'ST' : np.zeros((self.ndim, self.nresamples + 1, nrealizations))
            }
        if self.calc_second_order:
            S.update(
                {'S2' : 
                np.zeros((
                    int(self.ndim * (self.ndim - 1) / 2),
                    self.nresamples + 1,
                    nrealizations))
                }
            )

        return S

