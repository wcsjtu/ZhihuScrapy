# -*- coding: utf-8 -*-

import re
import os
import multiprocessing
from multiprocessing import Manager
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append("..")

#import Global as gl
from SpiderFrame import Global as gl
from ..Http.SexTuple import HttpSextp, HttpSrsc
from ..Rules.Rules import RuleFactor

class ParserProc(multiprocessing.Process):
    """base class for parser process"""
    def __init__(self, name_ ):
        super(ParserProc, self).__init__(name = name_)
        self.daemon = True
        self.exit = False
        self._args = ({'html_queue':  gl.g_html_queue,
                        'url_queue':  gl.g_url_queue,
                        'data_queue': gl.g_data_queue,
                        'static_rc':  gl.g_static_rc},
                     )
        self._target = self.work

    def work(self, proc_queue):
        """
        @params: proc_queue, dict. queues between two different process to share memeories. 
                 Its format is {'html_queue': gl.g_html_queue,
                 'url_queue': gl.g_url_queue,
                 'data_queue': gl.g_data_queue,
                 'static_rc': gl.g_static_rc} 
        """
        html_queue = proc_queue['html_queue']
        url_queue = proc_queue['url_queue']
        try:
            while True:
                if url_queue.empty() and html_queue.empty() or self.exit:
                    print 'task completed! process %s exit'%self.name
                    os._exit(0) 
                sextp = html_queue.get()
                self.dispatch(sextp, proc_queue) 
        except Exception, e :
            _g_html_logger.error(e)         
        os._exit(0) 

    def parse_default(self, sextp, proc_queue):
        """
          default parser. It will be called when the url of html has no matched parser.
        this method just abstracts urls from html, and filter the static resource, such
        as ico, css, jpg, jpeg, png, js and etc.
          If needed, override it
        @params: sextp, instance of class HttpSextp. See Http/SexTuple.py for detail
                 proc_queue, dict. queues between two different process to share memeories. Its format is {'html_queue': gl.g_html_queue,
                                                                                                           'url_queue': gl.g_url_queue,
                                                                                                           'data_queue': gl.g_data_queue,
                                                                                                           'static_rc': gl.g_static_rc}                   
        """
        url_list = re.findall(r'href="(.+?)"', sextp.response[0])
        #TODO filter(url_list)
        return RuleFactor(urls=url_list)
        pass

    def dispatch(self, sextp, proc_queues):
        """
        interface, must be override in subclass
        """
        raise NotImplementedError("method dispatch must be override in subclass of ParserProc!")

    def quit(self):
        """force process to exit"""
        self.exit = True
