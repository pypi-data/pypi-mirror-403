from pilot.job.impl.base_job import BaseJob

from pilot.conver.converfileEncodding import nkf_convert


class EncodingTransformerJob(BaseJob):
    def run(self):
        nkf_args = ['-w', '--overwrite']
        nkf_convert(self.file_path, nkf_args)
        super().run()