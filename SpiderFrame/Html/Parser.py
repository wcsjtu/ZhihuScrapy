# -*- coding: utf-8 -*-
# ATTENTION: this module doesn't support multi-threading or multiprocessing.
# MAKE SURE there's only one Parser process!!!! 

import re
import os
import HTMLParser
import multiprocessing
import Queue
from multiprocessing import Manager
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append("..")

#import Global as gl
from SpiderFrame import Global as gl
from ..Http.SexTuple import HttpSextp, HttpSrsc
from ..Logger import ZhihuLog
from ..Rules.Rules import RuleFactor

_g_html_logger = ZhihuLog.creatlogger(__name__)


class BasicParser(HTMLParser.HTMLParser):
    def __init__(self):
        self._urls = []
        HTMLParser.HTMLParser.__init__(self)    

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name,value in attrs:
                if name == 'href':
                    self._urls.append(value)





class ParserProc(multiprocessing.Process):
    """base class for parser process"""

    # mapping between parse method and sextp.url, which used to identify whether parse method should be called to parse html specified by this kind of url
    # the format of mapping is {"method_name": _sre.SRE_Pattern instance}, such as {"parse_bing": re.compile(r'cn.bing.com')}.
    # if sextp.url has no parse method in mapping, the default parse method 'parse_default' will be called.
    method_url_map = {}
    TIME_OUT = 5

    def __init__(self, name_ ):
        super(ParserProc, self).__init__(name = name_)
        self.daemon = True
        self.exit = False
        self._args = ({'html_queue':  gl.g_html_queue,
                        'url_queue':  gl.g_url_queue,
                        'data_queue': gl.g_data_queue,
                        'static_rc':  gl.g_static_rc},
                     )
        self._basic_parser = BasicParser()
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
        while True:
            if self.exit:
                print 'task completed! process %s exit'%self.name
                os._exit(0) 
            try:
                sextp = html_queue.get(timeout = self.TIME_OUT)
                print "get url in Parser: ", sextp.url
                self.dispatch(sextp, proc_queue)
            except Queue.Empty:
                print "timeout, queue size in proc Parser: ", html_queue.qsize()
                pass
            #print "url in Parser: ",sextp.url                 
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
        @return: if method decroated by Rules.filter, it must return instance of RuleFactor. if there no decroator, method must return list of Sextp           
        """
        self._basic_parser._urls = []
        ret = []
        self._basic_parser.feed(sextp.response[0])
        if self._basic_parser._urls == []:
            return None
        else:
            return RuleFactor(urls=self._basic_parser._urls)

    def dispatch(self, sextp, proc_queues):
        """
        according to sextp.url and method_url_map, dispatch sextp to parse_xxx method
        """
        ret = None
        for func in self.method_url_map:
            if self.method_url_map[func].search(sextp.url):
                ret = func(self, sextp, proc_queues)
                if ret is not None:
                    for obj in ret:
                        proc_queues['url_queue'].put(obj) 
                return 
        ret = self.parse_default(sextp, proc_queues)
        if ret is not None:
            for obj in ret:
                proc_queues['url_queue'].put(obj)

    def quit(self):
        """force process to exit"""
        self.exit = True
    
    @classmethod
    def add_map(cls, func, pattern):
        """add map relation of func and pattern to cls.method_url_map"""
        assert isinstance(pattern, re.compile(r"").__class__)
        cls.method_url_map[func] = pattern

    def extract_url(self, html):
        """
        extract urls from html and return a list of urls
        """
        # the variable below leads to this module couldn't work in multi-thread condition
        self._basic_parser._urls = []
        self._basic_parser.feed(html)
        return self._basic_parser._urls

    @classmethod
    def set_timeout(cls, timeout):
        """
        set timeout value when get element from empty queue
        """
        assert timeout>=0, "parameter `timeout` must be positive value!"
        cls.TIME_OUT = timeout