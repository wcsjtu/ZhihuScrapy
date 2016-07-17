# -*- coding: utf-8 -*-

import datetime
import logging
import logging.handlers
from SpiderFrame import Global as gl
#import Global as gl


def creatlogger(logger_name, logfile=None, log_level=logging.WARNING):  

    import os
    log_folder = os.getcwd()+'/LOG/'
    if not os.path.exists(log_folder):  
        os.mkdir(log_folder)

    logger = logging.getLogger(logger_name)
  
    LOG_FILENAME = logfile if logfile is not None else '%s%sLog.log'%(log_folder, logger_name)  
          
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,maxBytes=10*1024*1024,backupCount=5)  
  
    formatter = logging.Formatter('%(asctime)s %(module)s %(funcName)s[line:%(lineno)d] thread:%(threadName)s: %(message)s')  
  
    handler.setFormatter(formatter)      
  
    logger.addHandler(handler)  
  
    logger.setLevel(log_level)  
  
    return logger       

gl.g_fail_url = creatlogger('%s_FailURL'%datetime.datetime.now().strftime('%Y-%m-%d'))     
