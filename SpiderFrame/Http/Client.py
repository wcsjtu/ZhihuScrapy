# -*- coding: utf-8 -*-

import Queue
import urlparse
import socket
import urllib
import json
import cookielib
import threading
import requests
import time
import os
import re
import copy

import sys


reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append("..")

from SpiderFrame import Global as gl
from SpiderFrame import ErrorCode
from ..Logger import ZhihuLog
from ..Local import Config
from SexTuple import HttpSextp, HttpSrsc


socket.setdefaulttimeout(5.0)

"""
this file defines basic httpclient 
"""

class HttpClient(object):
    """"""
    _MAX_LOGIN_LIMIT = 1
    TIMEOUT = 10

    def __init__(self):
       
        self.url = None
        self.account = None
        self.default_headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0",
                                "connection":"keep-alive",
                                "Accept-Encoding": "gzip"}
        self._is_init = False
        self.load_cookies_success = False
        self.login_success = False
        self.logger = ZhihuLog.creatlogger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.headers = self.default_headers
        self.session.cookies = cookielib.LWPCookieJar(gl.g_config_folder + 'cookiejar')
        if os.path.exists(gl.g_config_folder+'cookiejar'):
           self.session.cookies.load(ignore_discard=True)
           self.load_cookies_success = True    

    @property
    def host(self):
        return self.url
    
    def get_headers(self):
        return copy.deepcopy(self.default_headers)

    def url_request(self, method_, url_, payloads_, headers_):
        """
        @params: method, http method, 'GET' or 'POST', or 'PUT', or 'DELETE', or 'HEAD'
                 url, url, string, absolute url of resource at goal webserver
                 payloads, dict or None, extra data to send when visit certain resource
                 headers, dict  or None, customed headers
        @return: if http status is 200, this function will return HttpSextp instance. See SexTuple.py for detail.
                 if occurs connection error or http status is not 200, this function will return None
        """
        try:
            header = self.default_headers if headers_ is None else headers_
            payloads = urllib.urlencode(payloads_) if payloads_ is not None else None
            if payloads is not None:
                pass
            rqst = self.session.request(method=method_, url=url_, params=payloads, headers=header, timeout=self.TIMEOUT) 
            if 'Set-Cookie' in rqst.headers or 'Set-Cookie2' in rqst.headers:
                self.session.cookies.save(ignore_discard=True)
            if rqst.status_code != ErrorCode.HTTP_OK:
                rqst = self.session.request(method=method_, url=url_, params=payloads, headers=header, timeout=self.TIMEOUT)
                if rqst.status_code != ErrorCode.HTTP_OK:
                    if rqst.status_code != ErrorCode.HTTP_NOTFOUND:
                        gl.g_fail_url.put( HttpSextp(url_, method_, headers_, payloads_, None, None) )

                    print "%s: %s with payloads %s"%(rqst.status_code, url_, str(payloads_))
                    self.logger.error( "%s: %s with payloads %s"%(rqst.status_code, url_, str(payloads_)) )
                    return None
            return HttpSextp(url_, method_, headers_, payloads_, [rqst.content], rqst.headers)

        except (requests.HTTPError, requests.Timeout, requests.ConnectionError), e: 
            print "%s: %s with payloads %s"%(e, url_, str(payloads_))
            self.logger.error( "%s: %s with payloads %s"%(e, url_, str(payloads_)) )
            gl.g_fail_url.put( HttpSextp(url_, method_, headers_, payloads_, None, None) )
            return None
                 
    def get_html(self, method_, url_, payloads_, headers_):
        """get html and put it into html queue"""
        ret = self.url_request(method_, url_, payloads_, headers_)
        if ret is not None:
            gl.g_html_queue.put(ret)

    def get_static_rc(self, urls, headers, storepath):
        """
        get static resource and store it in certain path
        @params: urls, list of static resource's url
                 headers, dict or None, customed headers
                 storepath, file system folder, which store the resources in urls, such as E:/zhihuimg/ for windows, /meida/zhihuimg for linux
        """
        try:
            if not os.path.exists(storepath):
                os.mkdir(storepath)
        except WindowsError, e :
            gl.g_http_client.logger.error( "fail to check path %s" %storepath)
        for url_ in urls:
            try:
                rc_name = url_.split('/')[-1]
                rc_path = os.path.join(storepath, rc_name)
                if os.path.exists(rc_path):
                    print "EXISTD %s"%rc_name
                    continue
                ret = self.url_request('GET', url_, None, None)
                if ret is not None:
                    with open(rc_path, 'wb') as f:
                        f.write(ret.response[0])
                    print "OK %s"%rc_name
            except (IndexError, IOError), e :
                gl.g_http_client.logger.error( "%s when downloading img %s" % (e, url_))
                print "%s when downloading img %s" % (e, url_)


    def _get_veri_code(self):
        """to get captcha"""
        raise NotImplementedError("method must be override in child class")

    def login(self):
        """"""
        raise NotImplementedError("method must be override in child class")

    @classmethod
    def set_timeout(cls, timeout):
        """
        set timeout value when get web source
        """
        assert timeout>=0, "parameter `timeout` must be positive value!"
        cls.TIMEOUT = timeout


