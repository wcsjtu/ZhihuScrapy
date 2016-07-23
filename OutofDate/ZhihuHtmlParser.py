# -*- coding: utf-8 -*-


from functools import wraps
import multiprocessing
from multiprocessing import Manager
import os
import re
import json
import ZhihuLog
import ErrorCode
import Global as gl
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

try:
    from lxml import etree
except ImportError:
    print 'Fail to import lib `lxml`'
    import sys
    sys.exit()

_g_html_logger = ZhihuLog.creatlogger(__name__)


class ZhihuUser(object):

    """"""
    def __init__(self, name, gender, discr, location, position, business, employ, education,
                 sign, followees, followers, upvote, tnks, quest, answ, post, collect, logs, weibo_url, usr_url, avatar_url):
        """"""
        self.name = name
        self.gender = gender
        self.discription = discr
        self.location = location
        self.position = position
        self.business = business
        self.employ = employ
        self.education = education
        self.sign = sign
        self.followees = followees
        self.followers = followers
        self.upvote = upvote
        self.thanks = tnks
        self.asks = quest
        self.answers = answ
        self.papers = post
        self.collection = collect
        self.public = logs
        self.weibo = weibo_url
        self.user_url = usr_url
        self.avatar_url = avatar_url


class ZhihuQuestion(object):
    """"""
    def __init__(self, url, title):
        """"""
        self.question_url = url
        self.question_title = title


class ZhihuAnswer(object):
    """"""
    def __init__(self, id,          #answer id
                 date,              #date when the answer created
                 is_anonymous,
                 user_url,
                 user_name,         #user's nickname
                 vote,
                 comments_count,
                 content,
                 img_urls,          #list of img urls
                 extern_links,
                 img_folder,        #folder to save imgs
                 question_url,      # question which this answer belonged to
                 answer_url,
                 has_img            #this answer has image?
                 ):
        """"""
        self.id = id
        self.date = date
        self.is_anonymous = is_anonymous
        self.user_url = user_url
        self.user_name = user_name
        self.vote = vote
        self.comment_count = comments_count
        self.content = content
        self.img_urls = img_urls
        self.extern_links = extern_links
        self.img_folder = img_folder
        self.question_url = question_url
        self.answer_url = answer_url
        self.has_img = has_img


class ZhihuComment(object):
    """"""
    def __init__(self, id, replyid, name, content, likesCount, answer_url):

        self.id = id
        self.replyid = replyid
        self.comment_by = name
        self.content = content
        self.likes = likesCount
        self.answer_url = answer_url

        
def INT(String):
    """format string likes `14K` into 14000"""
    if 'K' in String:
        factor = int(String[:-1])
        return factor*1000
    else:
        return int(String)


class Rules(object):
    """base class for specified rules"""

    @classmethod
    def ajax_rules(cls, method, url, payloads, headers, stop_flag):
        """
        this function is used to generate parameters of next http request by ajax
        @params: method, http method
                 url, used to identify different ajax request
                 payloads, sheetlist of http request
                 headers, http header
                 stop_flag, self-define type, used to stop the ajax of this url
                 kwargs, just for extension 
        @return  this function must return [method, url, payloads, headers] or None
        """
        raise NotImplementedError('method `ajax_rules` must be override in child class')
        
    @classmethod
    def filt_rules(cls, urls, *args, **kwargs):
        """
        this function is used to filt the urls in html by cerntain rules
        @params:
                urls, list of url
                args and kwargs are used for extension
        @return this function must return [[url, payloads, headers], [url, payloads, headers], ....]
        """
        raise NotImplementedError('method `filt_rules` must be override in child class')

    @classmethod
    def ajax(cls, func):
        """"""
        @wraps(func)
        def wrapper(obj, html, method, url, payloads, headers, queue_dict):
            ret = func(obj, html, method, url, payloads, headers, queue_dict)
            assert isinstance(ret, int)
            next = cls.ajax_rules(method, url, payloads, headers, ret)
            return next
        return wrapper

    @classmethod
    def filter(cls, func):
        """"""
        @wraps(func)
        def wrapper(obj, html, urls, payloads, headers, *args, **kwargs):
            ret = func(obj, html, urls, payloads, headers)
            assert isinstance(ret, list)
            ret = cls.filt_rules(urls, *args, **kwargs)
            return ret
        return wrapper


