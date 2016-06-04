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

# =================Queue================================================

# question's url ,which format is '/question/id'. eg '/question/12345678'
#g_question_queue = Queue.Queue()

# {'user_name':blabla, 'img_urls':[]}
#g_img_queue = Queue.Queue()


# 'user_url' which format is '/people/username'. eg. '/people/anonymous'
#g_user_queue = Queue.Queue()

# [answer_url, comment_count] answeri_url format is '\d{8}'. eg. 44370648  comment_count is int
#g_answer_comment_queue = Queue.Queue()



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

# =================switch signal==========================================

g_question_exit = False
g_retrieve_exit = False
g_usr_exit = False
g_comment_exit = False
g_exit_quest_index = 0


# database
g_mysql_params = {}
g_zhihu_database = None
g_fail_url = None

sys_ = platform.system()

# path and folder
g_config_folder = os.getcwd() + '/config/'     #default value
g_storage_path = os.getcwd()                   #default value                 
