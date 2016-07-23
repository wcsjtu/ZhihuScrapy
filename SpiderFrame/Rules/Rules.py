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
import urllib
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append("..")
#import Global as gl
from SpiderFrame import Global as gl
from ..Http.SexTuple import HttpSextp
from .pybloom import BloomFilter, ScalableBloomFilter
from .utils import range_fn
from functools import wraps



class Rules(object):
    """base class for specified rules"""
    _bloom = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)

    @classmethod
    def ajax_rules(cls, sextp, rulefactor):
        """
        this function is used to generate parameters of next http request by ajax
        @params: sextp, instance of class HttpSextp. See .Http/SexTuple.py for detail 
                 rulefactor, instance of class RuleFactor. 
        @return  this function must return None or instance of class HttpSextp, whose reponse and response_headers are None
        """
        raise NotImplementedError('method `ajax_rules` must be override in subclass')
        
    @classmethod
    def filt_rules(cls, sextp, rulefactor):
        """
        this function is used to filt the urls in html by cerntain rules
        @params: sextp, instance of class HttpSextp. See .Http/SexTuple.py for detail 
                 rulefactor, instance of class RuleFactor.
        @return this function must return [url1, url2....] or None
        """
        raise NotImplementedError('method `filt_rules` must be override in subclass')

    @classmethod
    def filter(cls, func):
        """"""
        @wraps(func)
        def wrapper(obj, sextp, queue_dict):
            temp = []
            ret = func(obj, sextp, queue_dict)
            assert isinstance(ret, RuleFactor)
            #print "ret in filter is: ", ret.count, "  ", ret.urls
            #print "sextp in filter is ", sextp.url, " ", sextp.payloads
            #handle ajax
            next = cls.ajax_rules(sextp, ret)
            #print "next in filter", next
            if next is not None:
                if not cls.in_bloom(next.url, next.payloads):
                    temp.append(next)
            #handle urls in htmls
            url_list = cls.filt_rules(sextp, ret)
            if url_list is not None:
                for url in url_list:
                    if not cls.in_bloom(url, None):
                        temp.append(HttpSextp(url, "GET", None, None,None,None))      
            ret = None if temp == [] else temp         
            return ret
        return wrapper

    @classmethod
    def in_bloom(cls, url, payloads):
        """check whether url with payloads is in self._bloom or not"""
        if "#" in url:
            url = url.split("#")[0]
        if payloads is not None:
            url = ''.join([url, '?', urllib.urlencode(payloads)])
        if url.replace("https://", "http://") in cls._bloom:
            return True
        cls._bloom.add(url.replace("https://", "http://"))
        return False
    


class RuleFactor(object):
    """
    store the two aspects of rules
    """
    def __init__(self, count=-1, urls=None):
        """
        @params: count, integer.
                 urls, list.
        """
        self.count = count
        self.urls = urls

