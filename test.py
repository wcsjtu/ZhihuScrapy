# -*- coding: utf-8 -*-

import re
import os
import json
from lxml import etree
from SpiderFrame import Global as gl
from SpiderFrame import ErrorCode

from SpiderFrame.Http import Client, SexTuple
from SpiderFrame.Local import Config, DataBase
from SpiderFrame.Rules import Rules
from SpiderFrame.Logger import ZhihuLog
from SpiderFrame.Html import Parser, StructData

log = ZhihuLog.creatlogger("test_frame")
zhihu_host = "https://www.zhihu.com"

def INT(String):
    """format string likes `14K` into 14000"""
    if 'K' in String:
        factor = int(String[:-1])
        return factor*1000
    else:
        return int(String)


class MyHttpClient(Client.HttpClient):
    """"""
    def __init__(self, host):
        super(MyHttpClient, self).__init__()
        self.url = host
        self.account = {'phone_num': '1**', 'password': '**', 'remember_me':"true", '_xsrf': '**'}
        if not self.login_success:            
            self.input_account()
            self.login()

    def _get_veri_code(self):
        """to get captcha"""
        url = "https://www.zhihu.com/captcha.gif?r=1462615220376&type=login"
        rqst = self.session.request('GET', url) 
        if rqst.status_code != ErrorCode.HTTP_OK:
            self.logger.error("Fail to get captcha!")
            return False
        else:
            captcha = open('captcha.gif','wb')
            captcha.write(rqst.content)
            captcha.close()
            return True

    def login(self):
        """"""
        if self.login_success: return True
        self.account['remember_me'] = "true" 
        uri = "/login/email" if 'email' in self.account else "/login/phone_num"
        login_url = self.url+uri
        #rqst = self.session.request('GET', self.url, headers=self.default_headers)    
        rqst = self.url_request('GET', self.url, None, None)
         
        login_counter = 0
        while login_counter <= self._MAX_LOGIN_LIMIT:       
            login_counter += 1  
            try:
                if 'Set-Cookie' in rqst.response_headers and '_xsrf' not in self.account:
                    self.account['_xsrf'] = re.findall("_xsrf=(.*?);", rqst.response_headers['Set-Cookie'])[0]  
                #rqst2 = self.session.request('POST', login_url, params=self.account, headers=self.default_headers)
                rqst2 = self.url_request("POST", login_url, self.account, None)
                ret_value = json.loads(rqst2.response[0])['r']
                if ret_value == 0:
                    self.logger.error('Succeed to login')
                    self.login_success = True
                    self._is_init = True    
                    login_counter = self._MAX_LOGIN_LIMIT
                    return True
                else:
                    ret = self._get_veri_code()
                    if not ret:continue
                    os.system("captcha.gif")
                    cap = raw_input('please input Captcha which showed in your screen\n')
                    self.account['captcha'] = cap
                    continue                        
            except (IndexError, KeyError), e:
                self.logger.error('Fail to login, reason is %s'%e)
                
        self.login_success = False
        self._is_init = True
        return False

    def input_account(self):
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
        self.account = {user_type:username, "password":password, 'remember_me':"true"}   


class Users(StructData.StructData):
    """"""
    _database_struct = [("name", "varchar(256)"),  ("gender", "char(2)"),  ("discription", "text"),  ("location", "text"), 
                        ("position", "text"),      ("business", "text"),   ("employ", "text"),       ("education", "text"),
                        ("sign", "text"),          ("followees", "int"),   ("followers", "int"),     ("upvote", "int"),
                        ("thanks", "int"),         ("asks", "int"),        ("answers", "int"),       ("papers", "int"),
                        ("collection", "int"),     ("public", "int"),      ("weibo","varchar(256)"), ("user_url", "varchar(256)", "primary key"),
                        ("avatar_url", "varchar(256)"), ("avatar_path", "varchar(256)")
                        ]

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
        self.avatar_path = avatar_url
        super(Users, self).__init__()
Users.register()


class Questions(StructData.StructData):
    """"""
    _database_struct = [("title", "varchar(256)"),  ("url", "int", "primary key")]

    def __init__(self, title, url):
        self.title = title
        self.url = url
        return super(Questions, self).__init__()
Questions.register()


class Answers(StructData.StructData):

    _database_struct = [("id", "int", "primary key") , ("date" ,"int"),  ("anonymous", "char(1)"),
                        ("user_url", "varchar(256)"),  ("user_name", "varchar(256)"), ("vote", "int"),  
                        ("comment_count",  "int"),  ("content", "mediumtext"),  ("img_urls", "text"),
                        ("extern_links", "text"),  ("img_folder", "varchar(256)"),
                        ("question_url", "int"),   ("answer_url", "int") 
                       ]

    def __init__(self,id,          #answer id
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
                 ):
        self.id = id
        self.date = date
        self.anonymous = is_anonymous
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
        return super(Answers, self).__init__()
