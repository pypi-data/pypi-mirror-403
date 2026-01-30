import sys
import os
sys.path.append('/home/kimyh/library/logie')
import logie as lo


def main():
    log_path = os.getcwd()
    lo.log_del(
        log_path=os.path.join(log_path, 'log'),
        days=30
    )
    # log = lo.get_logger(
    #     console_display=True
    # )
    # log.info('아메리카노 마시고 싶다.')
    # log.error('이건 에러 문구가 나올지도 모른다.')
    # pass


def main1():
    import logie as lo

    file_path = "/home/kimyh/library/logie/logie/logutils/sourceutils.py"
    # source_log_list = lo.extract_logs_from_file(file_path)
    change_log = ""
    # for source_log in source_log_list:
    #     change_log += f" - {source_log}\n"
    # lo.log2donelog(file_path)
    a = lo.documenting(
        tag="태그", 
        summary="테스트", 
        version="0.1.1", 
        log_contents=change_log,
        docs_path=os.path.dirname(os.path.abspath(__file__)),
        overwrite=True
    )
    print(a)
    lo.delete_tmp("/home/kimyh/library/logie/logie/logutils")
    

if __name__ == '__main__':
    main1()
    