class ParserProc(multiprocessing.Process):
    """base class for parser process"""
    def __init__(self, name_ ):
        super(ParserProc, self).__init__(name = name_)
        self.daemon = True
        self.exit = False
        self._args = ({'html_queue': gl.g_html_queue,
                        'url_queue': gl.g_url_queue,
                        'data_queue': gl.g_data_queue,
                        'static_rc': gl.g_static_rc},
                     )
        self._target = self.work


    def work(self, proc_queue):
        """work function in this process"""
        raise NotImplementedError('method `work` must be override in child class')

#if a function is decorated by Rules.ajax, the return value must be integer!!
class ZhihuRules(Rules):
    """rules to filt url in html or yield ajax url and payloads"""

    
    _qst_url = re.compile(r'/question/\d{8}')
    _cmt_url = re.compile(r'/r/answers/\d+?/comments')
    _bing_url = re.compile(r'cn.bing.com')
    _usr_url = re.compile(r'about')

    _BING_MAX_ITEM = 10
    MAX_ANSWERS_PER_PAGE = 10      #max answers per page
    MAX_COMMENT_PER_PAGE = 30
    QUESTION_PER_PAGE_BING = 10

    def __init__(self, *args, **kwargs):
        return super(ZhihuRules, self).__init__(*args, **kwargs)

    @classmethod
    def ajax_rules(cls, method, url, payloads, headers, stop_flag):
        """
        this function is used to generate parameters of next http request by ajax
        @params: method, http method
                 url, used to identify different ajax request
                 payloads, sheetlist of http request
                 headers, http header
                 stop_flag, self-define type, used to stop the ajax of this url
                 kwargs, just for extension 
        @return  this function must return [method, url, payloads, headers] or None
                                                            {}
        """
        try:
            if cls._qst_url.search(url):
                if stop_flag < cls.MAX_ANSWERS_PER_PAGE: 
                    _g_html_logger.warning('Achieve to the end of question %s'%url)
                    return None
                if not payloads is None:
                    offset = json.loads(payloads['params'])['offset']
                    url_token = re.findall('\d{8}', payloads['params'])[0]
                    payloads['params'] = payloads['params'].replace('%d}'%offset, '%d}'%(offset+10))
                    ret = ['POST', url, payloads, headers]
                    pass
                else:
                    url_token = re.findall(r'\d{8}', url)[0]
                    _xsrf = gl.g_http_client.account['_xsrf']
                    url_ = ''.join([gl.g_zhihu_host, '/node/QuestionAnswerListV2'])
                    payloads = {'method':'next', 'params':'{"url_token":%s,"pagesize":10,"offset":20}'%url_token, '_xsrf':'%s'%_xsrf}
                    ret = ['POST', url_, payloads, {'Referer': 'https://www.zhihu.com/question/%s'%url_token,"Host": "www.zhihu.com", 'Cookie': _xsrf}]

            elif cls._cmt_url.search(url):
                if stop_flag < cls.MAX_COMMENT_PER_PAGE: 
                    _g_html_logger.warning('Achieve to the end of comments in answser %s'%url)
                    return None
                if not payloads is None:
                    payloads['page'] += 1
                    ret = ["GET", url, payloads, headers]
                else:
                    payloads = {'page':2}
                    ret = ["GET", url, payloads, headers]

            elif cls._bing_url.search(url):
                if stop_flag < cls.QUESTION_PER_PAGE_BING: 
                    _g_html_logger.warning('Achieve to the end of bing cache')
                    return None
                payloads['first'] += cls.QUESTION_PER_PAGE_BING
                ret = ["GET", url, payloads, None]
            return ret
        except Exception, e:
            print e 
            _g_html_logger.warning('ajax rule error, url is %s, payloads is %s'%(url, str(payloads).decode('unicode-escape')))
        return None

    @classmethod
    def filt_rules(cls, urls, *args, **kwargs):
        pass



