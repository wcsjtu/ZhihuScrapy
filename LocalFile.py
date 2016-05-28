# -*- coding: utf-8 -*-

import threading
import os
import ConfigParser
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


class IniParser(object):
    """parse and storage configuration informations"""
    def __init__(self):
        
        self.cfg_parser = ConfigParser.ConfigParser()
        self.sects = {}
        self.load()

    def load(self):
        """
        load configuration parameters from .ini file        
        """
        try:
            self.cfg_parser.read(gl.g_config_folder+'config.ini')
            sec_names = self.cfg_parser.sections()
            for sec in sec_names:
                temp = {} 
                for item in self.cfg_parser.items(sec):
                    temp[str(item[0])] = item[1]
                self.sects[sec] = temp
        except IOError,e:
            print "config.ini is not existed in config folder!"
            self.sects = {}
                    
    def save(self):
        """"""
        if self.sects == {}:
            return
        if not os.path.exists(gl.g_config_folder):
            os.mkdir(gl.g_config_folder)

        for sec in self.sects:
            self.cfg_parser.add_section(sec)
            for key in self.sects[sec]:
                self.cfg_parser.set(sec, key, self.sects[sec][key])

        with open(gl.g_config_folder+"config.ini", 'w') as cfg:
            self.cfg_parser.write(cfg)
            


    def modify(self, sec, **kwargs):
        """
        modify configuration file
        @params: sec, string, name of section
                 **kwargs, dict. the attribution under modifying 
        """       
        self.sects[sec] = kwargs




