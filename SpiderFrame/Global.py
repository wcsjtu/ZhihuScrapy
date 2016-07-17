# -*- coding: utf-8 -*-

import Queue
import multiprocessing
import datetime
import platform
import os
# =================HttpClient==============
g_http_client = None

# =================data Queue================================================
#  data queue
# instance of user, question, answer, or comment
g_data_queue = multiprocessing.Queue()

# =================url Queue================================================
#element is instance of SexTuple.HttpSextp
g_url_queue = multiprocessing.Queue()

#element is instance of SexTuple.HttpSrsc
g_static_rc = multiprocessing.Queue()

#element is instance of SexTuple.HttpSextp
g_html_queue = multiprocessing.Queue()


# database
g_mysql_params = {}
g_database = None
g_fail_url = None

sys_ = platform.system()

# path and folder
g_config_folder = os.getcwd() + '/config/'     #default value
g_storage_path = None                   #default value                 



#=======================framework attributes==================
g_dbtable = []
