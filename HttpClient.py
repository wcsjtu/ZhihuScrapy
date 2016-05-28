# -*- coding: utf-8 -*-
"""
singleton
"""
import Queue
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
import LocalFile as lf
import Global as gl
import ZhihuHtmlParser
import ZhihuLog
import ErrorCode
import Captcha
socket.setdefaulttimeout(5.0)

_GET_QUEUE_TIMEOUT = 20


_SEARCH_INTERVAL = 5
_COMMET_INTERVAL = 1
_USER_INTERVAL = 0


class HttpClient(object):
    """"""
    _MAX_LOGIN_LIMIT = 5

    def __init__(self, url, account):
       
        self._url = url
        self.account = account
        self._verify_code = ""
        self.default_headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0",
                                "connection":"keep-alive"}
        self._is_init = False
        self.login_success = False
        self.logger = ZhihuLog.creatlogger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.cookies = cookielib.LWPCookieJar(gl.g_config_folder + 'cookiejar')
        #if os.path.exists(gl.g_config_folder+'cookiejar'):
        #    self.session.cookies.load(ignore_discard=True)
            #self.login_success = True        
        if not self.login_success :
            self.login()
            pass

    def get_host(self):
        return self._url
    
    def get_headers(self):
        return copy.deepcopy(self.default_headers)

    def get_html(self, url, payload=None, header=None):
        """
        parameters: url, string, absolute url of resource at goal webserver
                    payload, dictionary, extra data to send when visit certain resource
                    header, dictionary, customed headers
        return: return dictionary, value is [error code, response headers, html(string) or binary data]
        """
        try:
            if payload is None:
                if header is None:
                    rqst = self.session.get(url, headers=self.default_headers, timeout=10)
                else:
                    rqst = self.session.get(url, headers=header, timeout=10)
            else:
                if header is None:
                    rqst = self.session.post(url, data=payload, headers=self.default_headers, timeout=10)
                else:
                    rqst = self.session.post(url, data=payload, headers=header, timeout=10) 
            self.session.cookies.save(ignore_discard=True)   
            if rqst.status_code != 200: 
                gl.g_fail_url.warning('%s %s'%(url, str(payload)))                
            return {'errno':rqst.status_code, 'headers':rqst.headers, 'content':[rqst.content]}
            
        except (requests.HTTPError, requests.Timeout, requests.ConnectionError), e:
            tips = '%s when visit %s '%(e, url) if payload is None else '%s when \
                    visit %s with data %s'%(e, url, str(payload).decode('unicode_escape'))
            self.logger.error(tips)
            gl.g_fail_url.warning('%s %s'%(url, str(payload)))
            return {'errno':ErrorCode.HTTP_FAIL, 'headers':{}, 'content':[]}
        except requests.TooManyRedirects, e :
            tips = '%s when visit %s '%(e, url) if payload is None else '%s when \
                    visit %s with data %s'%(e, url, str(payload).decode('unicode_escape'))
            self.logger.error(tips) 
            gl.g_fail_url.warning('%s %s'%(url, str(payload)))           
            return {'errno':ErrorCode.HTTP_TOMANY_REDCT, 'headers':{}, 'content':[]}

    def _get_veri_code(self):
        """to get captcha"""
        url = "https://www.zhihu.com/captcha.gif?r=1462615220376&type=login"
        response = self.get_html(url)
        if response['errno'] != ErrorCode.HTTP_OK:
            self.logger.error("Fail to get captcha!")
            return False
        else:
            captcha = open('captcha.gif','wb')
            captcha.write(response['content'][0])
            captcha.close()
            return True

    def login(self):
        """"""
        self.account['remember_me'] = "true" 
        uri = "/login/email" if 'email' in self.account else "/login/phone_num"
        login_url = self._url+uri
        response = self.get_html(self._url)       
        login_counter = 0
        while login_counter <= self._MAX_LOGIN_LIMIT:       
            login_counter += 1  
            try:
                if 'Set-Cookie' in response['headers'] and '_xsrf' not in self.account:
                    self.account['_xsrf'] = re.search("_xsrf=(.+?);", \
                    response['headers']['Set-Cookie']).group(0)[6:]   # '_xsrf=9bfe1f29fc48e124b60a1d80f7272f7a;'
                response2 = self.get_html(login_url, payload=self.account)
                if response2['errno'] == ErrorCode.HTTP_OK:
                    ret_value = json.loads(response2['content'][0])['r']
                    if ret_value == 0:
                        self.logger.error('Succeed to login')
                        self.login_success = True
                        self._is_init = True
                        return True
                    else:
                        ret = self._get_veri_code()
                        if not ret:continue
                        Captcha.show_captcha()
                        cap = raw_input('please input Captcha which showed in your screen\n')
                        self.account['captcha'] = cap
                        continue                        
                else:
                    self.logger.info("Fail to login")
                    continue
            except IndexError, e:
                self.logger.error('Fail to login, reason is %s'%e)
                
        self.login_success = False
        self._is_init = True
        return False


