# -*- coding: utf-8 -*-


import Global
import re
import json
import ZhihuLog
import ErrorCode
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

try:
    from lxml import etree
except ImportError:
    print 'Fail to import lib `lxml`'

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
    def __init__(self, url, title, keywords):
        """"""
        self.question_url = url
        self.question_title = title
        self.keywords = keywords


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




class Paser(object):
    """parse kinds of html"""
    
    _QUESTION_PER_PAGE_BING = 10
    MAX_QUESTION_PER_SEARCH_PAGE = 10
    
    MAX_ANSWERS_PER_PAGE = 10
    _vuser = ZhihuUser('','','','','','','','','',0,0,0,0,0,0,0,0,0,'','','')       #used for judging whether the user with certain user_url 
                                                                                    #is existed in database or not.
    MAX_COMMENT_PER_PAGE = 30                                                                                
    
    def __init__(self, *args, **kwargs):
        return super(CommentParser, self).__init__(*args, **kwargs)
    
    @classmethod
    def parse_bing(cls, html):
        """parse question url and title from html returned by Bing"""
        questions = re.findall(r'<h2><a href="(http(s|)://www.zhihu.com/question/\d{8})".+?>(.+?)</a></h2>', html[0])
        question_count = len(questions)
        for node in questions:
            try:
                url = node[0]
                uri = re.findall('/question/\d{8}', url)[0]
                title = node[2].decode('utf-8')

                q = ZhihuQuestion(uri, title, '')
                Global.g_data_queue.put(q)
                isexisted = Global.g_zhihu_database.is_existed(q)
                #if not isexisted: 
                Global.g_question_queue.put(uri)
                
            except Exception,e :
                _g_html_logger.error('%s when parse bing html'%e)
        if question_count < cls._QUESTION_PER_PAGE_BING:
            #_g_html_logger.warning('Achieve to the end of bing cache')
            return ErrorCode.ACHIEVE_END
        return ErrorCode.OK
        
    @classmethod
    def Parser_zhihu(cls, html, keywords, count=None, AJAX=True):
        '''
        parse questions' information in html returned by get_html(url) method, and put the Question object into global queue, and write 
              in database. 
        parameter: html, list[string], has only one element, which is the resource specified by url   
                   keywords, string, 
                   count, int, just tells the parser how many questions need to be parsed under this `keywords`(sorted by default),
                          if count is not specified, parser will parse questions till the end of the question list of this `keywords`
        return:  return error code(int), which is the signal to tell upper method to react properly, such as exit loop or continue loop or 
                 retry once again
        '''
        #if count has negative value, return directly
        if count is not None and count<=0: return ErrorCode.ACHIEVE_USER_SPECIFIED
        #abstract question node from html
        if not AJAX:
            parse = etree.HTML(html[0])
            question_node = parse.xpath("//li[@class='item clearfix' or 'item clearfix article-item']/div[@class='title']/a")
        else:
            question_node = json.loads(html[0])['htmls']
        question_counts = len(question_node)
        #if no question node is abstracted, return list_empty_error code
        if question_counts == 0:
            _g_html_logger.error("No question in search page, please chech xpath")
            return ErrorCode.LIST_EMPTY_ERROR
        num = 0 #initial counter
        for item in question_node:
            try:
                if AJAX:
                    item = etree.HTML(item).xpath('body/li/div/a')[0]
                question_url = item.attrib['href']
                question_title = ''.join(item.xpath('string(.)')) #abstract text which out of tag or in unstardard tag, such as `<a>blabla</b>` 

                if not question_url.startswith('http'): 
                    q = ZhihuQuestion(question_url, question_title, keywords)
                    Global.g_data_queue.put(q)
                    isexisted = Global.g_zhihu_database.is_existed(q)
                    if not isexisted: Global.g_question_queue.put(q)
                else:
                    question_title = question_title + u'(专栏)' #we don't care for special column                   
                    q = ZhihuQuestion(question_url, question_title, keywords) 
                    Global.g_data_queue.put(q)
                    isexisted = Global.g_zhihu_database.is_existed(q)
                    #if not isexisted: Global.g_question_queue.put(q)
                
                num += 1
                if count is not None and num >= count: #if counter achieves count's value, return 
                    _g_html_logger.info('%s question count has achieve given value: %s'%(keywords,count))
                    print '%s question count has achieve given value: %s'%(keywords,count)
                    return  ErrorCode.ACHIEVE_USER_SPECIFIED
            except (IndexError, AttributeError), e :
                _g_html_logger.warning('%s when parser %s'%(e, keywords))
                print ('%s when parser %s'%(e, keywords))

        if question_counts < cls.MAX_QUESTION_PER_SEARCH_PAGE: #if question count in this html less than standard count, it can be
                                                                            #considered this html is the last one of this `keywords`
            _g_html_logger.info('%s Achieve end of the search page!'%keywords)
            return ErrorCode.ACHIEVE_END  # notify the upper loop to exit
        return ErrorCode.OK #normal condition    
        
    @classmethod
    def parse_qstn(cls, html, quest_url):
        """
        @parameters: html, list which has only one element. 
                     quest_url, uniform resource locator, whose format is `/question/\d{8}`, eg. /question/12345678
        this function does two things below,
             1. when run into answer, push the url of anthor into Global.g_user_queue. and push image url list into Global.g_img_queue
                and push comment url of this answer int Global.g_answer_comment_queue
             2. insert answer information into database
        @return will return error code according to parse result
        """
        AJAX = True if '"r":0' in html[0] else False #specified whether the html has complete html structure ,
                                                     #or has only partial elements, such as json or xml
                                                     #if AJAX==False, means the html[0] has all elements of an complete html page
        
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
                _g_html_logger.error('%s when parse %s'%(e, quest_url))
                all_answer_counts = None
                answer_nodes = []
        answer_counts = len(answer_nodes)
        
        if answer_counts == 0 and u'"msg": []' not in html[0]:
            _g_html_logger.error("no answer in question page, chech xpath of answer_nodes")
            Global.g_fail_url.warning(quest_url)
            return ErrorCode.LIST_EMPTY_ERROR, all_answer_counts
            # return ErrorCode.LIST_EMPTY_ERROR
        
            
        for node in answer_nodes:
            try:
                if AJAX:
                    node = etree.HTML(node).xpath('body')[0].xpath('div')[0]
                id = node.attrib['data-aid']
                date = node.attrib['data-created']
                vote = node.xpath('div/button/span[@class="count"]')[0].text                
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
                    except KeyError:
                        url = img.attrib['src']
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
                answer_url = node.xpath("link")[0].attrib['href'].split('/')[4] # 44370648
                                                               
                answer = ZhihuAnswer(id, date, is_anonymous, user_url, user_name, INT(vote), comment_count, 
                                     content,img_urls, ext_links, user_url, quest_url, answer_url, hasimg)

                cls._vuser.user_url = user_url                
                isexisted = Global.g_zhihu_database.is_existed(answer)
                if not isexisted:
                    Global.g_data_queue.put(answer)
                if vote != '0' and hasimg and not isexisted:
                    Global.g_img_queue.put({'user_name': user_name, 'img_urls': img_urls})
                if not is_anonymous and not isexisted:
                    if not Global.g_zhihu_database.is_existed(cls._vuser):
                        Global.g_user_queue.put(user_url)
                if comment_count is not 0 and not isexisted:
                    #Global.g_answer_comment_queue.put([quest_url, answer_url, comment_count])
                    pass
            except Exception, e:
                print '%s when parser %s'%(e, quest_url)
                _g_html_logger.warning('%s when parser %s'%(e, quest_url))
        if answer_counts < cls.MAX_ANSWERS_PER_PAGE:
            _g_html_logger.info('Achieve end of the answers in %s'%quest_url)
            return ErrorCode.ACHIEVE_END, all_answer_counts
        return ErrorCode.OK, all_answer_counts
        
    @classmethod
    def parse_usr(cls, html, user_url):
        """
        @parameter: html, returned by GetHtml() method, list with only one element
                   user_url , is the url of user, such as /people/peng-quan-xin    
        @function, parse user's information and insert it into database                 
        @return error code
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
            Global.g_data_queue.put(user)
        except Exception, e:
            _g_html_logger.error("%s when parser %s"%(e, user_url))
            Global.g_fail_url.warning(user_url)
            return ErrorCode.USER_INFO_FAIL
        return 0
        
    @classmethod
    def parse_cmnt(cls, html, answer_url, url):
        """
        @param: answer_url is the code of answer, such as 20990037
                url is the whole url of this comment, such as 'https://www.zhihu.com/r/answers/8720147/comments?page=2'
        """

        try:
            comment_list = json.loads(html[0])['data']
        except Exception, e:
            _g_html_logger.error('%s when parse comment %s'%(e, answer_url))
            print '%s when parse comment %s'%(e, answer_url)
            #TODO write url file
            Global.g_fail_url.warning(url)
            return ErrorCode.COMMENT_FAIL
        for comment in comment_list:
            try:
                id = comment['id']
                replyid = comment['inReplyToCommentId']
                name = comment['author']['name']
                content = comment['content']
                likesCount = int(comment['likesCount'])
                c = ZhihuComment(id, replyid, name, content, likesCount, answer_url)
                Global.g_data_queue.put(c)

            except Exception,e:
                _g_html_logger.error("%s when parser %s"%(e, answer_url))
            
        return 0