#ZhihuScrapy
ZhihuScrapy用python 2.7编写，最初用于爬取[知乎](https://www.zhihu.com/)上的数据与静态资源。后来经过多次修改，从最初代码里提取出通用的
爬虫框架(SpiderFrame)。该框架现在还处于原始版本，只有数据库操作、进程调度等功能。用户只需要定制爬取规则(Rules)和html解析(Parser)部分，
就能写出定向爬虫。

## 依赖库
SpiderFrame是由纯python编写的，在其中使用了许多优秀的开源库。在使用SpiderFrame时请确保它们已正确安装
- [requests](https://github.com/kennethreitz/requests)面向人的网络库
- [bitarray](https://pypi.python.org/pypi/bitarray/)二进制数据操作模块(布隆过滤器使用)
- [MySQLdb](https://pypi.python.org/pypi/MySQL-python/1.2.5)MySQL python版驱动

## 快速开始
从github上下载[SpiderFrame](https://github.com/wcsjtu/ZhihuScrapy)，并将SpiderFrame目录放到$path/python27/Lib/site-packages/目录下。
下面便以爬取github上python repositories的名称、star数、fork数，并存入数据库为目标，写一个简单的爬虫

- 定制Parser模块，包括定义爬取的数据类型、定制解析html的函数
```python
# 导入模块
from SpiderFrame.Html import Parser, StructData
from SpiderFrame.Rules import Rules
from SpiderFrame.Local import Config, DataBase
from SpiderFrame.Http import Client, SexTuple
from SpiderFrame import Global as gl
import re
import urllib

# 定义数据结构，类名就是table名称
class GithubRepo(StructData):
    #定义数据库结构
    _database_struct = [("RepoName", "varchar(256)", "primary key"),
                        ("Stars", "int"),
                        ("Forks", "int"),
                        ("Language", "varchar(32)", "NULL")
                        ]
    def __init__(self, RepoName, Stars, Forks, Language=None):
        # 确保参数的顺序、数目与_database_struct中的一致
        self.RepoName = RepoName
        self.Stars = Stars
        self.Forks = Forks
        self.Language = Language
        super(GithubRepo, self).__init__()
# 最后注册数据结构，这句话一定不能省略
GithubRepo.register()

# 定制Parser类
class GithubParser(Parser.ParserProc):
    """
    ParserProc是multiprocessing.Process的子类。这个类主要负责解析html，要长时间占用CPU。由于Python GIL的存在，
    这种情况下多进程要比多线程效率高，所以把解析html的部分放在单独进程里。当调用Parser.ParserProc的__init__()后，
    执行self.start()便会fork出子进程。
    """
    def __init__(self, name_, fk=True):
        """
        name_是子进程名，fk是是否要fork子进程
        """
        super(GithubParser, self).__init__(name_)
        if fk:
            self.start()

    # 定义html解析函数。这个解析函数需要规则修饰器来修饰，规则修饰器后文会详细说明。
    # 这里暂定规则修饰器为GithubRules.filter
    @GithubRules.filter
    def parse_github(self, sextp, proc_queue):
        """
        这个函数负责解析html，并返回解析出来的数据条目数和html中包含的url列表，这两个值放在Rules.RuleFactor实例中。
        参数sextp是SexTuple.HttpSextp类的实例，这个类的定义在SpiderFrame.Http.SexTuple.py文件中。这个
        类包含6个属性， 
            url                请求url，即html对应的url
            method             请求方法，一般是'GET'或者'POST'
            request_headers    请求头部，默认值是None
            payloads           请求的负载，类型是字典或者None
            response           http响应正文，html就在这个属性中，即html=response[0]
            response_headers   http响应头部，字典或者None

        另外一个参数proc_queue是用于进程间通信的队列合集，类型是字典。这个参数中包含了4个队列，分别是，
            'html_queue'       用于进程间传递html信息，队列中元素是SexTuple.HttpSextp类的实例，而且它的
                               response不是None
            'url_queue'        用于进程间传递url信息，队列中的元素也是SexTuple.HttpSextp类的实例，但是它
                               的response和response_headers都是None
            'data_queue'       用于进程间传递结构化数据信息，队列中的元素是StructData的子类的实例，在这个
                               例子中，也就是GithubRepo的实例
            'static_rc'        用于进程间传递静态资源信息，队列中的元素是SexTuple.HttpSrc实例。这个类包含
                               静态资源的url和本地存储路径

        函数返回一个Rules.RuleFactor实例。该实例包含两个属性，
            count              表示从html提取到多少个结构化的数据，在这个例子里，也就是提取到多少个repo的
                               信息。这个属性会在Rules中使用，如果count值小于正常值，说明没有下一页了。
            urls               表示从html中提取到的超链接。这个属性同样会在Rules中使用，过滤掉不感兴趣的链
                               接。剩下的链接会生成SexTuple.HttpSextp实例并放入url_queue
        """
        # 解析html可以使用正则表达式、HtmlParser、BeautifulSoup、lxml等库。推荐使用lxml
        # 由于这个例子简单，杀鸡焉用牛刀，re模块就可以了
        pattern = re.compile(r'''repo-list-stats[\s\S]+?repo-list-description''')
        repos_blocks = pattern.findall(sextp.response[0])
        count = len(repos_blocks)
        for repo in repos_blocks:
            lang = re.findall(r'''repo-list-stats">\s+? +([a-z|A-Z|0-9]*)\s+?''', repo)[0]
            stars = re.findall(r'''Stargazers[\s\S]+?(\d+?)\n''', repo)[0]
            forks = re.findall(r'''Forks[\s\S]+?(\d+?)\n''', repo)[0]
            repo_name = re.findall(r'''repo-list-name[\s\S]+?href="/(.*)">''', repo)[0]

            # 生成结构化数据对象
            data = GithubRepo(repo_name, stars, forks, lang)

            # 将数据放入data_queue，数据库线程会从这个队列里取数据并存入数据库
            proc_queue['data_queue'].put(data)

        # 因为html没有感兴趣的url，所以第二个参数为None
        return Rules.RuleFactor(count, None)

# 定义Parse类后，需要将其中的parser_xxx方法与某一类url对应起来。即让程序知道，当html对应的url具有某种形式时，
# 应该把它送到哪个parser_xxx方法去解析。虽然这里只有一类url、一个解析函数，但还是要显式地指出parser_xxx方法与
# url的对应关系。
# classmethod add_map就是用来建立这种关系的函数。它第一个参数是方法名，第二个参数是re.compile()返回的实例
GithubParser.add_map(GithubParser.parse_github, re.compile('github.com/search'))
```

*****
- 定制url过滤规则、动态加载规则

第二步就是定制过滤规则。所谓过滤规则，就是用来过滤Rules.RuleFactor.urls中的不感兴趣的url。这个规则对应的代码
在filt_rules函数中。动态加载规则就是，根据当前html的url、payloads、count信息来计算出获取下一页对应的html
应发出的请求，请求对应的url，method，payloads等信息描述在sextp中。

对于这个例子，上代码：
```python
class GithubRules(Rules.Rules):
    """这个类用于描述各种规则"""

    # 定义常量，描述github的搜索页面，正常的repository的数目，如果某个搜索页面的html的repo数小于它，则说明
    # 该html已经是最后一页了
    MAX_REPOS = 10

    # 重写ajax_rules方法
    @classmethod
    def ajax_rules(cls, sextp, rulefactor):
        """
        这个函数实现这样一个功能，对于可以动态加载的页面(比如说有"下一页"的页面)，如何根据当前html的信息，导出获
        取下一页html所需要的http参数(url、payloads、method、headers等)。实现这个功能需要研究目标网站，在
        点击"下一页"后究竟发出了什么样的http请求。推荐使用firebug

        sextp是SexTuple.HttpSextp的实例，包含这当前html的一些信息。前文已详细说明过这个类的属性，不再累述
        rulefactor是Rules.RuleFactor的实例，包含当前html中结构化数据的个数count，html中的url列表urls
        """
        try:
            if re.search('github.com/search', sextp.url):
                if rulefactor.count < cls.MAX_REPOS:
                    # 如果html中的repo数目小于10，则说明翻页到底了，直接返回None
                    return None
                # 在请求头部中加入referer，以告知对方服务器请求是从当前页面发出的(欺骗服务器啊),这步非必要

                # 往请求头中添加元素时，记住要先判断request_headers是否为None
                if sextp.request_headers is None:
                	sextp.request_headers = {}
                sextp.request_headers['referer'] = ''.join([sextp.url, 
                                                            '?', 
                                                            urllib.urlencode(sextp.payloads)
                                                            ])
                # 往payloads里面添加字段时，也需要判断payloads是否是None
                if sextp.payloads is None:
                	sextp.payloads = {}
                if not 'p' in sextp.payloads:                                        
                    # 如果请求payloads里面没有'p'字段，说明当前是第一页，则下一页的payloads加上'p'=2就行
                    sextp.payloads['p'] = 2                                                                               
                else:
                    # 如果请求的payloads里面包含'p'字段，那直接加p加1
                    sextp.payloads['p'] = sextp.payloads['p'] + 1
                # 清除sextp中的过期的响应信息，以提高序列化、反序列化效率
                sextp.response = None
                sextp.response_headers = None
                return sextp
            else:
                # 由于这里只有一类url，所以else里面没有内容。如果有多个不同结构的html要分析，则这里会多出很多分支
                return None
        except Exception,e :
            return None
    
    # 重写ajax_rules方法
    @classmethod
    def filt_rules(cls, sextp, rulefactor):
        """
        这个函数用来过滤rulefactor中的url，具体过滤规则根据自己需求来写。
        返回url的列表,记住，非空，如果列表是空的，则应该返回None，或者None
        """
        if rulefactor.urls is None:
            return None
        # 过滤，具体的过滤规则根据需求实现。这个例子中，因为没有提取html中的url，所以这里用blablabla代替过滤函数
        ret_urls = []
        # ret_urls = blablabla(rulefactor.urls)
        if ret_urls == []:
            return None
        else:
            return ret_urls
```
至此，Rules部分算是定制完成。ajax_rules和filt_rules会在filter里面调用，所以用GithubRules.filter去修饰parse_xx
方法吧。

*****
- 定制的HttpClient

Http.Client.HttpClient类实现了http请求的一些通用功能，如cookie管理、默认User-Agent、日志、重传等功能
如果爬取的目标需要登录才能查看，则需要定制登录功能。
在这个例子中，repository信息不用登录就能查看，所以，不用定制功能，直接继承即可
废话少说，上代码
```python
class MyHttpClient(Client.HttpClient):
    """"""
    def __init__(self, hostname):

        super(MyHttpClient, self).__init__()
        self.url = hostname
```
至此，所有客制化的部分都已完成。

*****
- 初始化全局参数

在SpiderFrame.Global.py中定义了一系列没有赋值的全局变量，如g_http_client, g_database。这两个变量需要在定制完
StructData部分、HttpClient部分后，由用户在全局位置初始化。
**切记，g_http_client 和 g_database 必须在全局位置初始化，否则会出现进程间无法共享内存的情况**
在创建DataBase实例时，会要求输入MySQL的相关参数，这个要根据实际情况来输入
```python
gl.g_http_client = MyHttpClient("https://github.com")
gl.g_database = DataBase.DataBase()
```

*****
- 定义main函数
```python
def main():
    import time
    DataBase.DataBase.set_intval(30) #设置数据库commit时间间隔。框架里的默认值是300秒
    # 向队列里添加元素
    github_python = SexTuple.HttpSextp("https://github.com/search", 
                                       "GET", 
                                       None, 
                                       {'q': 'python', 'type': 'Repositories'},
                                       None,
                                       None)
    github_java = SexTuple.HttpSextp(  "https://github.com/search", 
                                       "GET", 
                                       None, 
                                       {'q': 'java', 'type': 'Repositories'},
                                       None,
                                       None)
    
    # 之所以要添加2个，是因为只添加1个的话，在htmlclient从队列中取出元素后，将html压入队列前，会导致所有的队列都处于empty
    # 状态，数据库线程、Parse进程在发现队列所有队列都为空时，会立即退出，导致程序无法正常工作。所以，在单htmlclient线程的
    # 情况下，开始时需要添加两个元素。如果是多htmlclient线程，情况会更复杂。这个问题后续会解决
    gl.g_url_queue.put(github_python)
    gl.g_url_queue.put(github_java)

    # 创建HtmlClient实例
    htmlclient = Client.HtmlClient('downloader')


    Client.HtmlClient.set_intval(5)
    
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
```

- 最后 
```python
if __name__ == "__main__":
    main()
```

- 更复杂的例子，见test.py