class ZhihuPaser(ParserProc):
    """parse kinds of html"""
    
    
    def __init__(self, name_ = 'Parser'):

        self._vuser = ZhihuUser('','','','','','','','','',0,0,0,0,0,0,0,0,0,'','','')     #used for judging whether the user with certain user_url                                                                                           #is existed in database or not.
        super(ZhihuPaser, self).__init__(name_)
        self.start()
        
    
    @ZhihuRules.ajax
    def parse_bing(self, html, method, url, payloads, headers, proc_queue):
        """
        parse question url and title from html returned by Bing
        @params: html, list. it has only one element, and type(html) is list, type(html[0]) is string or unicode
                 method, string. http method, one of 'GET', 'POST', 'PUT', 'OPTION', 'HEAD'
                 url, string. resource's url, without any query parameters, such as 'https://cn.bing.com/search', rather than 'https://cn.bing.com/search?q=keywords'
                 payloads, dict or None. http payloads
                 headers, dict or None.  http request headers
                 proc_queue, dict. queues between two different process to share memeories. Its format is {'html_queue': gl.g_html_queue,
                                                                                                           'url_queue': gl.g_url_queue,
                                                                                                           'data_queue': gl.g_data_queue,
                                                                                                           'static_rc': gl.g_static_rc}      
        @return: if method is decorated by `ajax` decorator, an integer type value must be returned. If not, an AssertionException will be raised.
                 if method is decorated by 'filt' decorator, a list, whose format is [[method, url, payloads, headers], ...] must be returned.
                 if these is no decorator, return None.
                 so, this method return an integer value, which means the count of entrie in current html[0]. It will determine the action of ajax rule
        """
        questions = re.findall(r'<h2><a href="(http(s|)://www.zhihu.com/question/\d{8})".+?>(.+?)</a></h2>', html[0])
        question_count = len(questions)
        for node in questions:
            try:
                url_ = node[0]
                uri = re.findall('\d{8}', url_)[0]
                title = node[2].decode('utf-8')

                q = ZhihuQuestion(int(uri), title)
                #gl.g_data_queue.put(q)
                proc_queue['data_queue'].put(q)
                isexisted = gl.g_zhihu_database.is_existed(q)
                #if not isexisted: 
                #gl.g_url_queue.put(['GET', url_, payloads, headers])       
                proc_queue['url_queue'].put(['GET', url_, None, headers])    
            except Exception,e :
                _g_html_logger.error('%s when parse bing html'%e)
        return question_count
            
    @ZhihuRules.ajax    
    def parse_qstn(self, html, method, url, payloads, headers, proc_queue):
        """
        parse question url and title from html returned by Bing
        @params: html, list. it has only one element, and type(html) is list, type(html[0]) is string or unicode
                 method, string. http method, one of 'GET', 'POST', 'PUT', 'OPTION', 'HEAD'
                 url, string. resource's url, without any query parameters, such as 'https://cn.bing.com/search', rather than 'https://cn.bing.com/search?q=keywords'
                 payloads, dict or None. http payloads
                 headers, dict or None.  http request headers
                 proc_queue, dict. queues between two different process to share memeories. Its format is {'html_queue': gl.g_html_queue,
                                                                                                           'url_queue': gl.g_url_queue,
                                                                                                           'data_queue': gl.g_data_queue,
                                                                                                           'static_rc': gl.g_static_rc}      
        @return: if method is decorated by `ajax` decorator, an integer type value must be returned. If not, an AssertionException will be raised.
                 if method is decorated by 'filt' decorator, a list, whose format is [[method, url, payloads, headers], ...] must be returned.
                 if these is no decorator, return None.
                 so, this method return an integer value, which means the count of entrie in current html[0]. It will determine the action of ajax rule
        """
        AJAX = True if '"r":0' in html[0] else False #specified whether the html has complete html structure ,
                                                     #or has only partial elements, such as json or xml
                                                     #if AJAX==False, means the html[0] has all elements of an complete html page
        
        quest_url = int(re.findall(r'(\d{8})', url)[0])
        if not AJAX:
            parse = etree.HTML(html[0])
            all_answer_counts_node = parse.xpath('//h3[@id="zh-question-answer-num"]')
            all_answer_counts = int(all_answer_counts_node[0].attrib['data-num']) if len(all_answer_counts_node) else 0
            answer_nodes = parse.xpath("//div[@class='zm-item-answer  zm-item-expanded']")
        else:
            try:
                answer_nodes = json.loads(html[0])['msg']
                all_answer_counts = None
            except ValueError, e :
                _g_html_logger.error('%s when parse %s'%(e, url))
                all_answer_counts = None
                answer_nodes = []
        answer_counts = len(answer_nodes)
        
        if answer_counts == 0 and u'"msg": []' not in html[0]:
            _g_html_logger.error("no answer in question page, chech xpath of answer_nodes")
            gl.g_fail_url.warning(url)
            return ErrorCode.LIST_EMPTY_ERROR
                    
        for node in answer_nodes:
            try:
                if AJAX:
                    node = etree.HTML(node).xpath('body')[0].xpath('div')[0]
                id = int(node.attrib['data-aid'])
                date = int(node.attrib['data-created'])
                vote = INT(node.xpath('div/button/span[@class="count"]')[0].text)               
                comments = node.xpath('div/div/a[@class="meta-item toggle-comment js-toggleCommentBox"]')[0].xpath('string(.)')
                comments_count = ''.join(comments)[1:-4]   ##\n62 条评论
                comment_count = INT(comments_count) if comments_count != '' else 0
                content_block = node.xpath('div/div[@class="zm-editable-content clearfix"]')[0]
                content = ''.join(content_block.xpath('string(.)'))
                # abstract image links and tag the hasimg attribute
                img_nodes = content_block.xpath('img')
                img_urls = []
                for img in img_nodes:
                    try:
                        url = img.attrib['data-original']
                        if not url.startswith('http'): continue
                    except KeyError:
                        url = img.attrib['src']
                        if not url.startswith('http'): continue
                    img_urls.append(url)
                # img_urls = [img.attrib['data-original'] for img in img_nodes ]
                
                hasimg = False if img_urls == [] else True

                # abstract user link and name, then tag the anonymous attribute
                user_link_node = node.xpath('div/div/a[@class="author-link"]')    
                if len(user_link_node) != 0:
                    user_url = user_link_node[0].attrib['href']
                    is_anonymous = False
                    user_name = user_link_node[0].text
                else:
                    user_url = '/people/anonymous/'
                    is_anonymous = True
                    user_name = 'anonymous'

                # abstract external link
                external_link_nodes = content_block.xpath('a[@class=" wrap external"]')                
                ext_links = [link.attrib['href'] for link in external_link_nodes ]
                answer_url = int(node.xpath("link")[0].attrib['href'].split('/')[4]) # 44370648
                                                               
                answer = ZhihuAnswer(id, date, is_anonymous, user_url, user_name, vote, comment_count, 
                                     content,img_urls, ext_links, user_url, quest_url, answer_url, hasimg)

                self._vuser.user_url = user_url                
                isexisted = gl.g_zhihu_database.is_existed(answer)
                if not isexisted:
                    #gl.g_data_queue.put(answer)
                    proc_queue['data_queue'].put(answer)
                if  hasimg:
                    rc = [img_urls, None, gl.g_storage_path + user_url]
                    proc_queue['static_rc'].put(rc)
                    

                if not is_anonymous and not isexisted:
                    if not gl.g_zhihu_database.is_existed(self._vuser):
                        proc_queue['url_queue'].put(['GET', 
                                                     ''.join([gl.g_zhihu_host, user_url, '/about/']),
                                                     None, 
                                                     {'Referer': gl.g_zhihu_host+user_url}
                                                   ])

                if comment_count is not 0 and not isexisted:
                    proc_queue['url_queue'].put(['GET', 
                                                 ''.join([gl.g_zhihu_host, '/r/answers/', str(answer_url), '/comments']),
                                                 None,
                                                 {'Referer': url}
                                               ])

            except Exception, e:
                print '%s when parser %s'%(e, quest_url)
                _g_html_logger.warning('%s when parser %s'%(e, quest_url))

        return answer_counts
    
        
    def parse_usr(self, html, method, url, payloads, headers, proc_queue):
        """
        parse question url and title from html returned by Bing
        @params: html, list. it has only one element, and type(html) is list, type(html[0]) is string or unicode
                 method, string. http method, one of 'GET', 'POST', 'PUT', 'OPTION', 'HEAD'
                 url, string. resource's url, without any query parameters, such as 'https://cn.bing.com/search', rather than 'https://cn.bing.com/search?q=keywords'
                 payloads, dict or None. http payloads
                 headers, dict or None.  http request headers
                 proc_queue, dict. queues between two different process to share memeories. Its format is {'html_queue': gl.g_html_queue,
                                                                                                           'url_queue': gl.g_url_queue,
                                                                                                           'data_queue': gl.g_data_queue,
                                                                                                           'static_rc': gl.g_static_rc}      
        @return: if method is decorated by `ajax` decorator, an integer type value must be returned. If not, an AssertionException will be raised.
                 if method is decorated by 'filt' decorator, a list, whose format is [[method, url, payloads, headers], ...] must be returned.
                 if these is no decorator, return None.
                 so, this method return None
        """
        parser = etree.HTML(html[0])
        try:
            node = parser.xpath("//div[@class='zm-profile-header ProfileCard']")
            try:
                [main_block, preformance, ask] = node[0]    #may 4
            except ValueError:
                [main_block, _, preformance, ask] = node[0]
            [top, body] = main_block.xpath('div')    
            #top in content
            weibo_node = top.xpath('div[@class="weibo-wrap"]/a')
            name_and_disr_node = top.xpath('div[@class="title-section ellipsis"]')[0]
        
            weibo_url = weibo_node[0].attrib['href'] if weibo_node != [] else ""
            name_node = name_and_disr_node.xpath('a[@class="name"]')[0]
            name = name_node.text ####
            usr_url = name_node.attrib['href'] ####
    
            discr_node = name_and_disr_node.xpath('span[@class="bio"]')
            discr = discr_node[0].text if discr_node != [] else "" ####
    
            # then body content
            avatar_node = body.xpath('img[@class="Avatar Avatar--l"]')[0]
            avatar_url = avatar_node.attrib['srcset'].split(' ')[0]  ####

            gl.g_static_rc.put([ [avatar_url], 
                                {'Referer':'%s'%url},  
                                os.path.join(gl.g_storage_path , usr_url)])
        
            total_profile = body.xpath('div/div/div[@class="items"]')[0]
        
            profile_node = total_profile.xpath('div[@class="item editable-group"]/span[@class="info-wrap"]')[0]
            location_node = profile_node.xpath('span[@class="location item"]')
            location = location_node[0].attrib['title'] if location_node != [] else ""   ####
            business_node = profile_node.xpath('span[@class="business item"]')
            business = business_node[0].attrib['title'] if business_node != [] else ""   ####
            gender_node = profile_node.xpath('span[@class="item gender"]/i')
            gender = gender_node[0].attrib['class'] if gender_node != [] else 'unkown'
            gender = True if 'female' in gender else False                               ####
        
            employ_node = total_profile.xpath('div/span/span[@class="employment item"]')
            employ = employ_node[0].attrib['title'] if employ_node != [] else ""         ####
            position_node = total_profile.xpath('div/span/span[@class="position item"]')
            position = position_node[0].attrib['title'] if position_node != [] else ""      ####
    
            education_node = total_profile.xpath('div/span/span[@class="education item"]')
            education = education_node[0].attrib['title'] if education_node != [] else ''  ####

            sign_node = total_profile.xpath('following-sibling::*[1]/span/span/span[@class="content"]')
            sign = ''.join(sign_node[0].xpath('string(.)')) if sign_node != [] else ""    ####
            #preformance
            [upvote_node, tnks_node] = preformance.xpath('div/span/strong')
            upvote = int(upvote_node.text) if upvote_node != [] else 0    ####     integer
            tnks = int(tnks_node.text) if tnks_node != [] else 0          ####
            #ask
            [_, quest, answ, post, collect, logs] = [item.xpath('span')[0].text for item in ask.xpath('a')]  ####
            #followee and follower
            f = node[0].xpath('//div[@class="zm-profile-side-following zg-clear"]/a[@class="item"]')
            [followees, followers] = [re.findall('\d+', ''.join(i.xpath('string(.)')))[0] for i in f]

            g = u'妹子' if gender else u'汉子'
            user = ZhihuUser(name, g, discr, location, position, business, employ, education,
                             sign, int(followees), int(followers), int(upvote), int(tnks), 
                             int(quest), int(answ), int(post), int(collect), int(logs), weibo_url, usr_url, avatar_url)
            #gl.g_data_queue.put(user)
            proc_queue['data_queue'].put(user)
        except Exception, e:
            _g_html_logger.error("%s when parser %s"%(e, url))
            gl.g_fail_url.warning(url)
        return None
        
    @ZhihuRules.ajax
    def parse_cmnt(self, html, method, url, payloads, headers, proc_queue):
        """
        parse question url and title from html returned by Bing
        @params: html, list. it has only one element, and type(html) is list, type(html[0]) is string or unicode
                 method, string. http method, one of 'GET', 'POST', 'PUT', 'OPTION', 'HEAD'
                 url, string. resource's url, without any query parameters, such as 'https://cn.bing.com/search', rather than 'https://cn.bing.com/search?q=keywords'
                 payloads, dict or None. http payloads
                 headers, dict or None.  http request headers
                 proc_queue, dict. queues between two different process to share memeories. Its format is {'html_queue': gl.g_html_queue,
                                                                                                           'url_queue': gl.g_url_queue,
                                                                                                           'data_queue': gl.g_data_queue,
                                                                                                           'static_rc': gl.g_static_rc}      
        @return: if method is decorated by `ajax` decorator, an integer type value must be returned. If not, an AssertionException will be raised.
                 if method is decorated by 'filt' decorator, a list, whose format is [[method, url, payloads, headers], ...] must be returned.
                 if these is no decorator, return None.
                 so, this method return an integer value, which means the count of entrie in current html[0]. It will determine the action of ajax rule
        """

        try:
            comment_list = json.loads(html[0])['data']
            comment_counts = len(comment_list)
            answer_code = int(re.findall(r'answers/(\d+?)/comments', url)[0])   # format is 20990037
        except Exception, e:
            _g_html_logger.error('%s when parse comment %s'%(e, answer_code))
            print '%s when parse comment %s'%(e, answer_code)
            gl.g_fail_url.warning(url)
            return ErrorCode.COMMENT_FAIL
        for comment in comment_list:
            try:
                id = int(comment['id'])
                replyid = int(comment['inReplyToCommentId'])
                name = comment['author']['name']
                content = comment['content']
                likesCount = int(comment['likesCount'])
                c = ZhihuComment(id, replyid, name, content, likesCount, answer_code)
                #gl.g_data_queue.put(c)
                proc_queue['data_queue'].put(c)
            except Exception,e:
                _g_html_logger.error("%s when parser %s"%(e, answer_code))            
        return comment_counts


    def dispatch(self, ele, proc_queue):
        """fecth data from html queue and put data to database queue, put url to url queue"""
        ret = None
        if ZhihuRules._qst_url.search(ele[2]):
            ret = self.parse_qstn(ele[0], ele[1], ele[2], ele[3], ele[4], proc_queue)
        elif ZhihuRules._cmt_url.search(ele[2]):
            ret = self.parse_cmnt(ele[0], ele[1], ele[2], ele[3], ele[4], proc_queue)
        elif ZhihuRules._bing_url.search(ele[2]):
            ret = self.parse_bing(ele[0], ele[1], ele[2], ele[3], ele[4], proc_queue)
        elif ZhihuRules._usr_url.search(ele[2]) :
            ret = self.parse_usr(ele[0], ele[1], ele[2], ele[3], ele[4], proc_queue)
        if ret is not None:
            proc_queue['url_queue'].put(ret)


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
                if url_queue.empty() and html_queue.empty() and self.exit:
                    print 'task completed! process %s exit'%self.name
                    os._exit(0) 
                ele = html_queue.get()
                self.dispatch(ele, proc_queue) 
        except Exception, e :
            _g_html_logger.error(e)         
        os._exit(0) 


    def quit(self):
        """force process to exit"""
        self.exit = True



#if __name__ == "__main__":

#    print 1
#    class A():
#        @ZhihuRules.ajax
#        def f(self, html, method, url, payloads, headers):
#            return 31

#    a = A()

#    a.f('', 'GET', 'https://www.zhihu.com/r/answers/8720147/comments', {}, {})
