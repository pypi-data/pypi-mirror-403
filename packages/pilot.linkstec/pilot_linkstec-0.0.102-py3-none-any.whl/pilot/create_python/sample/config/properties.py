import textwrap


class create_file():
    # 静的な文字列（詳細プロンプト）

    detail_prompt: str = textwrap.dedent("""\

work_space={{WORK_SPACE}}

project={{PROJECT_NAME}}
steps={{STEP_NAME}}
runsteps={{STEP_NAME}}
multisteps=
threads=1

```
    """).strip()
