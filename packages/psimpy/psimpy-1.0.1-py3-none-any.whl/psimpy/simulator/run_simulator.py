import os
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from beartype.typing import Callable
from beartype import beartype
from typing import Union

class RunSimulator:

    @beartype
    def __init__(
        self, simulator: Callable, var_inp_parameter: list[str], 
        fix_inp: Union[dict, None] = None,
        o_parameter: Union[str, None] = None, dir_out: Union[str, None] = None,
        save_out: bool = False) -> None:
        """
        Serial or parallel execution of a given simulator.

        Parameters
        ----------
        simulator : Callable
            A Python function defining the simulator. Its parameters are defined
            in three parts:
            ``var_inp_parameter`` defines variable parameters;
            ``fix_inp`` defines fixed parameters (``fix_inp.keys()``) and their
            values (``fix_inp.values()``);
            ``o_parameter`` defines an additional variable which is used to
            name files saved onto the disk within the function body of
            ``simulator``.
            The simulator should return outputs of interest as 
            :class:`numpy.ndarray`.
        var_inp_parameter :  list of str
            A list consists of all variable input parameters of ``simulator``.
        fix_inp : dict, optional
            A dictionary consists of key-value pairs of all fixed input of the
            ``simulator``.
        o_parameter : str, optional
            Keyword parameter of ``simulator`` which is used to name internally
            saved files (if defined). It is only relevant if the function body
            of ``simulator`` saves data onto the disk.  
        dir_out : str, optional
            Directory to save outputs of interest returned by ``simulator``.
        save_out : bool, optional
            Whether to save returned values of ``simulator``. If `True`,
            ``dir_out`` must be given. 
        """
        self.simulator = simulator
        self.var_inp_parameter = var_inp_parameter
        self.fix_inp = {} if fix_inp is None else fix_inp
        self.o_parameter = o_parameter

        if save_out:
            if dir_out is None:
                raise ValueError(
                    "dir_out must be defined if save_out is True")
            elif not os.path.isdir(dir_out):
                raise ValueError(
                    f"{dir_out} does not exist or is not a directory") 
        self.dir_out = dir_out
        self.save_out = save_out
        
        self.var_samples: np.ndarray = np.array([])
        """Samples of variable input parameters."""
        self.outputs: list = []
        """Simulation outputs."""

    @beartype
    def serial_run(
        self, var_samples: np.ndarray, prefixes: Union[list[str], None] = None,
        append: bool = False) -> None:
        """
        Perform serial execution of ``simulator`` at a set of ``var_samples``.

        Parameters
        ----------
        var_samples : numpy array
            Samples of variable input parameters. The first axis
            (:code:`var_samples.shape[0]`) corresponds to the number of samples.
            The second axis (:code:`var_samples.shape[1]`) corresponds to the
            number of variable input parameters. 
        prefixes :  list of str, optional
            Contains :code:`len(var_samples)` prefixes. Each of them is used to
            name corresponding simulation output file. 
        append : bool, optional
            If `True`, append ``var_samples`` to existing samples and
            correspondingly append simulation outputs.
        """
        num_pre_run, num_new_run, kwargs_num_new_run, prefixes = \
            self._preprocess(var_samples, prefixes, append)
        
        for i in range(num_new_run):
            kwargs = kwargs_num_new_run[i]

            try:
                output = self.simulator(**kwargs)
                self.outputs.append(output)
                
                if self.save_out:
                    fname = f"{prefixes[i]}_output.npy"
                    np.save(os.path.join(self.dir_out, fname), output)

            except Exception as e:
                print(f"Exception occurred in simulation {prefixes[i]}."
                      f"The error message is: {str(e)}")
                self.outputs.append(str(e))
            
    @beartype
    def parallel_run(
        self, var_samples: np.ndarray, prefixes: Union[list[str], None] = None,
        append: bool = False, max_workers: Union[int, None] = None) -> None:
        """
        Perform parallel execution of ``simulator`` at a set of ``var_samples``.

        Parameters
        ----------
        var_samples : numpy array
            Samples of variable input parameters. The first axis
            (:code:`var_samples.shape[0]`) corresponds to the number of samples.
            The second axis (:code:`var_samples.shape[1]`) corresponds to the
            number of variable input parameters.
        prefixes :  list of str, optional
            Contains :code:`len(var_samples)` prefixes. Each of them is used to
            name corresponding simulation output file.
        append : bool, optional
            If `True`, append ``var_samples`` to existing samples and
            correspondingly append simulation outputs.
        max_workers : int, optional
            Controls the maximum number of tasks running in parallel.
            Default is the number of CPUs on the host.        
        """
        num_pre_run, num_new_run, kwargs_num_new_run, prefixes = \
            self._preprocess(var_samples, prefixes, append)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.simulator, **kwargs)
                       for kwargs in kwargs_num_new_run]
            for i in range(num_new_run):
                try:
                    output = futures[i].result()
                    self.outputs.append(output)

                    if self.save_out:
                        fname = f"{prefixes[i]}_output.npy"
                        np.save(os.path.join(self.dir_out, fname), output)

                except Exception as e:
                    print(f"Exception occurred in simulation {prefixes[i]}."
                          f"The error message is: {str(e)}")
                    self.outputs.append(str(e))
    

    def _preprocess(self, var_samples: np.ndarray, prefixes: list[str],
        append: bool) -> tuple[int, int, list[dict], list[str]]:
        """
        Preprocess inputs for :meth:`.serial_run` and :meth:`parallel_run`.

        Parameters
        ----------
        var_samples : numpy array
            Samples of variable input parameters. The first axis
            (:code:`var_samples.shape[0]`) corresponds to the number of samples.
            The second axis (:code:`var_samples.shape[1]`) corresponds to the
            number of variable input parameters.
        prefixes :  list of str, optional
            Contains :code:`len(var_samples)` prefixes. Each of them is used to
            name corresponding simulation output file.
        append : bool
            If `True`, append ``var_samples`` to existing samples and
            correspondingly append simulation outputs.

        Returns
        -------
        num_pre_run : int
            Number of existing runs.
        num_new_run : int
            Number of new runs. 
        kwargs_num_new_run: list
            Contains ``num_new_run`` dictionaries, each of which corresponds to 
            ``kwargs`` of one simulation.     
        prefixes : list of str
        """
        if var_samples.ndim == 0 or var_samples.ndim == 1:
            var_samples = np.reshape(var_samples, (1, -1))           

        if var_samples.shape[1] != len(self.var_inp_parameter):
            raise ValueError(
                "var_samples should have the same number of" 
                " variable inputs as defined by var_input_parameter")
        
        num_new_run = len(var_samples)
        
        if not append:
            num_pre_run = 0
            self.outputs = []
            self.var_samples = var_samples
        else:
            num_pre_run = len(self.var_samples)
            if num_pre_run == 0:
                raise ValueError(
                    "append is True but no previous var_samples exist")
            else:
                self.var_samples = np.vstack((self.var_samples, var_samples))
        
        if prefixes is None:
            prefixes = [f'sim{i+num_pre_run}' for i in range(num_new_run)]
        elif len(prefixes) != num_new_run:
            raise ValueError(
                "prefixes should have same number of items as var_samples")
        elif len(set(prefixes)) != num_new_run:
            raise ValueError("Each element of prefixes should be unique")

        if self.save_out:
            new_filenames = \
                [f'{prefixes[i]}_output.npy' for i in range(num_new_run)]
            exist_filenames = os.listdir(self.dir_out)
            common_filenames = set(new_filenames).intersection(exist_filenames)
            
            if len(common_filenames) != 0:
                raise ValueError(
                    f"{self.dir_out} contains files named with prefixes. "
                    f"Please move or delete the files before starting runs, "
                    f"or provide different prefixes.")
        
        kwargs_num_new_run = []
        for i in range(num_new_run):
            
            var_sample = self.var_samples[i+num_pre_run]
            kwargs = {self.var_inp_parameter[j]: var_sample[j] 
                for j in range(len(var_sample))}
            
            kwargs.update(self.fix_inp)

            if self.o_parameter is not None:
                kwargs.update({f'{self.o_parameter}': f'{prefixes[i]}'})
            
            kwargs_num_new_run.append(kwargs)

        return num_pre_run, num_new_run, kwargs_num_new_run, prefixes