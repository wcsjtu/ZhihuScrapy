# -*- coding: utf-8 -*-



"""
this file defines the basic data structure in http requests and respnose
"""

class HttpSextp(object):

    """
    data structure which storage http revalent data, such as request headers, 
    url, payload, response data and response headers
    """    
    def __init__(self, url, method, req_headers, payloads, response,  rsp_headers):
        
        """
        @params: url, string. Http request url
                 method, string. Http method, one of "GET" "POST" "PUT" "DELETE" "OPTION" "TRACE" "HEAD"
                 req_headers, dict or None. http request headers, if is None, the request method will use default headers
                 payloads, dict or None. extra information need to take when send request
                 response, list, which has only on element. its element always is html or binary data
                 rsp_headers, dict. Http response's headers. it always contans many useful information, such as cookies, locaitons
                 
        """

        self.url = url
        self.method = method
        self.request_headers = req_headers
        self.payloads = payloads
        self.response = response
        self.response_headers = rsp_headers
        return super(HttpSextp, self).__init__()


class HttpSrsc(object):
    """Http static resource """
    
    def __init__(self, urls, headers, storepath):
        """
        @params: urls, list of static resources' url.
                 headers, dict or None. http request headers. If is None, the request method will use default headers
                 storagepath, the path in file system of static resource storaged
        """
        self.urls = urls
        self.headers = headers
        self.storepath = storepath
        return super(HttpSrsc, self).__init__()