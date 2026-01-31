
from pilot.job.impl.base_job import BaseJob

class SpitPreDigit(BaseJob):
    def run(self):

        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        cleaned_lines = []
        for line in lines:
            # 先頭6文字を抽出
            prefix = line[:6]

            # 先頭6文字がすべて数字（かつ6文字以上ある）かチェック
            if len(prefix) == 6 and prefix.isdigit():
                # 数字だった場合は7文字目以降を保存
                cleaned_lines.append(line[6:])
            else:
                # 数字でない（または6文字未満）場合はそのまま保存
                cleaned_lines.append(line)

        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)


