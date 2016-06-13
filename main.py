# -*- coding: utf-8 -*-

import datetime
from HttpClient import *
import Global as gl
import Control
import ZhihuHtmlParser
import LocalFile
import DataBase
import ZhihuLog




if __name__ == '__main__':

    from ZhihuHtmlParser import ZhihuQuestion, ZhihuAnswer, ZhihuUser, ZhihuPaser

    
    
            
     
    #gl.g_http_client.login()
    print 'create HttpClient instance'
    # controller = Control.Control()

    # controller.init_task(kw=u'site:zhihu.com/question *', std=1)
    # controller.wait_cmd()


    


    u0 = ['GET', 'https://cn.bing.com/search', {'q':'site:zhihu.com/question *', 'first':1}, None]
    u1 = ['GET', 'https://www.zhihu.com/question/39677202', None, None]
    u2 = ['GET', 'https://www.zhihu.com/r/answers/31504680/comments', None, None]
    u3 = ['GET', 'https://www.zhihu.com/people/wang-su-yang-43/about', None, None]
    gl.g_url_queue.put(u0)
    gl.g_url_queue.put(u1)
    #gl.g_url_queue.put(u3)

    
    print 'main', gl.g_zhihu_database
    htmldownloader = HtmlClient(name_ = 'Html')
    imgdownloader = StaticClient(name_ = 'Image')

    parser = ZhihuPaser(name_ = 'Parser')


    while True:
        print 'url queue:  ', gl.g_url_queue.qsize()
        print 'html queue: ', gl.g_html_queue.qsize()
        print 'data queue: ', gl.g_data_queue.qsize()
        print 'image queue:', gl.g_static_rc.qsize()
        print '========================================='
        print ''
        print ''
        time.sleep(3)



    print 11




    #while not gl.g_url_queue.empty():
    #    ele = gl.g_url_queue.get()    
    #    gl.g_http_client.get_html(*tuple(ele))

    #while not gl.g_html_queue.empty():
    #    parser.dispatch()

    #gl.g_zhihu_database.write()
    #gl.g_zhihu_database._commit_data()




    #q = ZhihuQuestion(title=u'马化腾写代码的水平如何？ - 腾讯 - 知乎', url='/question/20485547')
    #a = ZhihuAnswer(5042800, 1397376050, 0, '/people/si-pi-lie-dan', u'撕皮裂蛋', 790, 111, u'不得不服周杰伦 全是自己的歌', '', '', '/people/si-pi-lie-dan', '/question/23371727', 24440533, False)


    #gl.g_zhihu_database.insert_data(a)
    #gl.g_zhihu_database.insert_data(q)
    #gl.g_zhihu_database._commit_data()
    #data = gl.g_zhihu_database.read('Users', u"education='北京大学'")
    #print data
    


