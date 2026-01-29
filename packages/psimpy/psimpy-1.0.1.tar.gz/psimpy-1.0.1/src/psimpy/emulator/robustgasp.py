import os

if "CONDA_PREFIX" in os.environ and "R_HOME" not in os.environ:
    # if a conda environment is active and the R_HOME variable was not set
    R_home = os.environ["CONDA_PREFIX"] + '/lib/R'
    if os.path.exists(R_home):
        os.environ['R_HOME'] = R_home

import numpy as np
from rpy2.robjects.packages import importr
import rpy2.robjects.numpy2ri
from rpy2.rinterface import NA
from rpy2.rinterface_lib.sexp import NALogicalType
from typing import Union
from beartype import beartype
from sklearn.model_selection import RepeatedKFold
from contextlib import nullcontext, contextmanager
from sklearn.metrics import mean_absolute_percentage_error, r2_score, root_mean_squared_error
import io
import sys

rpy2.robjects.numpy2ri.activate()
RobustGaSP = importr("RobustGaSP")

# fetch @
r_base = importr("base")
r_at = r_base.__dict__["@"]


class RobustGaSPBase:
    @beartype
    def __init__(
        self,
        ndim: int,
        zero_mean: str = "No",
        nugget: float = 0.0,
        nugget_est: bool = False,
        range_par: Union[np.ndarray, NALogicalType] = NA,
        method: str = "post_mode",
        prior_choice: str = "ref_approx",
        a: float = 0.2,
        b: Union[float, None] = None,
        kernel_type: str = "matern_5_2",
        isotropic: bool = False,
        optimization: str = "lbfgs",
        alpha: Union[np.ndarray, None] = None,
        lower_bound: bool = True,
        max_eval: Union[int, None] = None,
        num_initial_values: int = 2,
    ) -> None:
        """
        Set up basic parameters of the emulator.

        Parameters
        ----------
        ndim : int
            Input parameter dimension.
        zero_mean : str, optional
            If `'Yes'`, the mean is set to zero. If `'No'`, the mean is
            specified by ``trend``. Default is `'No'`.
        nugget : float, optional
            Nugget variance ratio.
            If :math:`0`, there is no nugget or the nugget is estimated.
            If not :math:`0`, it means a fixed nugget. Default is :math:`0`.
        nugget_est : bool, optional
            `True` means ``nugget`` should be estimated.
            `False` means ``nugget`` is fixed or not estimated.
            Default is `False`.
        range_par : numpy array, optional
            Range parameters. One dimension :class:`numpy.ndarray` of length
            ``ndim``. If given, range parameters are set to the given values
            rather than estimated based on training data.
            By default `NA`, meaning that range parameters are estimated based
            on training data.
        method : str, optional
            Method used for parameter estimation.
            `'post_mode'`: marginal posterior mode estimation, resulted emulator
            is a Student's t-process.
            `'mmle'`: maximum marginal likelihood estimation, resulted emulator
            is a Student's t-process.
            `'mle'`: maximum likelihood estimation, resulted emulator is a
            Gaussian process.
            Default is `'post_mode'`.
        prior_choice : str, optional
            `'ref_xi'`, `'ref_gamma'`, or `'ref_approx'`.
            Default is `'ref_approx'`.
        a : float, optional
            Prior parameters in the jointly robust prior. Default :math:`0.2`.
        b : float, optional
            Prior parameters in the jointly robust prior.
            Default value is :math:`ntrain^{-1/ndim}(a+ndim)`, where ``ntrain``
            is the number of training input points and ``ndim`` is input
            parameter dimension.
        kernel_type : str, optional
            `'matern_3_2'`: Matern correlation with roughness parameter :math:`3/2`.
            `'matern_5_2'`: Matern correlation with roughness parameter :math:`5/2`.
            `'pow_exp'`: power exponential correlation with roughness parameter
            ``alpha``.
            Default is `'matern_5_2'`.
        isotropic : bool, optional
            `True`: isotropic kernel. `False`: separable kernel.
            Default is `False`.
        optimization : str, optional
            Optimization method for kernel parameters.
            `'lbfgs'`: low storage version of the Broyden-Fletcher-Goldarb-Shanno
            method.
            `'nelder-mead'`: Nelder and Mead method.
            `'brent'`: Brent method for one-dimensional problems.
        alpha : numpy array, optional
            Roughness parameters in the `'pow_exp'` correlation functions. One
            dimension :class:`numpy.ndarray` of length ``ndim``.
            Default is a one dimension array with each entry being :math:`1.9`.
        lower_bound : bool
            `True`: the default lower bounds of the inverse range parameters are
            used to constrain the optimization.
            `False`: the optimization is unconstrained.
            Default is `True`.
        max_eval : int, optional
            Maximum number of steps to estimate the range and nugget parameters.
            Default is :math:`max(30,20+5*ndim)`.
        num_initial_values : int, optional
            Number of initial values of the kernel parameters in optimization.
            Default is :math:`2`.
        """
        self.ndim = ndim

        if zero_mean not in ["No", "Yes"]:
            raise ValueError("zero_mean can be either 'No' or 'Yes'.")
        self.zero_mean = zero_mean

        self.nugget = float(nugget)
        self.nugget_est = nugget_est

        if range_par is not NA:
            if range_par.ndim != 1 or len(range_par) != ndim:
                raise ValueError("range_par must be 1d numpy array of length ndim")
        self.range_par = range_par

        if method not in ["post_mode", "mmle", "mle"]:
            raise ValueError("method can only be 'post_mode', 'mmle', or 'mle'.")
        self.method = method

        if prior_choice not in ["ref_xi", "ref_gamma", "ref_approx"]:
            raise ValueError(
                "prior_choice can only be 'ref_xi', 'ref_gamma'," " or 'ref_approx'."
            )
        self.prior_choice = prior_choice

        self.a = float(a)
        self.b = b

        if kernel_type not in ["matern_3_2", "matern_5_2", "pow_exp"]:
            raise ValueError(
                "kernel_type can only be 'matern_3_2', 'matern_5_2'," " or 'pow_exp'."
            )
        self.kernel_type = kernel_type

        self.isotropic = isotropic

        if optimization not in ["lbfgs", "nelder-mead", "brent"]:
            raise ValueError(
                "optimization can only be 'lbfgs', 'nelder-mead', or 'brent'."
            )
        self.optimization = optimization

        if alpha is None:
            alpha = np.ones(ndim) * 1.9
        elif alpha.ndim != 1 or len(alpha) != ndim:
            raise ValueError("alpha must be 1d numpy array of length ndim")
        self.alpha = alpha.astype(np.float64)

        self.lower_bound = lower_bound

        if max_eval is None:
            max_eval = int(max(30, 20 + 5 * ndim))
        self.max_eval = max_eval

        self.num_initial_values = int(num_initial_values)

        self.emulator = None

    def _preprocess_design_response_trend(
        self, design: np.ndarray, response: np.ndarray, trend: np.ndarray
    ) -> None:
        """
        Preprocess design, response, and trend before train an emulator.

        Parameters
        ----------
        design : numpy array
            Training input points. Shape :code:`(ntrain, ndim)`.
            ``ntrain`` is the number of training points, ``ndim`` is the input
            dimension. If :math:`ndim=1`, both :code:`(ntrain, 1)` and
            :code:`(ntrain,)` :class:`numpy.ndarray` are valid.
        response : numpy array
            Training output points. Shape :code:`(ntrain, nresponse)`.
            ``nresponse`` is the number of QoIs of a single simulation.
            ``ntrain`` output points corresponding to ``design``.
            For child class :class:`.ScalarGaSP`, :math:`nresponse=1`.
            For child class :class:`.PPGaSP`, :math:`nresponse>1`.
        trend : numpy array
            Basis function matrix. Shape :code:`(ntrain, q)`.
            If `None`, a :code:`(ntrain, 1)` matrix of ones is used.
            If :math:`q=1`, both :code:`(ntrain, 1)` and :code:`(ntrain,)`
            :class:`numpy.ndarray` are valid.
        """
        if not (design.ndim == 1 or design.ndim == 2):
            raise ValueError("design must be 1d or 2d numpy array.")
        elif design.ndim == 1:
            design = np.reshape(design, (len(design), 1))

        if design.shape[1] != self.ndim:
            raise ValueError("design must match the input dimension ndim")

        self.design = design.astype(np.float64)

        if not (response.ndim == 1 or response.ndim == 2):
            raise ValueError("response must be 1d or 2d numpy array.")
        elif response.ndim == 1:
            response = np.reshape(response, (len(response), 1))
        if response.shape[0] != design.shape[0]:
            raise ValueError("response must have same number of points as design")
        self.response = response.astype(np.float64)

        if trend is None:
            trend = np.ones((design.shape[0], 1))
        elif not (trend.ndim == 1 or trend.ndim == 2):
            raise ValueError("trend must be 1d or 2d numpy array.")
        elif trend.ndim == 1:
            trend = np.reshape(trend, (len(trend), 1))
        if trend.shape[0] != design.shape[0]:
            raise ValueError("trend must have same numer of points as design")
        self.trend = trend.astype(np.float64)

        if self.zero_mean == "Yes":
            self.trend = np.zeros((design.shape[0], 1), dtype=np.float64)

        if self.b is None:
            self._b = (1 / design.shape[0]) ** (1 / design.shape[1]) * (
                self.a + design.shape[1]
            )
        else:
            self._b = self.b

    def _preprocess_testing_input_trend(
        self, testing_input: np.ndarray, testing_trend: np.ndarray
    ) -> None:
        """
        Preprocess testing_input and testing_trend before make prediction or
        draw samples.

        Parameters
        ----------
        testing_input : numpy array
            Input matrix to make prediction or draw samples.
            Shape :code:`(ntest, ndim)`.
            If :math:`ndim=1`, both :code:`(ntest, 1)` and :code:`(ntest,)`
            :class:`numpy.ndarray` are valid.
        testing_trend : numpy array
            Basis function matrix corresponds to ``testing_input``.
            Shape :code:`(ntest, q)`.
            By default :code:`(ntest, 1)` matrix of ones.
            If :math:`q=1`, both :code:`(ntest, 1)` and :code:`(ntest,)`
            :class:`numpy.ndarray` are valid.
        """
        if not (testing_input.ndim == 1 or testing_input.ndim == 2):
            raise ValueError("testing_input must be 1d or 2d numpy array.")
        elif testing_input.ndim == 1:
            testing_input = np.reshape(testing_input, (len(testing_input), 1))

        if testing_input.shape[1] != self.ndim:
            raise ValueError("testing_input must match the input dimension ndim")

        self.testing_input = testing_input.astype(np.float64)

        if self.zero_mean == "Yes":
            testing_trend = np.zeros((testing_input.shape[0], 1))
        elif testing_trend is None:
            testing_trend = np.ones((testing_input.shape[0], 1))
        elif not (testing_trend.ndim == 1 or testing_trend.ndim == 2):
            raise ValueError("testing_trend must be 1d or 2d numpy array.")
        elif testing_trend.ndim == 1:
            testing_trend = np.reshape(testing_trend, (len(testing_trend), 1))

        self.testing_trend = testing_trend.astype(np.float64)

        if testing_trend.shape[0] != testing_input.shape[0]:
            raise ValueError(
                "testing_trend must have same numer of points as testing_input"
            )

        if testing_trend.shape[1] != self.trend.shape[1]:
            raise ValueError(
                "testing_trend must have the same basis as the trend used"
                " for emulator training."
            )

    @contextmanager
    def _nostdout(self):
        """
        Discard any output to the standard output stream (stdout).
        """
        save_stdout = sys.stdout
        sys.stdout = io.StringIO()
        yield
        sys.stdout = save_stdout