class SearchEngine(threading.Thread):
    """
    class to search resourch by key on given website
    """
    _parser = ZhihuHtmlParser.SearchPageParser()
    _QUESTION_PER_PAGE = ZhihuHtmlParser.SearchPageParser.MAX_QUESTION_PER_SEARCH_PAGE

    def __init__(self, url, keyword, results_num=None, ui_mode=False):
        """
        parameters: url, given webstie
                    key_words, key words
                    results_num, the count of result user wants to get
                    ui_mode, if false, self.search method work at scrapy mode, cover all the questions returned by key words
        """
        threading.Thread.__init__(self, name='SearchEngine')
        self.url = url
        self.key_words = keyword
        self.results_num = results_num
        self.ui_mode = ui_mode
        self.setDaemon(False)
        self.start()
        

    def search(self):
        """"""
        for item in self.keyword_list:
            self.key_words = item
            search_by_keyword = {"q":self.key_words, "type":"content"}    # after March, 18，`question` is replaced by `content`
            search_url = self.url + '/search?' + urllib.urlencode(search_by_keyword)
            response = gl.g_http_client.get_html(search_url)
            if response['errno'] != ErrorCode.HTTP_OK:  # if http error or socket error, retry once
                response = gl.g_http_client.get_html(search_url)
            ret = self._parser.ParserHtml(response['content'], self.key_words, self.results_num, AJAX=False)
            if ret == ErrorCode.LIST_EMPTY_ERROR:  # if find nothing in html , retry once
                response = gl.g_http_client.get_html(search_url)
                ret = self._parser.ParserHtml(response['content'], self.key_words, self.results_num, AJAX=False)
            if ret == ErrorCode.ACHIEVE_END or ret == ErrorCode.ACHIEVE_USER_SPECIFIED:  # if achieve to the end of questions, return
                return

        if self.ui_mode:   # if UI mode is active, method 'more'
            return         # will be called by 'MORE' button , rather than by console

        if self.results_num is not None:
            remainder = self.results_num - ZhihuHtmlParser.SearchPageParser.MAX_QUESTION_PER_SEARCH_PAGE
        else:
            remainder = None
        i = 0
        while True:
            i += 1
            html = self.More(self._QUESTION_PER_PAGE*i)
            ret = self._parser.ParserHtml(html, self.key_words, remainder, AJAX=True)
            if ret == ErrorCode.LIST_EMPTY_ERROR:
                ret = self._parser.ParserHtml(self.More(self._QUESTION_PER_PAGE*i),
                                              self.key_words, remainder, AJAX=True)
            if ret == ErrorCode.ACHIEVE_END or ret == ErrorCode.ACHIEVE_USER_SPECIFIED:
                break
            elif ret == ErrorCode.OK:
                if remainder is not None:
                    remainder -= ZhihuHtmlParser.SearchPageParser.MAX_QUESTION_PER_SEARCH_PAGE

    def More(self, offset):
        """"""
        # after March,18，{"q":self.key_words, "type":"question", "range":"","offset":offset}
        # is replaced by{"q":self.key_words, "type":"content", "offset":offset}
        search_by_keyword={"q":self.key_words, "type":"content", "offset":offset}
        search_url = self.url + '/r/search?' + urllib.urlencode(search_by_keyword)
        response = gl.g_http_client.get_html(search_url)
        if response['errno'] != ErrorCode.HTTP_OK:
            gl.g_http_client.logger.warning('%s when get %s'%(response['errno'], search_url))
        return response['content']

    @classmethod
    def search_by_bing(cls, keywords):
        """"""
        bing = 'https://cn.bing.com/search?'
        first = 1
        while True:
            
            try:
                payload = urllib.urlencode({'q':keywords, 'first':first})
                url = ''.join([bing, payload])
                response = gl.g_http_client.get_html(url)
                if response['errno'] != ErrorCode.HTTP_OK:
                    gl.g_http_client.logger.warning('%s when get %s'%(response['errno'], url))
                ret = ZhihuHtmlParser.SearchPageParser.ParserBing(response['content'])
                first += ZhihuHtmlParser.SearchPageParser._QUESTION_PER_PAGE_BING
                gl.g_exit_quest_index = first
                #if ret == ErrorCode.ACHIEVE_END:
                #    break
            except Exception,e:
                first += ZhihuHtmlParser.SearchPageParser._QUESTION_PER_PAGE_BING
                gl.g_http_client.logger.error('%s when search bing at first=%s'%(e, first))
                gl.g_exit_quest_index = first
            finally:
                if gl.g_question_exit:                     
                    return first
                time.sleep(_SEARCH_INTERVAL)

    def run(self):
        self.search_by_bing(self.key_words)


