# -*- coding: utf-8 -*-

import DataBase
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append("..")

import Global as gl
import Config

Config.mysql_params()
gl.g_zhihu_database = DataBase.DataBase()