class ScalarGaSP(RobustGaSPBase):
    @beartype
    def train(
        self,
        design: np.ndarray,
        response: np.ndarray,
        trend: Union[np.ndarray, None] = None,
        verbose: bool = True
    ) -> None:
        """
        Train a scalar GP given training data.

        Parameters
        ----------
        design : numpy array
            Training input points. Shape :code:`(ntrain, ndim)`.
            ``ntrain`` is the number of training points, ``ndim`` is the input
            dimension. If :math:`ndim=1`, both :code:`(ntrain, 1)` and
            :code:`(ntrain,)` :class:`numpy.ndarray` are valid.
        response : numpy array
            Training output points. Shape :code:`(ntrain, 1)` or
            :code:`(ntrain,)`.
        trend : numpy array, optional
            Basis function matrix. Shape :code:`(ntrain, q)`.
            If `None`, a :code:`(ntrain, 1)` matrix of ones is used.
            If :math:`q=1`, both :code:`(ntrain, 1)` and :code:`(ntrain,)`
            :class:`numpy.ndarray` are valid.
        verbose : bool, optional
            If `'True'`, Displays detailed information.
            Default is `True`.
        """
        self._preprocess_design_response_trend(design, response, trend)

        if self.response.shape[1] != 1:
            raise RuntimeError("ScalarGaSP only works for scalar-output model")

        with self._nostdout() if not verbose else nullcontext():
            self.emulator = RobustGaSP.rgasp(
                design=self.design,
                response=self.response,
                trend=self.trend,
                nugget=self.nugget,
                method=self.method,
                prior_choice=self.prior_choice,
                a=self.a,
                b=self._b,
                kernel_type=self.kernel_type,
                isotropic=self.isotropic,
                optimization=self.optimization,
                alpha=self.alpha,
                lower_bound=self.lower_bound,
                max_eval=self.max_eval,
                num_initial_values=self.num_initial_values,
            )

    @beartype
    def predict(
        self, testing_input: np.ndarray, testing_trend: Union[np.ndarray, None] = None
    ) -> np.ndarray:
        """
        Make prediction using the trained scalar GP emulator.

        Parameters
        ----------
        testing_input : numpy array
            Input points at which to make prediction. Shape :code:`(ntest, ndim)`.
            ``ntest`` is the number of input points and ``ndim`` is the
            input dimension. If :math:`ndim=1`, both :code:`(ntest, 1)` and
            :code:`(ntest,)` :class:`numpy.ndarray` are valid.
        testing_trend : numpy array, optional
            Basis function matrix corresponds to ``testing_input``.
            Shape :code:`(ntest, q)`. By default :code:`(ntest, 1)` matrix of ones.
            If :math:`q=1`, both :code:`(ntest, 1)` and :code:`(ntest,)`
            :class:`numpy.ndarray` are valid.

        Returns
        -------
        predictions : numpy array
            Emulator-prediction at ``testing_input``. Shape :code:`(ntest, 4)`.
            `predictions[:, 0]` - mean,
            `predictions[:, 1]` - low95,
            `predictions[:, 2]` - upper95,
            `predictions[:, 3]` - sd
        """
        if self.emulator is None:
            raise RuntimeError("Emulator has not been trained!")

        self._preprocess_testing_input_trend(testing_input, testing_trend)

        r_predictions = RobustGaSP.predict_rgasp(
            self.emulator,
            self.testing_input,
            testing_trend=self.testing_trend,
            interval_data=True,
            outasS3=True,
        )
        predictions = np.transpose(np.array(r_predictions))

        return predictions

    @beartype
    def sample(
        self,
        testing_input: np.ndarray,
        nsamples: int = 1,
        testing_trend: Union[np.ndarray, None] = None,
    ) -> np.ndarray:
        """
        Draw samples using the trained scalar GP emulator.

        Parameters
        ----------
        testing_input : numpy array
            Input points at which to draw samples. Shape :code:`(ntest, ndim)`.
            ``ntest`` is the number of input points and ``ndim`` is the input
            dimension. If :math:`ndim=1`, both :code:`(ntest, 1)` and
            :code:`(ntest,)` :class:`numpy.ndarray` are valid.
        nsamples : int, optional
            Number of samples to be drawn.
        testing_trend : numpy array, optional
            Basis function matrix corresponds to ``testing_input``.
            Shape :code:`(ntest, q)`. By default :code:`(ntest, 1)` matrix of ones.
            If :math:`q=1`, both :code:`(ntest, 1)` and :code:`(ntest,)`
            :class:`numpy.ndarray` are valid.

        Returns
        -------
        samples : numpy array
            Shape :code:`(ntest, nsamples)`. Each column contains one realization
            of the trained emulator at ``testing_input``.
        """
        if self.emulator is None:
            raise RuntimeError("Emulator has not been trained!")

        self._preprocess_testing_input_trend(testing_input, testing_trend)

        r_samples = RobustGaSP.Sample(
            self.emulator,
            self.testing_input,
            num_sample=nsamples,
            testing_trend=self.testing_trend,
        )
        samples = np.array(r_samples)

        return samples

    def loo_validate(self):
        """
        Validate trained scalar GP emulator using leave-one-out-cross-validation.

        Returns
        -------
        validation : numpy array
            Shape :code:`(n, 2)`.
            validation[:, 0] - leave-one-out fitted values
            validation[:, 1] - standard deviation of each prediction
        """
        if self.emulator is None:
            raise RuntimeError("Emulator has not been trained!")

        r_validation = RobustGaSP.leave_one_out_rgasp(self.emulator)
        validation = np.transpose(np.array(r_validation))

        return validation
    
    @beartype
    def repeated_kfold_validate(self, k: int = 5, repeat: int = 10) -> dict:
        """
        Performs repeated K-Fold cross-validation on trained emulator. Calculates
        MAPE, NRMSE, and R^2 errors.

        Parameters
        ----------
            k : int, optional
                K-factor. Default is :math:`5`.
            repeat : int, optiona
                Repeat-factor. Default is :math:`10`.

        Returns
        -------
            validation_dict : dict
                A dictionary consists of key-value pairs of error metrics (MAPE, 
                NRMSE, and R^2) and numpy array of respective error per validation
                step.
        """
        if self.emulator is None:
            raise RuntimeError("Emulator has not been trained!")
        
        X = self.design
        y = self.response

        rkf = RepeatedKFold(n_splits=k, n_repeats=repeat)
        nval = rkf.get_n_splits() 

        MAPE = np.empty(nval)           # mean absolute percentage
        R_squared = np.empty(nval)      # coefficient of determination
        NRMSE = np.empty(nval)          # normalized root mean square

        for i, (train_index, test_index) in enumerate(rkf.split(X)):
            training_inputs = X[train_index, :]
            training_outputs = y[train_index]
            testing_inputs = X[test_index, :]
            testing_outputs = y[test_index]

            self.train(training_inputs, training_outputs, verbose=False)
            prediction = self.predict(testing_inputs)[:, 0]

            R_squared[i] = None
            if len(prediction) > 1:
                R_squared[i] = r2_score(testing_outputs, prediction)

            MAPE[i] = 100 * mean_absolute_percentage_error(testing_outputs, prediction)

            RMSD = root_mean_squared_error(testing_outputs, prediction)
            mean = np.mean(testing_outputs)

            if abs(mean) < sys.float_info.epsilon:
                NRMSE[i] = None
            else:
                NRMSE[i] =  RMSD / mean

        validation_dict = {"MAPE": MAPE, "NRMSE": NRMSE, "R_squared": R_squared}
        return validation_dict