class QuestionAbs(threading.Thread):

    _parser = ZhihuHtmlParser.QuestionParser()
    _ANSWERS_PER_PAGE = ZhihuHtmlParser.QuestionParser.MAX_ANSWERS_PER_PAGE

    def __init__(self, name, ui_mode=False, question_index=None):
        """"""
        threading.Thread.__init__(self)
        self.name = name
        self.ui_mode = ui_mode
        if ui_mode: self.done=False
        self.question_index = question_index
        self.setDaemon(False)
        self.start()

    @classmethod
    def parse_answers(cls, question_url, headers):
        """
        the format of question_url is `/question/\d{8}`, for example, /question/25835899
        """
        response = gl.g_http_client.get_html(gl.g_http_client.get_host()+question_url, header=headers)
        ret, max_answ_counts = cls._parser.ParserHtml(response['content'], question_url, AJAX=False)
        if ret == ErrorCode.ACHIEVE_END:
            return ErrorCode.ACHIEVE_END

        offset = 0 
        remainder = max_answ_counts - cls._ANSWERS_PER_PAGE
        while remainder > 0:
            offset += 1
            html = cls.more(question_url, offset*cls._ANSWERS_PER_PAGE)
            ret, _ = cls._parser.ParserHtml(html, question_url, AJAX=True)
            if ret == ErrorCode.LIST_EMPTY_ERROR:
                print 'visit %s with offset %s once again!' % (question_url, str(offset*cls._ANSWERS_PER_PAGE))
                gl.g_http_client.logger.warning('visit %s with offset %s once again!' % (question_url, str(offset*20)))
                response = gl.g_http_client.get_html(gl.g_http_client.get_host()+question_url)
                ret, _ = cls._parser.ParserHtml(response['content'], question_url, AJAX=True)
            if ret == ErrorCode.ACHIEVE_END:
                break
            elif ret == ErrorCode.OK:
                remainder -= cls._ANSWERS_PER_PAGE
        return ErrorCode.ACHIEVE_END

    def run(self):
        """"""
        _headers = gl.g_http_client.get_headers()
        _headers['Referer'] = gl.g_http_client.get_host()
        while True:

            if gl.g_question_queue.empty() and gl.g_question_exit:
                print "Task compeleted! thread %s exit!\n" % self.name
                gl.g_http_client.logger.warning("Task compeleted! thread %s exit!\n" % self.name)
                break 
            else:
                if self.ui_mode:
                    if self.done:
                        break
                    goal_url = gl.g_question_queue.queue[self.question_index].question_url  # maybe error
                    self.done = True
                    if goal_url.startswith('http'):
                        gl.g_http_client.logger.warning('zhuanlan url %s' % goal_url)
                        continue 
                else:
                    try:    
                        goal_url = gl.g_question_queue.get(timeout=_GET_QUEUE_TIMEOUT)
                    except Queue.Empty,e:
                        print 'timeout when get question url in %s thread'%self.name
                        gl.g_http_client.logger.warning('timeout when get question url in %s thread'%self.name)
                        continue
                    print goal_url 
                    if goal_url.startswith('http'):
                        gl.g_http_client.logger.warning('zhuanlan url %s'%goal_url)
                        continue
            ret = self.parse_answers(goal_url, _headers)
        gl.g_comment_exit = True
        gl.g_usr_exit = True
        gl.g_retrieve_exit = True
        return 0
            
    @classmethod
    def more(cls, goal_url, offset):
        """
        parameter: offset equal to 10*i, where i is 1,2,3.....
        return html and answers count
        retval count will be used to judge when to break loop
        """
        uri = '/node/QuestionAnswerListV2'
        question_code = goal_url.split('/')[2]
        gl.g_http_client.default_headers['Referer'] = "https://www.zhihu.com" + goal_url
        gl.g_http_client.default_headers['Content-Type'] = "application/x-www-form-urlencoded; charset=UTF-8"
        pagesize = cls._ANSWERS_PER_PAGE
        post_data = "method=next&params=%7B%22url_token%22%3A" + question_code + "%2C%22pagesize%22%3A" + str(pagesize) + \
                    "%2C%22offset%22%3A" + str(offset) + "%7D&_xsrf=" + gl.g_http_client.account['_xsrf']
        response = gl.g_http_client.get_html(gl.g_http_client.get_host()+uri, post_data)
        if response['errno'] != ErrorCode.HTTP_OK:
            gl.g_http_client.logger.warning('%s when get %s'%(response['errno'], question_code))
        return response['content']


