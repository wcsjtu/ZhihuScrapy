# -*- coding: utf-8 -*-

import threading
import os
import ConfigParser
from SpiderFrame import Global as gl
#import Global as gl

download_img_queue = []


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
        #if self.sects == {}:
        #    return
        if not os.path.exists(gl.g_config_folder):
            os.mkdir(gl.g_config_folder)

        for sec in self.sects:
            if not self.cfg_parser.has_section(sec):
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

    def __enter__(self):
        """base function for `with` syntax"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """base function for `with` syntax"""
        self.save()


  

def mysql_params():

    if gl.g_mysql_params != {}:
        print 'current MySQL parameters in config.ini is:'
        print gl.g_mysql_params
        return

    print "input parameters for MySql"
    gl.g_mysql_params['host'] = raw_input('host : ')
    gl.g_mysql_params['port'] = int(raw_input('port(default 3306) : '))
    gl.g_mysql_params['user'] = raw_input('username : ')
    gl.g_mysql_params['passwd'] = raw_input('password : ')
    gl.g_mysql_params['db'] = raw_input('database : ')
    gl.g_mysql_params['charset'] = raw_input('charset(default `utf8`) : ')

    with IniParser() as ini:
        ini.modify('DataBase', **gl.g_mysql_params)

def image_folder():
    """"""
    if gl.g_storage_path is not None:
        print 'current storage folder is:'
        print gl.g_storage_path
        return

    notice = 'please input folder path for storage image.\nmake sure tha disk has enough space\n'
    folder = raw_input(notice)
    gl.g_storage_path = folder

    with IniParser() as ini:
        ini.modify('ImageFolder', **{'folder':gl.g_storage_path})

def loadcfg():
    """"""
    cfg = IniParser()
    if cfg.sects != {}:
        gl.g_storage_path = cfg.sects['ImageFolder']['folder']
        gl.g_mysql_params = cfg.sects['DataBase']
        gl.g_mysql_params['port'] = int(gl.g_mysql_params['port'])
    else :       
        image_folder() 
        cfg.modify('ImageFolder', **{'folder':gl.g_storage_path})
                
        mysql_params()
        cfg.modify('DataBase', **gl.g_mysql_params)



loadcfg()

if __name__ == "__main__":

    with IniParser() as  ini:

        ini.modify('ImageFolder', **{'folder':'E:/zhihuimg'})

    print 'Done!' 
        



