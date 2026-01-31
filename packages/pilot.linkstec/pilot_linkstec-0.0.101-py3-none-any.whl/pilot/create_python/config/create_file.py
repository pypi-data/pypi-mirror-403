import textwrap


class create_file():
    # 静的な文字列（詳細プロンプト）

    detail_prompt: str = textwrap.dedent("""\
    
work_space=C:/workspace/lsc_sci/plsql_detail

sub_project_name=common
sub_source_folder=clearner
sub_sub_source_folder_1=cobol


```
    """).strip()
