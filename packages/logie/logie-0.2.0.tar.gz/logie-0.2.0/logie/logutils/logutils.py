import sys
import os
import shutil
from datetime import datetime, timedelta

import logging
from logging import handlers

import warnings
warnings.filterwarnings('ignore')

__all__ = ['get_logger', 'log_sort', 'log_del']


# 커스텀 필터: INFO 이하만 통과
class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level):
        self.max_level = max_level
    def filter(self, record):
        return record.levelno <= self.max_level
    

def get_logger(log_id, log_path=None, log_name='app', display=True, rollover=True):#, console_display=False, logging_level='info'):

    if log_path is None:
        log_path = os.path.join(os.getcwd(), 'log')
    
    # 로그 저장 경로 생성
    os.makedirs(log_path, exist_ok=True)

    # 경로
    file_h_path = os.path.join(log_path, f'{log_name}.log')
    info_h_path = os.path.join(log_path, 'info.log')
    error_h_path = os.path.join(log_path, 'error.log')

    '''
    로그 수준 정도(낮은 순)
    logging.NOTSET
    logging.DEBUG
    logging.INFO
    logging.WARNING
    logging.ERROR
    logging.CRITICAL
    '''

    # 로거 생성
    logger = logging.getLogger(log_id)

    # # 기존 핸들러 다 제거
    # for h in logger.handlers[:]:
    #     logger.removeHandler(h)

    # 로거 전체 기준 수준 설정
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # 파일 핸들러 설정
        if rollover:
            file_handler = handlers.TimedRotatingFileHandler(
                filename=file_h_path,
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8")
            file_handler.suffix = '%Y%m%d'

            info_handler = handlers.TimedRotatingFileHandler(
                filename=info_h_path,
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8")
            info_handler.suffix = '%Y%m%d'

            error_handler = handlers.TimedRotatingFileHandler(
                filename=error_h_path,
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8")
            error_handler.suffix = '%Y%m%d'
        else:
            file_handler = logging.FileHandler(file_h_path)
            info_handler = logging.FileHandler(info_h_path)
            error_handler = logging.FileHandler(error_h_path)
        
        # 핸들러 수준 설정
        file_handler.setLevel(logging.INFO)

        info_handler.setLevel(logging.INFO)
        info_handler.addFilter(MaxLevelFilter(logging.INFO))    # info 수준만 기록
        
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(MaxLevelFilter(logging.ERROR))  # error 수준만 기록

        # formatter 설정
        formatter = logging.Formatter('%(asctime)s level:%(levelname)s %(filename)s line %(lineno)d %(message)s')
        if display:
            console_fomatter = logging.Formatter('%(message)s')
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(console_fomatter)
            logger.addHandler(stream_handler)

        # 핸들러에 formatter 연결
        file_handler.setFormatter(formatter)
        info_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)

        # 로거에 핸들러 추가
        logger.addHandler(file_handler)
        logger.addHandler(info_handler)
        logger.addHandler(error_handler)

    # 같은 핸들러 인스턴스에 여러 로거를 추가하는 것은 추후 추가
    return logger


def log_sort(log_path=None):
    if log_path is None:
        log_path = os.path.join(os.getcwd(), 'log')

    os.makedirs(f'{log_path}_history', exist_ok=True)
    log_file_list = os.listdir(log_path)
    log_file_list.sort()

    log_dict = {}
    for log_file in log_file_list:
        log_name = log_file.split('.')[0]
        date = log_file.split('.')[-1]
        if date == 'log':
            continue
        try:
            log_dict[log_name].append(log_file)
        except KeyError:
            log_dict[log_name] = [log_file]

    
    for log_name, log_list in log_dict.items():
        for log_file in log_list:
            date = log_file.split('.')[-1]
            yyyy = date[:4]
            mm = date[4:6]
            # dd = date[6:]
            move_path = f'{log_path}_history/{yyyy}/{mm}/{log_name}'
            os.makedirs(move_path, exist_ok=True)
            shutil.move(
                f'{log_path}/{log_file}',
                f'{move_path}/{log_file}'
            )



def log_del(log_path=None, days=0):
    if log_path is None:
        log_path = os.path.join(os.getcwd(), 'log')
    log_file_list = os.listdir(log_path)
    log_file_list.sort()

    # 현재 날짜 int 값
    now = datetime.now()
    back = now - timedelta(days=days)
    back_str = str(back)
    date_ = back_str.split(' ')[0]
    date_int = int(date_.replace('-', ''))
    date_int = int(date_.replace('-', ''))
    print(f'{date_} 이전 log 삭제')
    for log_file in log_file_list:
        l_date_str = log_file.split('.')[-1]
        if l_date_str == 'log':
            continue
        l_date_int = int(l_date_str)

        if l_date_int < date_int:
            os.remove(os.path.join(log_path, log_file))
            print(f'{log_file} --> 삭제')
        

if __name__ == "__main__":
    root_path = ''
    log_sort(root_path)