#gl.g_http_client = HttpClient()

class HtmlClient(threading.Thread):
    """charged to handle html request and put them into queue"""

    GET_TIMEOUT = 10
    intval = 0

    def __init__(self, name_):
        
        self.exit = False
        self.httpclient = gl.g_http_client
        self.work_func = gl.g_http_client.get_html
        super(HtmlClient, self).__init__(name = name_)
        self.setDaemon(False)
        self.start()

    def quit(self):
        """force thread to exit"""
        self.exit = True

    def run(self):
        """loop"""
        while True:
            #if (gl.g_url_queue.empty() and gl.g_html_queue.empty()) or self.exit:
            if self.exit:
                self.httpclient.logger.warning('task completed! thread %s exit'%self.name)
                print 'task completed! thread %s exit'%self.name
                break

            if not gl.g_url_queue.empty():
                try:
                    ele = gl.g_url_queue.get(timeout=self.GET_TIMEOUT)
                    self.work_func(ele.method, ele.url, ele.payloads, ele.request_headers)
                except Queue.Empty, e :
                    self.httpclient.logger.warning('timeout when get url from url queue')
                finally:
                    time.sleep(self.intval)
    
    @classmethod
    def set_intval(cls, intval):
        """
        set inteval between two http request
        @params: intval, unit is second
        """
        assert intval >=0, "inteval must be positive value"
        cls.intval = intval

    @classmethod
    def set_get_timeout(cls, timeout):
        """
        set timeout value when get element from empty queue
        """
        assert timeout>=0, "parameter `timeout` must be positive value!"
        cls.GET_TIMEOUT = timeout


class StaticClient(threading.Thread):
    """charged to handle static resource and store them in file system"""

    GET_TIMEOUT = 10
    intval = 0

    def __init__(self, name_):
        """"""
        Config.image_folder()
        super(StaticClient, self).__init__(name = name_)
        self.httpclient = gl.g_http_client
        self.work_func = gl.g_http_client.get_static_rc
        self.exit = False
        self.setDaemon(False)
        self.start()


    def quit(self):
        """force thread to exit"""
        self.exit = True

    def run(self):
        """loop"""
        while True:
            #if (gl.g_url_queue.empty() and gl.g_html_queue.empty() and gl.g_static_rc.empty()) or self.exit:
            if self.exit:
                self.httpclient.logger.warning('task completed! thread %s exit'%self.name)
                print 'task completed! thread %s exit'%self.name
                break
            
            if not gl.g_static_rc.empty():
                try:
                    ele = gl.g_static_rc.get(timeout=self.GET_TIMEOUT)     # HttpSrsc instance
                    self.work_func(ele.urls, ele.headers, ele.storepath)
                except Queue.Empty, e :
                    self.httpclient.logger.warning('timeout when get url from url queue')
                finally:
                    time.sleep(self.intval)

    @classmethod
    def set_intval(cls, intval):
        """
        set inteval between two http request
        @params: intval, unit is second
        """
        assert intval >=0, "inteval must be positive value"
        cls.intval = intval

    @classmethod
    def set_get_timeout(cls, timeout):
        """
        set timeout value when get element from empty queue
        """
        assert timeout>=0, "parameter `timeout` must be positive value!"
        cls.GET_TIMEOUT = timeout
