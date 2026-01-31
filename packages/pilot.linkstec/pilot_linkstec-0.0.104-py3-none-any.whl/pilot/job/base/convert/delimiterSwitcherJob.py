from pathlib import Path

from pilot.job.impl.base_job import BaseJob

class DelimiterSwitcherJob(BaseJob):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.from_sep = ''
        self.to_sep = ''
        self.desc_file_path = None
        self.src_file_path = None

    def run(self):
        replaced_text = []
        if self.src_file_path is None:
            self.src_file_path = Path(self.file_path)
        with open(self.src_file_path, 'r', encoding='utf-8', newline='') as rf:
            for line in rf:
                replaced_text.append(line.replace(self.from_sep, self.to_sep))
        if self.desc_file_path is None:
            self.desc_file_path = Path(self.file_path)
        with open(self.desc_file_path, 'w', encoding='utf-8', newline='') as wf:
            wf.writelines(replaced_text)
        super().run()