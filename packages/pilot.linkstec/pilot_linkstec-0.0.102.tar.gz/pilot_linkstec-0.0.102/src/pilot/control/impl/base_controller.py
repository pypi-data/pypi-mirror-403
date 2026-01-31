import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor


from pilot.control.control_interface import ControlInterface
from pilot.unit.impl.base_unit import BaseUnit
from pilot.config.config_reader import ConfigReader


class BaseController(ControlInterface):

    config_dto = None

    def __init__(self):
        pass

    def _init_unit(self):
        return BaseUnit()

    def run(self,configfile: str = None):

        config_dto = ConfigReader(configfile).get_dto()
        unit = self._init_unit()
        unit.config_dto = config_dto

        steps = config_dto.steps
        runsteps = config_dto.runsteps

        def run_step(index):
            if index >= len(steps):
                return
            step = steps[index]
            if step in config_dto.skipsteps:
                run_step(index + 1)
                return

            if len(runsteps) == 0:
                pass
            elif len(runsteps) != 0 and step not in runsteps:
                run_step(index + 1)
                return

            max_workers = 1
            if step in config_dto.multisteps:
                max_workers = config_dto.threads

            def step_worker():
                unit.run(index)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for _ in range(max_workers):
                    futures.append(executor.submit(step_worker))
                    time.sleep(0.5)
                for future in futures:
                    future.result()
                run_step(index + 1)

        run_step(0)

    def copy_result_files_to_next_control(from_configfile: str,to_configfile: str ):
        from_config_dto = ConfigReader(from_configfile).get_dto()
        to_config_dto = ConfigReader(to_configfile).get_dto()
        from_runsteps = from_config_dto.steps
        to_runsteps = to_config_dto.steps
        from_workspace = from_config_dto.work_space
        to_workspace = to_config_dto.work_space
        from_fold = os.path.join(from_workspace, from_runsteps[-1])
        to_fold = os.path.join(to_workspace, to_runsteps[0])
        if os.path.exists(to_fold):
            shutil.rmtree(to_fold)
        os.makedirs(to_fold)
        shutil.rmtree(to_fold)
        os.makedirs(to_fold, exist_ok=True)
        shutil.copytree(from_fold, to_fold, dirs_exist_ok=True)
        for root, _, files in os.walk(to_fold):
            for fname in files:
                if fname.endswith(('.trg', '.begin', '.end')):
                    try:
                        os.remove(os.path.join(root, fname))
                    except OSError:
                        pass


    def copy_result_files_to_next_control_without_delete(from_configfile: str,to_configfile: str ):
        from_config_dto = ConfigReader(from_configfile).get_dto()
        to_config_dto = ConfigReader(to_configfile).get_dto()
        from_runsteps = from_config_dto.steps
        to_runsteps = to_config_dto.steps
        from_workspace = from_config_dto.work_space
        to_workspace = to_config_dto.work_space
        from_fold = os.path.join(from_workspace, from_runsteps[-1])
        to_fold = os.path.join(to_workspace, to_runsteps[0])
        os.makedirs(to_fold, exist_ok=True)
        shutil.copytree(from_fold, to_fold, dirs_exist_ok=True)
        for root, _, files in os.walk(to_fold):
            for fname in files:
                if fname.endswith(('.trg', '.begin', '.end')):
                    try:
                        os.remove(os.path.join(root, fname))
                    except OSError:
                        pass