class RetrieveAgent(threading.Thread):

              
    def __init__(self, name, ui_mode=False):
        """"""
        threading.Thread.__init__(self)
        self.name = name
        self.setDaemon(False)
        self.parser = ZhihuHtmlParser.PersonPageParser()
        self.ui_mode = ui_mode
        self.downloadimg_queue = []
        self.start()

    @classmethod
    def _check_folder(cls, foder_path):
        """
        check the path is existed or not, if not, create it
        folder_path is the name of user. eg. likaifu
        """
        
        absolut_path = ''.join([gl.g_storage_path, '/people/',  foder_path])
        if not os.path.exists(absolut_path) :
            os.makedirs(absolut_path)
        return absolut_path

    def retrieve_image(self):
        """"""
        while True:
            
            if gl.g_img_queue.empty() and gl.g_retrieve_exit:
                print "Task compeleted! thread %s exit"%self.name
                gl.g_http_client.logger.warning("Task compeleted! thread %s exit"%self.name)
                break

            try:
                answer = gl.g_img_queue.get(timeout=_GET_QUEUE_TIMEOUT)        
            except Queue.Empty, e:
                print 'timeout when get img list in %s thread'%self.name
                gl.g_http_client.logger.warning('timeout when get img list in %s thread'%self.name) 
                continue

            folder_path = self._check_folder(answer['user_name'])
            for url in answer['img_urls']:
                img_name = url.split('/')[3]
                file_path = ''.join([folder_path, '/', img_name])
                if not os.path.exists(file_path):
                    ret = self.downloader(url, file_path)
                    if not ret: ret = self.downloader(url, file_path)
                    if ret and self.ui_mode:  self.downloadimg_queue.append(''.join(['/people/', answer['user_name'], '/', img_name, '\n']))
                else:
                    gl.g_http_client.logger.info( "%s is existed"%file_path)
                    if self.ui_mode : self.downloadimg_queue.append(answer.userlink+'/'+img_name+'\n')



    @classmethod
    def downloader(cls, url, path):
        if not url.startswith('http') : return False
        try:
            response = gl.g_http_client.get_html(url)
            if response['errno'] != ErrorCode.HTTP_OK:
                response = gl.g_http_client.get_html(url)
            if response['errno'] != ErrorCode.HTTP_OK:
                gl.g_http_client.logger.warning("img %s NOT OK" % url)
                return False
            data = response['content'][0]
            tofile = open(path, 'wb')
            tofile.write(data)
            tofile.close()
            gl.g_http_client.logger.info("img %s OK"%url)
            return True
        except Exception, e:
            gl.g_http_client.logger.error( "%s when downloading img %s" % (e, url))
            print "%s when downloading img %s" % (e, url)
            return False

    def run(self):
        self.retrieve_image()


