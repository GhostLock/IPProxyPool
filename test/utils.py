import pymysql
import csv
import os
import threading
from threading import RLock


def first_list_data(list, default=""):
    """
    从list中获取第一个元素，如果list为空，就输出默认值
    """
    return next(iter(list), default)


def db_insert_data(db_name, sql, **kwargs):
    db = pymysql.connect("localhost", "root", "123456", db_name, **kwargs)
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except Exception as e:
        print(e)
    finally:
        db.close()


def __dict_to_csv(file_path, dict):
    file_exists = os.path.exists(file_path)
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        if not file_exists:
            csv.writer(f).writerow(dict.keys())
        csv.writer(f).writerow(dict.values())


def dict_to_csv(file_path, dict, lock=None):
    """传递一个dict，写入到csv文件中，支持传入线程锁"""
    import _thread
    if lock:
        if isinstance(lock,_thread.RLock):
            with lock:
                __dict_to_csv(file_path, dict)
        else:
            raise Exception("Expect threading.Rlock,got {}".format(type(lock)))
    else:
        __dict_to_csv(file_path, dict)


class CsvWorker(threading.Thread):
    def __init__(self,work_queue,file_path,lock=None):
        super().__init__()
        self.work_queue = work_queue
        self.file_path = file_path
        self.lock = lock
        self.daemon = True

    def run(self):
        print("CsvWorker running...")
        while True:
            data = self.work_queue.get()
            dict_to_csv(self.file_path, data, self.lock)
            self.work_queue.task_done()
