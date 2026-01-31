import json
import os
import threading
import time

from pilot.job.impl.base_job import BaseJob

from pilot.generater.vertexai import VertexAISingleton

class GenerateTextBaseJob(BaseJob):

    prompt_content: str
    result_content: str
    result_file_path: str

    def run(self):
        #with self._begin_file_lock:
        #    if not self.change_current_trg_to_begin():
        #        return
        #prompt = self.get_file_content()
        prompt = self.prompt_content
        # トークン数チェック
        vertexai = VertexAISingleton.get_instance()
        token_count = vertexai.count_tokens(prompt)
        if token_count == 0:
            super().run()
            return
        if token_count > 900000:
            print(f"警告: promptのトークン数が900000を超えています ({token_count} tokens)")
            super().run()
            return
        # VertexAI で生成
        start = time.time()
        result = vertexai.generate_content(prompt)
        end = time.time()
        print(f"AI 処理時間 {self.file_path}: {end - start:.2f}秒")
        result_content = result.get('response', '')
        with open(self.result_file_path, 'w', encoding='utf-8') as f:
            f.write(result_content)
        super().run()