class CommentAbs(threading.Thread):
    """"""
    _url = '/r/answers/%s/comments'

    def __init__(self, tname):

        threading.Thread.__init__(self, name=tname)
        self.setDaemon(False)
        self.start()

    def run(self):
        """"""  
        _headers = gl.g_http_client.get_headers()
        while True:

            if gl.g_answer_comment_queue.empty() and gl.g_comment_exit:
                print "Task compeleted! thread %s exit"%self.name
                gl.g_http_client.logger.warning("Task compeleted! thread %s exit"%self.name)
                break
            else:
                try:
                    [quest, uri, count] = gl.g_answer_comment_queue.get(timeout=_GET_QUEUE_TIMEOUT)
                except Queue.Empty:
                    print 'timeout when get comment in %s thread'%self.name
                    gl.g_http_client.logger.warning('timeout when get comment in %s thread'%self.name)
                    continue
                _headers['Referer'] = gl.g_http_client.get_host() + quest
                cur_page = 1
                while count > 0:
                    ret = self.get_comment(quest, uri, cur_page, _headers)
                    count -= ZhihuHtmlParser.CommentParser.MAX_COMMENT_PER_PAGE
                    cur_page += 1
            time.sleep(_COMMET_INTERVAL)

    @classmethod
    def get_comment(cls, quest, uri, page, headers):
        """
        quest is the code of question , such as /question/12345678
        uri is the code of answer, such as 16202962"""
        if page > 1:
            url = gl.g_http_client.get_host() + cls._url%uri + '?page=%s'%page      #'https://www.zhihu.com/r/answers/8720147/comments?page=2'
        else:
            url = gl.g_http_client.get_host() + cls._url%uri    #'https://www.zhihu.com/r/answers/8700893/comments'
        response = gl.g_http_client.get_html(url, header=headers)
        if response['errno'] != ErrorCode.HTTP_OK:
            gl.g_http_client.logger.warning("%s when get comment in %s"%(response['errno'],uri))
            print "%s when get comment at %s"%(response['errno'],uri)
            return ErrorCode.COMMENT_FAIL
        ret = ZhihuHtmlParser.CommentParser.ParserHtml(response['content'], uri, url)
        return ret


class UserAbs(threading.Thread):
    """"""
    def __init__(self, tname):
        """"""
        threading.Thread.__init__(self, name=tname)
        self.setDaemon(False)
        self.start()

    @classmethod
    def get_user(cls, user_url, headers):
        """
        :param user_url: /people/peng-quan-xin
        :return: ErrorCode
        """
        refer = gl.g_http_client.get_host() + user_url 
        headers['Referer'] = refer
        url = refer + '/about/'
        response = gl.g_http_client.get_html(url, header=headers)
        if response['errno'] != ErrorCode.HTTP_OK:
            gl.g_http_client.logger.warning('%s when visit %s'%(response['errno'], url))
        ret = ZhihuHtmlParser.PersonPageParser.ParserHtml(response['content'], user_url)
        return ret

    def run(self):
        """"""
        _headers = gl.g_http_client.get_headers()
        while True:
            try:
                if gl.g_user_queue.empty() and gl.g_usr_exit:
                    print 'Task compeleted, thread %s exit' % self.name
                    gl.g_http_client.logger.info('Task compeleted, thread %s exit' % self.name)
                    break
                try:
                    user_url = gl.g_user_queue.get(timeout=_GET_QUEUE_TIMEOUT)
                except Queue.Empty:
                    print 'timeout when get user url in %s thread'%self.name
                    gl.g_http_client.logger.warning('timeout when get user url in %s thread'%self.name)
                    continue

                ret = self.get_user(user_url, _headers)
                time.sleep(_USER_INTERVAL)
            except RuntimeError, e :
                gl.g_http_client.logger.warning(e)




