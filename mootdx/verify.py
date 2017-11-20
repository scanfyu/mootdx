# -*- coding: utf-8 -*-
import logging
import socket
import threading
import time

# import coloredlogs
from prettytable import PrettyTable
from pytdx.config.hosts import hq_hosts

logger = logging.getLogger(__name__)
# coloredlogs.install(level='DEBUG', logger=logger)

result = []
hosts = []

for x in hq_hosts[:-7]:
    hosts.append({'addr': x[1], 'port': x[2], 'time': 0, 'site': x[0]})

# 线程同步锁
lock = threading.Lock()


def synchronous(f):
    def call(*args, **kwargs):
        lock.acquire()

        try:
            return f(*args, **kwargs)
        finally:
            lock.release()

    return call


# 获取一个待验证行情
@synchronous
def get_hosts():
    global hosts

    if len(hosts) > 0:
        return hosts.pop()
    else:
        return ''


# 保存验证结果
@synchronous
def saveresult(proxy):
    global result

    if not (proxy in result):
        result.append(proxy)


# 线程函数
def verify():
    while 1:
        proxy = get_hosts()
        # 所有行情均已验证完毕
        if len(proxy) == 0:
            return

        # 验证行情的可用性
        # 创建一个TCP连接套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 设置10超时
        sock.settimeout(10)

        try:
            start = time.clock()

            # 连接行情服务器
            sock.connect((proxy['addr'], int(proxy['port'])))
            proxy['time'] = (time.clock() - start) * 1000
            sock.close()

            saveresult(proxy)

            logging.debug("%s:%s 验证通过，响应时间：%d ms." % (proxy['addr'], proxy['port'], proxy['time']))
        except Exception as e:
            logging.error("%s,%s 验证失败." % (proxy['addr'], proxy['port']))


def check(limit=10, verbose=False, tofile=''):
    # init thread_pool
    thread_pool = []

    for i in range(20):
        th = threading.Thread(target=verify, args=())
        thread_pool.append(th)

    # start threads one by one
    for thread in thread_pool:
        thread.start()

    # collect all threads
    for thread in thread_pool:
        threading.Thread.join(thread)

    # 结果按响应时间从小到大排序

    # result.sort(lambda x, y: cmp(x['time'], y['time']))
    result.sort(key=lambda x: (x['time']))

    print("最优服务器:")

    t = PrettyTable(["Name", "Addr", "Port", "Time"])
    t.align["Name"] = "l"  # Left align city names
    t.align["Addr"] = "l"  # Left align city names
    t.align["Port"] = "l"  # Left align city names
    t.align["Time"] = "r"  # Left align city names
    t.padding_width = 1  # One space between column edges and contents (default)

    for x in result[:int(limit)]:
        t.add_row([x['site'], x['addr'], x['port'], '%.2fms' % x['time']])

    print(t)

    # if tofile:
    #     import csv
    #     with open(tofile, 'wb') as csvfile:
    #         writer = csv.DictWriter(csvfile, fieldnames=result[0].keys())
    #         writer.writeheader()
    #         for item in result:
    #             writer.writerow(item)


if __name__ == '__main__':
    check()