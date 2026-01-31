from pathlib import Path

from pilot.job.impl.base_job import BaseJob

class TabReplaceJob(BaseJob):

    def run(self):
        self.replace_tabs_with_spaces()
        super().run()

    def replace_tabs_with_spaces(self, tab_width: int = 4):
        replaced_text =[]
        src_path = Path(self.file_path)
        spaces = ' ' * tab_width
        with open(self.file_path, 'r', encoding='utf-8', newline='') as rf:
            for line in rf:
                replaced_text.append(line.replace('\t', spaces))

        tmp_path = src_path.parent / (src_path.name + '.tmp')
        with open(tmp_path, 'w', encoding='utf-8', newline='') as wf:
            wf.writelines(replaced_text)

        tmp_path.replace(src_path)