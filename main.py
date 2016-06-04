# -*- coding: utf-8 -*-

import datetime
#from HttpClient import *
import Global as gl
#import Control
#import ZhihuHtmlParser
import LocalFile
import DataBase
import ZhihuLog

def input_account():
    """
    method to input account
    """
    import re
    email_pattern = "^([a-z0-9A-Z]+[-|\\.]?)+[a-z0-9A-Z]@([a-z0-9A-Z]+(-[a-z0-9A-Z]+)?\\.)+[a-zA-Z]{2,}$"
    phone_num_pattern = r"^1\d{10}$"

    print "Please entry your ZhiHu account"
    while True:
        username = raw_input("username : ")
        if re.match(email_pattern,username):
            user_type = "email"
            break
        if re.match(phone_num_pattern, username):
            user_type = "phone_num"
            break
        else:
            print "username is invalid, please input email or mobile phone number!"

    password = raw_input("password : ")
    gl.g_zhihu_account = {user_type:username, "password":password, 'remember_me':"true"}      

def mysql_params():
    print "input parameters for MySql"
    gl.g_mysql_params['host'] = raw_input('host : ')
    gl.g_mysql_params['port'] = int(raw_input('port(default 3306) : '))
    gl.g_mysql_params['user'] = raw_input('username : ')
    gl.g_mysql_params['passwd'] = raw_input('password : ')
    gl.g_mysql_params['db'] = raw_input('database : ')
    gl.g_mysql_params['charset'] = raw_input('charset(default `utf8`) : ')

def image_folder():
    """"""
    notice = 'please input folder path for storage image.\nmake sure tha disk has enough space\n'
    folder = raw_input(notice)
    gl.g_storage_path = folder

def init():
    """"""
    cfg = LocalFile.IniParser()
    if cfg.sects == {}:       
        image_folder() 
        cfg.modify('ImageFolder', **{'folder':gl.g_storage_path})
        
        input_account()                        
        cfg.modify('Account', **gl.g_zhihu_account)
        
        if DataBase._mysql_flag:
            mysql_params()
            cfg.modify('DataBase', **gl.g_mysql_params)

        cfg.save()

    else:
        gl.g_storage_path = cfg.sects['ImageFolder']['folder']
        gl.g_zhihu_account = cfg.sects['Account']
        gl.g_mysql_params = cfg.sects['DataBase']
        gl.g_mysql_params['port'] = int(gl.g_mysql_params['port'])
        

if __name__ == '__main__':

    from ZhihuHtmlParser import ZhihuQuestion, ZhihuAnswer, ZhihuUser
    init()

    gl.g_zhihu_database = DataBase.ZhihuDataBase()
    gl.g_fail_url = ZhihuLog.creatlogger('%s_FailURL'%datetime.datetime.now().strftime('%Y-%m-%d'))
            
    # gl.g_http_client = HttpClient("https://www.zhihu.com", gl.g_zhihu_account) 
    # print 'create HttpClient instance'
    # controller = Control.Control()

    # controller.init_task(kw=u'site:zhihu.com/question *', std=1)
    # controller.wait_cmd()


    q = ZhihuQuestion(title=u'马化腾写代码的水平如何？ - 腾讯 - 知乎', url='/question/20485547', keywords='')
    a = ZhihuAnswer(5042800, 1397376050, 0, '/people/si-pi-lie-dan', u'撕皮裂蛋', 790, 111, u'不得不服周杰伦 全是自己的歌', '', '', '/people/si-pi-lie-dan', '/question/23371727', '24440533', False)


    gl.g_zhihu_database.insert_data(a)
    gl.g_zhihu_database.insert_data(q)
    gl.g_zhihu_database._commit_data()
    data = gl.g_zhihu_database.read('Users', u"education='北京大学'")
    print data
    


