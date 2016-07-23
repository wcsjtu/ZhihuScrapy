# -*- coding: utf-8 -*-

import Queue
import multiprocessing
import datetime
import platform
import os
# =================HttpClient==============
g_zhihu_host = 'https://www.zhihu.com'
g_http_client = None
g_zhihu_account = {}


# =================data Queue================================================
#  data queue
# instance of user, question, answer, or comment
g_data_queue = multiprocessing.Queue()

# =================url Queue================================================
#url queue, format is [method, url, payloads, headers]
g_url_queue = multiprocessing.Queue()

#[urls, headers, storepath]
g_static_rc = multiprocessing.Queue()

#[html, method, url, payloads, headers]
g_html_queue = multiprocessing.Queue()


# database
g_mysql_params = {}
g_zhihu_database = None
g_fail_url = None

sys_ = platform.system()

# path and folder
g_config_folder = os.getcwd() + '/config/'     #default value
g_storage_path = None                   #default value                 



#=======================framework attributes==================
g_dbtable = []