Answers.register()


class Comments(StructData.StructData):
    """"""
    _database_struct = [("ID", "int", "primary key"), ("ReplyID", "int"), ("CommentBy", "text"),
                        ("Content", "text"), ("Supporters", "int"), ("answer_url", "int")]


    def __init__(self,
                 id, replyid, name, content, likesCount, answer_url):
        self.ID = id
        self.ReplyID = replyid
        self.CommentBy = name
        self.Content = content
        self.Supporters = likesCount
        self.answer_url = answer_url
        return super(Comments, self).__init__()
Comments.register()


class ZhihuRules(Rules.Rules):
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
    def ajax_rules(cls, sextp, rulefactor):
        """
        this function is used to generate parameters of next http request by ajax
        @params: sextp, instance of class HttpSextp. See .Http/SexTuple.py for detail 
                 rulefactor, instance of RuleFactor
        @return  this function must return sextp or None                                                            
        """
        try:
            if cls._qst_url.search(sextp.url):
                if rulefactor.count < cls.MAX_ANSWERS_PER_PAGE: 
                    log.warning('Achieve to the end of question %s'%sextp.url)
                    return None
                if not sextp.payloads is None:
                    offset = json.loads(sextp.payloads['params'])['offset']
                    url_token = re.findall('\d{8}', sextp.payloads['params'])[0]
                    sextp.payloads['params'] = sextp.payloads['params'].replace('%d}'%offset, '%d}'%(offset+10))
                    #ret = ['POST', sextp.url, sextp.payloads, sextp.request_headers]
                    pass
                else:
                    print "account in Rules: ", gl.g_http_client.account
                    url_token = re.findall(r'\d{8}', sextp.url)[0]
                    _xsrf = gl.g_http_client.account['_xsrf']
                    url_ = ''.join([gl.g_http_client.url, '/node/QuestionAnswerListV2'])
                    sextp.payloads = {'method':'next', 'params':'{"url_token":%s,"pagesize":10,"offset":20}'%url_token, '_xsrf':'%s'%_xsrf}
                    #ret = ['POST', url_, sextp.payloads, {'Referer': 'https://www.zhihu.com/question/%s'%url_token,"Host": "www.zhihu.com", 'Cookie': _xsrf}]
                    sextp.request_headers = {'Referer': 'https://www.zhihu.com/question/%s'%url_token,"Host": "www.zhihu.com", 'Cookie': _xsrf}

            elif cls._cmt_url.search(sextp.url):
                if rulefactor.count < cls.MAX_COMMENT_PER_PAGE: 
                    log.warning('Achieve to the end of comments in answser %s'%sextp.url)
                    return None
                if not sextp.payloads is None:
                    sextp.payloads['page'] += 1
                    #ret = ["GET", sextp.url, sextp.payloads, sextp.request_headers]
                else:
                    sextp.payloads = {'page':2}
                    #ret = ["GET", sextp.url, sextp.payloads, sextp.request_headers]

            elif cls._bing_url.search(sextp.url):
                if rulefactor.count < cls.QUESTION_PER_PAGE_BING: 
                    log.warning('Achieve to the end of bing cache')
                    return None
                sextp.payloads['first'] += cls.QUESTION_PER_PAGE_BING
                #ret = ["GET", sextp.url, sextp.payloads, None]
            sextp.response = None
            sextp.response_headers = None
            return sextp
        except Exception, e:
            print e 
            log.warning('ajax rule error, url is %s, payloads is %s'%(sextp.url, str(sextp.payloads).decode('unicode-escape')))
        return None

    @classmethod
    def filt_rules(cls, sextp, rulefactor):
        return None


