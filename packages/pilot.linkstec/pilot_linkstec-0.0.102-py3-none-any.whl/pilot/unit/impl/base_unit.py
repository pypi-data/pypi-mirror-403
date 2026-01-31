import os

from pilot.unit.unit_interface import UnitInterface
from pilot.job.impl.base_job import BaseJob
from pilot.config.config_reader import ConfigReader, ConfigDTO  # 追加

class BaseUnit(UnitInterface):
    config_dto: ConfigDTO = None  # 型アノテーションを追加
    joblist = []

    def __init__(self):
        pass

    def _init_job(self,step):
        return BaseJob()

    def run(self, index=0):
        steps = self.config_dto.steps
        step = steps[index]
        current_step_dir = self.config_dto.work_space + "/" + step
        self._run_jobs_in_step_dir(current_step_dir, step, index)

    def _run_jobs_in_step_dir(self, current_step_dir, step, index):
        for dirpath, _, filenames in os.walk(current_step_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                job = self._init_job(step)
                job.config_dto = self.config_dto
                job.current_step = step
                job.step_index = index
                job.file_path = file_path
                if self.job_need_run(job, filename, index):
                    if index != 0:
                        if not job.pre_run():
                            continue
                    job.run()
                    if index != 0:
                        job.post_run()

    def job_need_run(self, job:BaseJob ,filename: str, step_index: int):
        if step_index == 0:
            return True
        file_ext =  file_ext = filename.split('.')[-1]
        if file_ext == "trg":
            # ★ trgファイルは、jobのfile_pathに設定する
            job.current_trg_file_path = job.file_path
            job.file_path = job.file_path.rsplit('.trg', 1)[0]
            return True
        elif file_ext == "end":
            #job.copy_input_file_to_next_step(job.file_path.rsplit('.', 1)[0])
            #job.create_next_step_end_trg_file()
            return False
        elif file_ext  == "begin":
            return False
        else:
            return False