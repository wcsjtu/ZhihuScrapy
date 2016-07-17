# -*- coding: utf-8 -*-
# -*- author: wangchao
# -*- email: wcsjtu@gmail.com



# This file is used for user to inherit to custom the rules of target web server


"""
   This file is used for user to inherit to custom the `rules` of target web server.
The `rules` are used to generate urls for the following http requests, according to 
current url, request payloads, headers and corresponding html. The details of `rules` 
is depend on user's requirments and the interfaces of target webserver. Generally, 
`rules` are two main parts: i) filters of urls in html, ii) generators from next ajax 
request. 

    For example, we want to obtain the all urls in html which returned by search engine bing
with keywords `site:www.zhihu.com/question/ *`. our interested urls match the format fmt='htt
ps://www.zhihu.com/question/\d{8}'. Firstly, we need bing keywords `site:www.zhihu.com/questi
on/ *` to get the html, the corresponding http url is 'https://cn.bing.com/search', method is 
'GET', payloads is {'q':'site:www.zhihu.com/question/ *', 'first':1}, headers is None, means  
has no special requirements. So, the filter is f(html, url, method, payloads, headers, fmt)=
[ [] ]
 
url is 'https://'
    
 
"""
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append("..")
#import Global as gl
from SpiderFrame import Global as gl

from functools import wraps



class Rules(object):
    """base class for specified rules"""

    @classmethod
    def ajax_rules(cls, sextp, rulefactor):
        """
        this function is used to generate parameters of next http request by ajax
        @params: sextp, instance of class HttpSextp. See .Http/SexTuple.py for detail 
                 rulefactor, instance of class RuleFactor. 
        @return  this function must return None or instance of class HttpSextp, whose reponse and response_headers are None
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
        def wrapper(obj, sextp, queue_dict):
            ret = func(obj, sextp, queue_dict)
            assert isinstance(ret, RuleFactor)
            next = cls.ajax_rules(sextp, ret)
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


class RuleFactor(object):
    """
    store the two aspects of rules
    """
    def __init__(self, count=None, urls=None):
        """
        @params: count, integer.
                 urls, list.
        """
        self.count = count
        self.urls = urls