class ZhihuPaser(Parser.ParserProc):
    """parse kinds of html"""
    
    
    def __init__(self, name_ = 'Parser', fk=True):

        self._vuser = Users('','','','','','','','','',0,0,0,0,0,0,0,0,0,'','','')     #used for judging whether the user with certain user_url                                                                                           #is existed in database or not.
        super(ZhihuPaser, self).__init__(name_)
        if fk:
            self.start()
        
    
    @ZhihuRules.filter
    def parse_bing(self, sextp, proc_queue):
        """
        parse question url and title from html returned by Bing
        @params: sextp, instance of class SexTuple.HttpSextp
                 proc_queue, dict. queues between two different process to share memeories. Its format is {'html_queue': gl.g_html_queue,
                                                                                                           'url_queue': gl.g_url_queue,
                                                                                                           'data_queue': gl.g_data_queue,
                                                                                                           'static_rc': gl.g_static_rc}      
        @return: if method is decorated by `ajax` decorator, an integer type value must be returned. If not, an AssertionException will be raised.
                 if method is decorated by 'filt' decorator, a list, whose format is [[method, url, payloads, headers], ...] must be returned.
                 if these is no decorator, return None.
                 so, this method return an integer value, which means the count of entrie in current html[0]. It will determine the action of ajax rule
        """
        questions = re.findall(r'<h2><a href="(http(s|)://www.zhihu.com/question/\d{8})".+?>(.+?)</a></h2>', sextp.response[0])
        question_count = len(questions)
        for node in questions:
            try:
                url_ = node[0]
                uri = re.findall('\d{8}', url_)[0]
                title = node[2].decode('utf-8')

                q = Questions(title, int(uri))
                #gl.g_data_queue.put(q)
                proc_queue['data_queue'].put(q)
                #isexisted = gl.g_database.is_existed(q)
                #if not isexisted: 
                #gl.g_url_queue.put(['GET', url_, payloads, headers])  
                temp = SexTuple.HttpSextp(url_, "GET", None, None, None)
                proc_queue['url_queue'].put(temp)    
            except Exception,e :
                log.error('%s when parse bing html'%e)
        return Rules.RuleFactor(question_count, None)
    
            
    @ZhihuRules.filter    
    def parse_qstn(self, sextp, proc_queue):
        """
        parse question url and title from html returned by Bing
        @params: sextp, instance of class SexTuple.HttpSextp
                 proc_queue, dict. queues between two different process to share memeories. Its format is {'html_queue': gl.g_html_queue,
                                                                                                           'url_queue': gl.g_url_queue,
                                                                                                           'data_queue': gl.g_data_queue,
                                                                                                           'static_rc': gl.g_static_rc}      
        @return: if method is decorated by `ajax` decorator, an integer type value must be returned. If not, an AssertionException will be raised.
                 if method is decorated by 'filt' decorator, a list, whose format is [[method, url, payloads, headers], ...] must be returned.
                 if these is no decorator, return None.
                 so, this method return an integer value, which means the count of entrie in current html[0]. It will determine the action of ajax rule
        """
        html = sextp.response
        url = sextp.url
        headers = sextp.request_headers
        method = sextp.method
        payloads = sextp.payloads


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
                log.error('%s when parse %s'%(e, url))
                all_answer_counts = None
                answer_nodes = []
        answer_counts = len(answer_nodes)
        
        if answer_counts == 0 and u'"msg": []' not in html[0]:
            log.error("no answer in question page, chech xpath of answer_nodes")
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
                                                               
                answer = Answers(id, date, is_anonymous, user_url, user_name, vote, comment_count, 
                                     content, '\n'.join(img_urls), '\n'.join(ext_links), user_url, quest_url, answer_url)

                self._vuser.user_url = user_url                
                isexisted = gl.g_database.is_existed(answer)
                if not isexisted:
                    #gl.g_data_queue.put(answer)
                    proc_queue['data_queue'].put(answer)
                if  hasimg:
                    rc = SexTuple.HttpSrsc(img_urls, None, ''.join([gl.g_storage_path, user_url]))
                    proc_queue['static_rc'].put(rc)
                    

                if not is_anonymous and not isexisted:
                    if not gl.g_database.is_existed(self._vuser):
                        usr = SexTuple.HttpSextp(''.join([zhihu_host, user_url, '/about/']),
                                                  "GET",
                                                  {'Referer': zhihu_host+user_url},
                                                  None, None, None
                                                  )
                        proc_queue['url_queue'].put(usr)

                if comment_count is not 0 and not isexisted:
                    cmnt = SexTuple.HttpSextp(''.join([zhihu_host, '/r/answers/', str(answer_url), '/comments']), 
                                              "GET", 
                                              {'Referer': url},
                                              None, None, None
                                             )
                    proc_queue['url_queue'].put(cmnt)

            except Exception, e:
                print '%s when parser %s'%(e, quest_url)
                log.warning('%s when parser %s'%(e, quest_url))

        return Rules.RuleFactor(answer_counts, None)
            
    def parse_usr(self, sextp, proc_queue):
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
        html = sextp.response
        url = sextp.url
        headers = sextp.request_headers
        method = sextp.method
        payloads = sextp.payloads
        
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
            temp = SexTuple.HttpSrsc([avatar_url], {'Referer':'%s'%url}, os.path.join(gl.g_storage_path , usr_url))
            gl.g_static_rc.put(temp)
        
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
            user = Users(name, g, discr, location, position, business, employ, education,
                             sign, int(followees), int(followers), int(upvote), int(tnks), 
                             int(quest), int(answ), int(post), int(collect), int(logs), weibo_url, usr_url, avatar_url)
            #gl.g_data_queue.put(user)
            proc_queue['data_queue'].put(user)
        except Exception, e:
            log.error("%s when parser %s"%(e, url))
            gl.g_fail_url.warning(url)
        return None
        
    @ZhihuRules.filter
    def parse_cmnt(self, sextp, proc_queue):
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
        html = sextp.response
        url = sextp.url
        headers = sextp.request_headers
        method = sextp.method
        payloads = sextp.payloads

        try:
            comment_list = json.loads(html[0])['data']
            comment_counts = len(comment_list)
            answer_code = int(re.findall(r'answers/(\d+?)/comments', url)[0])   # format is 20990037
        except Exception, e:
            log.error('%s when parse comment %s'%(e, sextp.url))
            print '%s when parse comment %s'%(e, sextp.url)
            gl.g_fail_url.warning(url)
            return RuleFactor(ErrorCode.COMMENT_FAIL, None)
        for comment in comment_list:
            try:
                id = int(comment['id'])
                replyid = int(comment['inReplyToCommentId'])
                name = comment['author']['name']
                content = comment['content']
                likesCount = int(comment['likesCount'])
                c = Comments(id, replyid, name, content, likesCount, answer_code)
                #gl.g_data_queue.put(c)
                proc_queue['data_queue'].put(c)
            except Exception,e:
                log.error("%s when parser %s"%(e, answer_code))            
        return Rules.RuleFactor(comment_counts, None)

