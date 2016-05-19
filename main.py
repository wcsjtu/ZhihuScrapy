# -*- coding: utf-8 -*-

from HttpClient import *
import Global as gl
import Control
import ZhihuHtmlParser
import LocalFile
import DataBase



if __name__ == '__main__':

    
    config = LocalFile.loadini()
    if config == {}:        
        folder = raw_input('please input folder of image\n')
        gl.g_storage_path = folder                
        account = InputAccount()	
        account["remember_me"] = "true"
        LocalFile.saveini(**dict(account, img_folder=folder))
    else:
        gl.g_storage_path = config['img_folder']
        del config['img_folder']
        account = config
            
    gl.g_http_client = HttpClient("https://www.zhihu.com", account) 
    print 'create HttpClient instance'
    controller = Control.Control()

    controller.init_task(kw=u'site:zhihu.com/question *', std=1)
    controller.wait_cmd()
    

    


