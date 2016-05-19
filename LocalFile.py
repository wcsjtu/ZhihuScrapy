# -*- coding: utf-8 -*-

import threading
import os
import Global as gl

download_img_queue = []



class LocalImg(threading.Thread):

    def __init__(self, path):
        threading.Thread.__init__(self)
        self.name = "ImgLoader"
        self.path = path

        self.setDaemon(True)
        self.start()

    def _load_img(self):

        for dirnames in os.walk(self.path):
            for dirname in  dirnames[1]:
                for _,_,filenames in os.walk(dirnames[0]+"\\"+dirname):
                    for filename in filenames:
                        if filename == "user.txt" or filename[-6:-4]=='xl': continue
                        download_img_queue.append("/people"+'/'+dirname+"/"+filename+'\n')
                               
    def run(self):

        self._load_img()

def saveini(**kwargs):
    """save user's configuration to .ini file"""

    if not os.path.exists(gl.g_config_folder):
        os.mkdir(folder)
    try:    
        with open(gl.g_config_folder+'config.ini', 'w') as cfg:
            for key in kwargs:
                cfg.write(key+'='+kwargs[key]+'\n')
                
    except Exception, e :
        print 'Fail to save configuration parameters to config.ini, reason: %s'%e
        
        
    
    
def loadini():
    """
    load configuration parameters from .ini file
    if all parameters are loaded successfully, this function will return configuration
    parameters in a dict, else just return empty dict {}
    """
    config = {}
    try:
        with open(gl.g_config_folder+'config.ini', 'r') as cfg:
            for line in cfg:
                [key, value] = line.split('=')
                config[key] = value[:-1] #kick the '\n' at the end of string `value`
        assert 'password' and 'remember_me' and 'img_folder' and 'email' or 'phone_num' in config   
    except Exception, e :
        print 'Fail to load configuartion parameters, please check config.ini'
        config = {}
        
    finally:
        return config