ZhihuPaser.add_map(ZhihuPaser.parse_bing, re.compile(r'cn.bing.com'))
ZhihuPaser.add_map(ZhihuPaser.parse_cmnt, re.compile(r'/r/answers/\d+?/comments'))
ZhihuPaser.add_map(ZhihuPaser.parse_qstn, re.compile(r'/question/\d{8}'))
ZhihuPaser.add_map(ZhihuPaser.parse_usr, re.compile(r'about'))

#
#

def test_parser():
    gl.g_http_client.account = {'email': 'aaaa@xxx.com', 'password': '123123', '_xsrf': 'asdfasdfasdfsafdgasdfsfdgasdfsfdg'}
    DataBase.DataBase.set_intval(30)
    import os
    path = os.getcwd()
    with open(path + '/test/bing.html', 'r') as f:
        bing_html = [f.read()]
        sextp_bing = SexTuple.HttpSextp("https://cn.bing.com/search", "GET", None, {"q": "site:zhihu.com/question", "first":1}, bing_html, None)
        gl.g_html_queue.put(sextp_bing)

    with open(path + "/test/question.html", 'r') as f:
        question_html = [f.read()]
        sextp_qst = SexTuple.HttpSextp("https://www.zhihu.com/question/33500236", "GET", None, None, question_html, None)
        gl.g_html_queue.put(sextp_qst)

    with open(path + "/test/user.html", 'r') as f:
        user_html = [f.read()]
        sextp_usr = SexTuple.HttpSextp("https://www.zhihu.com/people/cong-wei-79-45/about", "GET", "https://www.zhihu.com/people/cong-wei-79-45/", None, user_html, None)       
        gl.g_html_queue.put(sextp_usr)

    parser = ZhihuPaser(fk=False)
    parser.work(parser._args[0])


gl.g_http_client = MyHttpClient(zhihu_host)
gl.g_database = DataBase.DataBase()

def main():
    import time
    bing_start = SexTuple.HttpSextp('https://cn.bing.com/search', "GET", None, {'q':u'site:zhihu.com/question', 'first':1}, None, None)
    qst_start = SexTuple.HttpSextp('https://www.zhihu.com/question/39677202', "GET", None, None, None, None)
    cmt_start = SexTuple.HttpSextp('https://www.zhihu.com/r/answers/31504680/comments', "GET", None, None, None, None)
    usr_start = SexTuple.HttpSextp('https://www.zhihu.com/people/wang-su-yang-43/about', "GET", None, None, None, None)

    gl.g_url_queue.put(bing_start)
    gl.g_url_queue.put(qst_start)
    gl.g_url_queue.put(cmt_start)
    gl.g_url_queue.put(usr_start)

    htmlclient = Client.HtmlClient('downloader')
    static_rcclient = Client.StaticClient('image')

    parser = ZhihuPaser()
    while True:
        print 'url queue:  ', gl.g_url_queue.qsize(), "downloader: ", htmlclient.isAlive()
        print 'html queue: ', gl.g_html_queue.qsize(), "parser: ", parser.is_alive()
        print 'data queue: ', gl.g_data_queue.qsize(), "database: ", gl.g_database.isAlive()
        print 'image queue:', gl.g_static_rc.qsize() , "image: ", static_rcclient.isAlive()
        print '=========================================\n\n'
        time.sleep(3)    



if __name__ == "__main__":


    main()


    print zhihu_host
