# -*- coding: utf-8 -*-

import Queue
import multiprocessing
import datetime
import platform
import os
# =================HttpClient==============
# instance of HttpClient
# ATTENTION: this variable must initiallize at global position
# ATTENTION: this variable must initiallize at global position
g_http_client = None


# =================data Queue======================================================
# this queue will be used to communicate between module Parser and DataBase
# its element is instance of subclass of StructData
g_data_queue = multiprocessing.Queue()

# =================Queue===========================================================
# all the queues below will be used to communicate between module Client and Parser
# its element is instance of SexTuple.HttpSextp
g_url_queue = multiprocessing.Queue()

# element is instance of SexTuple.HttpSrsc
g_static_rc = multiprocessing.Queue()

# element is instance of SexTuple.HttpSextp
g_html_queue = multiprocessing.Queue()
# =================================================================================


# ======================database===================================================
# this variable will used to store the parameters of mysql database
g_mysql_params = {}

# instance of class DataBase
# ATTENTION: this variable must initiallize at global position
# ATTENTION: this variable must initiallize at global position
g_database = None
# =================================================================================


# =================config and storage folder=======================================
# this variable defines the folder of saving config.ini file
g_config_folder = os.getcwd() + '/config/'     #default value

# this variable will used to specify where to store the static resource.
# MAKE SURE TARGET DISK HAS ENOUGH SPACE!!!
g_storage_path = None                               
# =================================================================================


#=======================framework attributes=======================================
# when classmethod Register in subclass of StructData called, the
# attribute _database_struct will be append to this variable
g_dbtable = []


# ==========================Exception Handle=======================================
# if occur http error, which exclude 404, or tcp error when visit cerntain url 
# with certain payloads, the url and payloads will be put in this variable.
# if `g_url_queue` and `g_html_queue` are empty, the httpclient will attempt to get
# element from this variable. 
# whether it would lead to endless loop, need to validate!!!
g_fail_url = multiprocessing.Queue()


# ==========================other=======================================
sys_ = platform.system()
