# -*- coding: utf-8 -*-

from SpiderFrame.Html import Parser, StructData
from SpiderFrame.Rules import Rules
from SpiderFrame.Local import Config, DataBase
from SpiderFrame.Http import Client, SexTuple
from SpiderFrame import Global as gl
import re
import urllib
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class GithubRepo(StructData.StructData):
    _database_struct = [("RepoName", "varchar(256)", "primary key"),
                        ("Stars", "int"),
                        ("Forks", "int"),
                        ("Language", "varchar(32)", "NULL")
                        ]
    def __init__(self, RepoName, Stars, Forks, Language=None):
        self.RepoName = RepoName
        self.Stars = Stars
        self.Forks = Forks
        self.Language = Language
        super(GithubRepo, self).__init__()
GithubRepo.register()


class GithubRules(Rules.Rules):

    MAX_REPOS = 0

    @classmethod
    def ajax_rules(cls, sextp, rulefactor):
        """"""
        try:
            if re.search('github.com/search', sextp.url):
                if rulefactor.count < cls.MAX_REPOS:
                    return None
                if sextp.request_headers is None:
                    sextp.request_headers = {}

                if sextp.payloads is None:
                    sextp.payloads = {}

                sextp.request_headers['referer'] = ''.join([sextp.url, 
                                                            '?', 
                                                            urllib.urlencode(sextp.payloads)
                                                            ])
                if not 'p' in sextp.payloads:                                        
                    sextp.payloads['p'] = 2                                                                               
                else:
                    sextp.payloads['p'] = sextp.payloads['p'] + 1
                sextp.response = None
                sextp.response_headers = None
                print "payloads in rules: ", sextp.payloads
                return sextp
            else:
                print "url in rules: ", sextp.url 
                return None
        except Exception,e :
            print "error in ajax_rules", e
            return None

    @classmethod
    def filt_rules(cls, sextp, rulefactor):
        """ """
        if rulefactor.urls is None:
            return None
        ret_urls = []
        for url in rulefactor.urls:
            if re.search('github.com/search', url):
                ret_urls.append(url)
        if ret_urls == []:
            return None
        else:
            return ret_urls
    #_filter_pattern = re.compile(r'/question/\d{8}|/people/.+')
    #@classmethod
    #def filt_rules(cls, sextp, rulefactor):
    #    """
    #    filter the url in rulefactor.urls
    #    """
    #    if rulefactor.urls is None:
    #        return None
    #    ret_urls = []
    #    for url in rulefactor.urls:
            
    #        keyword = cls._filter_pattern.findall(url)
    #        if keyword != []:
    #            ret_urls.append("https://www.zhihu.com"+keyword[0])
    #    return None if ret_urls == [] else ret_urls


class GithubParser(Parser.ParserProc):
    """"""
    def __init__(self, name_, fk=True):
        """"""
        super(GithubParser, self).__init__(name_)
        if fk:
            self.start()

    @GithubRules.filter
    def parse_github(self, sextp, proc_queue):
        """"""
        pattern = re.compile(r'''repo-list-stats[\s\S]+?repo-list-description''')
        repos_blocks = pattern.findall(sextp.response[0])
        count = len(repos_blocks)
        for repo in repos_blocks:
            lang = re.findall(r'''repo-list-stats">\s+? +([a-z|A-Z|0-9]*)\s+?''', repo)[0]
            stars = re.findall(r'''Stargazers[\s\S]+?(\d+?)\n''', repo)[0]
            forks = re.findall(r'''Forks[\s\S]+?(\d+?)\n''', repo)[0]
            repo_name = re.findall(r'''repo-list-name[\s\S]+?href="/(.*)">''', repo)[0]

            data = GithubRepo(repo_name, stars, forks, lang)

            proc_queue['data_queue'].put(data)
        urls = self.extract_url(sextp.response[0])
        #print "count in parse: ", count
        #print "payloads in parse: ", sextp.payloads
        return Rules.RuleFactor(count, urls)

    
GithubParser.add_map(GithubParser.parse_github, re.compile('github.com/search'))
GithubParser.parse_default = GithubRules.filter(GithubParser.parse_default)



class MyHttpClient(Client.HttpClient):
    """"""
    def __init__(self, hostname):

        super(MyHttpClient, self).__init__()
        self.url = hostname

gl.g_http_client = MyHttpClient("https://github.com")
gl.g_database = DataBase.DataBase()


def main():
    import time
    DataBase.DataBase.set_intval(30)
    # 向队列里添加元素
    github_python = SexTuple.HttpSextp("https://github.com/search", 
                                       "GET", 
                                       None, 
                                       {'q': 'lua', 'type': 'Repositories', 'ref': 'searchresults'},
                                       None,
                                       None)
    github_java = SexTuple.HttpSextp(  "https://github.com/search", 
                                       "GET", 
                                       None, 
                                       {'q': 'go', 'type': 'Repositories', 'ref': 'searchresults'},
                                       None,
                                       None)
    
    # 之所以要添加2个，是因为只添加1个的话，在htmlclient从队列中取出元素后，将html压入队列前，会导致所有的队列都处于empty
    # 状态，数据库线程、Parse进程在发现队列所有队列都为空时，会立即退出，导致程序无法正常工作。所以，在单htmlclient线程的
    # 情况下，开始时需要添加两个元素。如果是多htmlclient线程，情况会更复杂。这个问题后续会解决
    gl.g_url_queue.put(github_python)
    gl.g_url_queue.put(github_java)

    # 创建HtmlClient实例
    Client.HtmlClient.set_intval(8)
    htmlclient = Client.HtmlClient('downloader')

    # 如果需要下载静态资源，可以创建StaticClient实例
    # static_rcclient = Client.StaticClient()

    # 创建Parse子进程
    parser = GithubParser('github')

    print "enjoy it!"
    
    #监视各个队列
    while True:
        print 'url queue:  ', gl.g_url_queue.qsize(), "downloader: ", htmlclient.isAlive()
        print 'html queue: ', gl.g_html_queue.qsize(), "parser: ", parser.is_alive()
        print 'data queue: ', gl.g_data_queue.qsize(), "database: ", gl.g_database.isAlive()
        print 'image queue:', gl.g_static_rc.qsize()
        print '=========================================\n\n'
        time.sleep(3)    


def test_parser():
    import os
    pwd = os.getcwd()

    with open(pwd + "/test/zhihu.html", 'r') as f:
        html = [f.read()]
        sextp_github = SexTuple.HttpSextp("https://github.com/search", "GET", None, {'type': 'Repositories', 'q': 'python'}, html, None)
        gl.g_html_queue.put(sextp_github)

    #往布隆过滤器中添加元素，用于测试布隆过滤器是否正常工作
    GithubRules.in_bloom("https://github.com/search", None)
    GithubRules.in_bloom("https://github.com/search?q=python&type=Users&utf8=%E2%9C%93", None)
    GithubRules.in_bloom('https://github.com/search?l=VimL&q=python&type=Repositories&utf8=%E2%9C%93', None)
    GithubRules.in_bloom("https://github.com/search?o=asc&q=python&s=forks&type=Repositories&utf8=%E2%9C%93", None)
    GithubRules.in_bloom("https://github.com/search?q=python&type=Users&utf8=%E2%9C%93", None)


    parser = GithubParser(name_ = 'github', fk=False)
    parser.work(parser._args[0])






if __name__ == "__main__":
    #main()
    test_parser()