import sys
import os
import re
import textwrap
import shutil
from datetime import datetime


__all__ = ['tmp2new', 'delete_tmp', "documenting", "log2donelog", "extract_logs_from_file"]


# @log: 함수 `tmp2new` 추가
def tmp2new(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if ".tmp" in file:
                new_file = file.split(".tmp")[0]
                # print(root, file, new_file)
                tmp = os.path.join(root, file)
                new = os.path.join(root, new_file)
                os.replace(tmp, new)
                print(f"{new} 저장되었습니다. (.tmp 삭제)")


# @log: 함수 `delete_tmp` 추가
def delete_tmp(path):
    string = textwrap.dedent(
        f"""
        .tmp 를 남기시겠습니까 삭제하시겠습니까?
        0: 남김, 1: 삭제
        """
    )
    # 결정
    while True:
        try:
            tmp_del = int(input(string))
            if tmp_del in [0, 1]:
                break
            else:
                print("0 또는 1 을 입력하십시오.")
        except Exception:
            print("0 또는 1 을 입력하십시오.")
    # 보존
    if tmp_del == 0:
        print('tmp 파일을 보존합니다.')
    # 삭제
    elif tmp_del == 1:
        for root, dirs, files in os.walk(path):
            for file in files:
                if ".tmp" in file:
                    tmp = os.path.join(root, file)
                    os.remove(tmp)
        print("생성된 모든 .tmp 파일을 삭제합니다.")


# @log: 기본적인 README 기록 형태를 제공하는 함수 `documenting` 추가
# @log: 함수 `documenting` 내부에 README.md.tmp 파일 생성 추가
# @log: 함수 `documenting` 에 덮어씌우기 인자 `overwrite` 추가
def documenting(tag, summary, version, log_contents, docs_path, docs_name="README.md", overwrite=False):
    now = datetime.now()

    log_entry = f'\n### {now.strftime("%Y-%m-%d")} Version {version}\n'
    log_entry += f"**tag:** @{tag}\n"
    log_entry += f"**Summary:** {summary}\n"
    log_entry += "**Detail:**\n"
    log_entry += log_contents

    if not isinstance(overwrite, bool):
        raise TypeError(f"overwrite must be boolean type.")

    # 기존 README.에 그대로 덮어씌울 경우
    if overwrite:
        string = textwrap.dedent(
            f"""
            ⚠️ 덮어씌우기 인자가 활성화 되어 .tmp 없이 기존 파일 {docs_name} 에 바로 변경이 적용됩니다. 진행하시겠습니까?
            0:미진행 1:진행
            """
        ).strip()
        do = input(string)
        if do == "1":
            with open(os.path.join(docs_path, f"{docs_name}.tmp"), "a", encoding="utf-8") as f:
                f.write("\n\n" + log_entry)
    # .tmp 파일 생성
    else:
        try:
            shutil.copy2(
                os.path.join(docs_path, f"{docs_name}"),
                os.path.join(docs_path, f"{docs_name}.tmp")
            )
            with open(os.path.join(docs_path, f"{docs_name}.tmp"), "a", encoding="utf-8") as f:
                f.write("\n\n" + log_entry)
        except FileNotFoundError:
            with open(os.path.join(docs_path, f"{docs_name}.tmp"), "w", encoding="utf-8") as f:
                f.write("\n\n" + log_entry)
        return log_entry


# @log: 함수 `log2donelog` 에서 version 변수에 대한 입력 여부 결정 추가
def log2donelog(file_path, version=None):
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 문구 교체 (@log -> [version] @done_log)
        pattern = r"#" + r" @log:"
        if version is not None:
            new_content = re.sub(pattern, f"# [{version}] @done_log:", content)
        else:
            new_content = re.sub(pattern, f"# @done_log:", content)

        # 4. 파일 다시 저장
        with open(f"{file_path}.tmp", 'w', encoding='utf-8') as f:
            f.write(new_content)
    except IsADirectoryError:
        pass


def extract_logs_from_file(file_path):
    """
    파일 내부 주석 중 에서 @log: 로 시작하는 주석 문구를 추출합니다.
    """
    logs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 주석 중에서 @log: 로 시작하는 부분의 문구 추출
                pattern = r"#" + r" @log:\s*([^\"\n]*)"
                match = re.search(pattern, line)
                if match:
                    log_msg = match.group(1).strip()
                    if log_msg:
                        logs.append(log_msg)
    except Exception as e:
        pass
    
    return logs