class PPGaSP(RobustGaSPBase):
    @beartype
    def train(
        self,
        design: np.ndarray,
        response: np.ndarray,
        trend: Union[np.ndarray, None] = None,
    ) -> None:
        """
        Train a parallel partial GP given training data.

        Parameters
        ----------
        design : numpy array
            Training input points. Shape :code:`(ntrain, ndim)`.
            ``ntrain`` is the number of training points, ``ndim`` is the input
            dimension. If :math:`ndim=1`, both :code:`(ndim, 1)` and
            :code:`(ndim,)` :class:`numpy.ndarray` are valid.
        response : numpy array
            Training output points. Shape :code:`(ntrain, nresponse)`,
            :math:`nresponse>1`.
        trend : numpy array, optional
            Basis function matrix. Shape :code:`(ntrain, q)`.
            If `None`, a :code:`(ntrain, 1)` matrix of ones is used.
            If :math:`q=1`, both :code:`(ntrain, 1)` and :code:`(ntrain,)`
            :class:`numpy.ndarray` are valid.
        """
        self._preprocess_design_response_trend(design, response, trend)

        if self.response.shape[1] == 1:
            raise RuntimeError(
                "PPGaSP should be used for models with vector output."
                " For scalar output model, please use ScalarGaSP."
            )

        self.emulator = RobustGaSP.ppgasp(
            design=self.design,
            response=self.response,
            trend=self.trend,
            zero_mean=self.zero_mean,
            nugget=self.nugget,
            nugget_est=self.nugget_est,
            range_par=self.range_par,
            method=self.method,
            prior_choice=self.prior_choice,
            a=self.a,
            b=self._b,
            kernel_type=self.kernel_type,
            isotropic=self.isotropic,
            optimization=self.optimization,
            alpha=self.alpha,
            lower_bound=self.lower_bound,
            max_eval=self.max_eval,
            num_initial_values=self.num_initial_values,
        )

    @beartype
    def predict(
        self, testing_input: np.ndarray, testing_trend: Union[np.ndarray, None] = None
    ) -> np.ndarray:
        """
        Make prediction using the trained parallel partial GP emulator.

        Parameters
        ----------
        testing_input : numpy array
            Input points at which to make prediction. Shape :code:`(ntest, ndim)`.
            ``ntest`` is the number of input points and ``ndim`` is the input
            dimension. If :math:`ndim=1`, both :code:`(ntest, 1)` and
            :code:`(ntest,)` :class:`numpy.ndarray` are valid.
        testing_trend : numpy array, optional
            Basis function matrix corresponds to ``testing_input``.
            Shape :code:`(ntest, q)`. By default :code:`(ntest, 1)` matrix of ones.
            If :math:`q=1`, both :code:`(ntest, 1)` and :code:`(ntest,)`
            :class:`numpy.ndarray` are valid.

        Returns
        -------
        predictions : numpy array
            Emulator-prediction at ``testing_input``.
            Shape :code:`(ntest, nresponse, 4)`.
            `predictions[:, :, 0]` - mean,
            `predictions[:, :, 1]` - low95,
            `predictions[:, :, 2]` - upper95,
            `predictions[:, :, 3]` - sd
        """
        if self.emulator is None:
            raise RuntimeError("Emulator has not been trained!")

        self._preprocess_testing_input_trend(testing_input, testing_trend)

        r_predictions = RobustGaSP.predict_ppgasp(
            self.emulator,
            self.testing_input,
            testing_trend=self.testing_trend,
            interval_data=True,
            outasS3=True,
        )

        ntest = self.testing_input.shape[0]
        nresponse = self.response.shape[1]

        predictions = np.zeros((ntest, nresponse, 4))
        for i in range(4):
            predictions[:, :, i] = np.array(r_predictions[i])

        return predictions

    @beartype
    def sample(
        self,
        testing_input: np.ndarray,
        nsamples: int = 1,
        testing_trend: Union[np.ndarray, None] = None,
    ) -> np.ndarray:
        """
        Draw samples using the trained parallel partial GaSP emulator.

        Parameters
        ----------
        testing_input : numpy array
            Input point at which to draw samples. Shape :code:`(ntest, ndim)`.
            ``ntest`` is the number of input points and ``ndim`` is the input
            dimension. If :math:`ndim=1`, both :code:`(ntest, 1)` and
            :code:`(ntest,)` :class:`numpy.ndarray` are valid.
        nsamples : int, optional
            Number of samples to be drawn.
        testing_trend : numpy array, optional
            Basis function matrix corresponds to ``testing_input``.
            Shape :code:`(ntest, q)`. By default :code:`(ntest, 1)` matrix of ones.
            If :math:`q=1`, both :code:`(ntest, 1)` and :code:`(ntest,)`
            :class:`numpy.ndarray` are valid.

        Returns
        -------
        samples : numpy array
            Shape :code:`(ntest, nresponse, nsamples)`.
            `samples[:, :, i]` corresponds to i-th realization of the trained
            emulator at ``testing_input``, i=1, ..., ``nsamples``.
        """
        if self.emulator is None:
            raise RuntimeError("Emulator has not been trained!")

        self._preprocess_testing_input_trend(testing_input, testing_trend)

        ntest = self.testing_input.shape[0]
        nresponse = self.response.shape[1]

        # extract trained parameters of ppgasp_emulator
        sigma2_hat = r_at(self.emulator, "sigma2_hat")
        nugget = r_at(self.emulator, "nugget")[0]
        beta_hat = r_at(self.emulator, "beta_hat")
        range_par = 1 / beta_hat

        # set up a rgasp_emulator using trained parameters of ppgasp_emulator
        rgasp_emulator = RobustGaSP.rgasp(
            design=self.design,
            response=self.response[:, 0],
            trend=self.trend,
            zero_mean=self.zero_mean,
            nugget=nugget,
            nugget_est=False,
            range_par=range_par,
            method=self.method,
            prior_choice=self.prior_choice,
            a=self.a,
            b=self._b,
            kernel_type=self.kernel_type,
            isotropic=self.isotropic,
            optimization=self.optimization,
            alpha=self.alpha,
            lower_bound=self.lower_bound,
            max_eval=self.max_eval,
            num_initial_values=self.num_initial_values,
        )

        # predictions and samples of y1 at testing_input using rgasp_emulator
        r_predictions_y1 = RobustGaSP.predict_rgasp(
            rgasp_emulator, self.testing_input, testing_trend=self.testing_trend
        )
        predictions_y1 = np.transpose(np.array(r_predictions_y1))
        predictions_mean_y1 = np.reshape(predictions_y1[:, 0], (ntest, 1))

        r_samples_y1 = RobustGaSP.Sample(
            rgasp_emulator,
            self.testing_input,
            num_sample=nsamples,
            testing_trend=self.testing_trend,
        )
        samples_y1 = np.array(r_samples_y1)

        # use predictions_mean and samples of y1 to calculate LW term
        LW_term = (samples_y1 - predictions_mean_y1) / np.sqrt(sigma2_hat[0])

        # predictions of y1,...,yk using ppgasp_emulator
        predictions = self.predict(self.testing_input, self.testing_trend)
        predictions_mean = predictions[:, :, 0]

        samples = np.zeros((ntest, nresponse, nsamples))
        for i in range(nresponse):
            samples[:, i, :] = (
                np.reshape(predictions_mean[:, i], (ntest, 1))
                + np.sqrt(sigma2_hat[i]) * LW_term
            )

        return samples
