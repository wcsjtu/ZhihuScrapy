# -*- coding: utf-8 -*-

# save text data to database and retrieve media data to file system
#
#

import sqlite3
import time
import datetime
import sys
import threading
import ErrorCode
import Global as gl
import ZhihuLog
from ZhihuHtmlParser import ZhihuAnswer, ZhihuComment, ZhihuQuestion, ZhihuUser

reload(sys)
sys.setdefaultencoding('utf-8')

_g_database_logger = ZhihuLog.creatlogger(__name__)
  

def _create_database(path, table_list):
    '''
    parameter: path, path of database, such as D:\zhihu.db
    table_list, list contains certain tables, such as question, answer, user
    '''
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    for table in table_list:
        try:
            cur.execute(table)
            _g_database_logger.info("Succeed to create table %s in database %s"%(table, path))
        except Exception, e :
            _g_database_logger.error('Fail to create table in database %s, reason: %s'%(path, e.message))

class ZhihuDataBase(threading.Thread):
    '''save text data to database'''

    _DATABASE_PATH = 'zhihu.db'
    _question_table_name = 'Questions'
    _answer_table_name = 'Answers'
    _user_table_name = 'Users'
    _comment_table_name = 'Comments'
    _QUESTION_TABLE = '''CREATE TABLE %s       (   title      TEXT,
                                                   url        TEXT,
                                                   keywords   TEXT,
                                                   PRIMARY KEY(url))'''%_question_table_name
    _ANSWER_TABLE = '''CREATE TABLE %s       (   id             TEXT,
                                                 date           TEXT,
                                                 anonymous      TEXT,
                                                 user_url       TEXT,
                                                 user_name      TEXT,
                                                 vote           INTEGER,
                                                 comment_count  INTEGER,
                                                 content        TEXT,
                                                 img_urls       TEXT,
                                                 extern_links   TEXT,
                                                 img_folder     TEXT,
                                                 question_url   TEXT,
                                                 answer_url     TEXT,
                                                 PRIMARY KEY(id)
                                                 FOREIGN KEY(question_url) REFERENCES %s(url)
                                                 FOREIGN KEY(user_url) REFERENCES %s(user_url)
                                                ) '''%(_answer_table_name, _question_table_name, _user_table_name)
    _USER_TABLE = '''CREATE TABLE %s     (   name           TEXT,
                                             gender         TEXT,
                                             discription    TEXT,
                                             location       TEXT,
                                             position       TEXT,
                                             business       TEXT,
                                             employ         TEXT,
                                             education      TEXT,
                                             sign           TEXT,
                                             followees      INTEGER,
                                             followers      INTEGER,
                                             upvote         INTEGER,
                                             thanks         INTEGER,
                                             asks           INTEGER,
                                             answers        INTEGER,
                                             papers         INTEGER,
                                             collection     INTEGER,
                                             public         INTEGER,
                                             weibo          TEXT,
                                             user_url       TEXT,
                                             avatar_url     TEXT,
                                             avatar_path    TEXT,
                                             PRIMARY KEY(user_url)
                                             )'''%_user_table_name

    _COMMENT_TABLE = '''CREATE TABLE %s       (  ID             INTEGER,
                                                 ReplyID        INTEGER,
                                                 CommentBy      TEXT,
                                                 Content        TEXT,
                                                 Supporters     INTEGER,
                                                 answer_url     TEXT,
                                                 PRIMARY KEY(ID)
                                                ) '''%(_comment_table_name)

    _COMMIT_INTEVAL = 300
    _create_database(_DATABASE_PATH, [_QUESTION_TABLE, _ANSWER_TABLE, _USER_TABLE, _COMMENT_TABLE])

    def __init__(self):
        threading.Thread.__init__(self, name='save_data')
        with sqlite3.connect(self._DATABASE_PATH, check_same_thread=False) as db:
            self.database = db
        self.database.text_factory = str  
        self.cur = self.database.cursor()
        self.timer = time.time()
        self.setDaemon(False)
        self._lock = threading.Lock()
        self.start()

    def insert_data(self, instance):
        '''
        parameter: instance, instance of Zhihu data class, such as ZhihuUser, ZhihuComment 
        '''
        if isinstance(instance, ZhihuQuestion):
            data = (instance.question_title, instance.question_url, instance.keywords)
            cmd = r'''INSERT INTO %s VALUES (?,?,?)'''%self._question_table_name
        elif isinstance(instance, ZhihuAnswer):
            data = (instance.id, instance.date, int(instance.is_anonymous), instance.user_url, instance.user_name, instance.vote, instance.comment_count, instance.content,
                    '\n'.join(instance.img_urls), '\n'.join(instance.extern_links),  instance.img_folder, instance.question_url, instance.answer_url)
            cmd = r'''INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''' % self._answer_table_name
        elif isinstance(instance, ZhihuUser):
            data = (instance.name, instance.gender, instance.discription, instance.location, instance.position,
                    instance.business, instance.employ, instance.education, instance.sign, instance.followees, 
                    instance.followers, instance.upvote, instance.thanks, instance.asks, instance.answers, instance.papers, 
                    instance.collection, instance.public, instance.weibo, instance.user_url, instance.avatar_url, instance.user_url)
            cmd = r'''INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''%self._user_table_name
        elif isinstance(instance, ZhihuComment):
            data = (instance.id, instance.replyid, instance.comment_by, instance.content, instance.likes, instance.answer_url)
            cmd = r'''INSERT INTO %s VALUES (?,?,?,?,?,?)'''%self._comment_table_name

        try:
            self._lock.acquire(True)  
            self.cur.execute(cmd, data)
            #self.database.commit()            
        except sqlite3.Error, e :
            _g_database_logger.warning("insert data error, reason: %s"%e.message)
        finally:
            self._lock.release()

    def write(self):
        """insert data into database continuously"""
        while True:
            try:
                if (time.time()-self.timer) >= self._COMMIT_INTEVAL:
                    self._commit_data()
                    self.timer = time.time()
                else:
                    instance = gl.g_data_queue.get()
                    self.insert_data(instance)
            
                if gl.g_question_exit and gl.g_retrieve_exit and gl.g_usr_exit and gl.g_comment_exit and gl.g_data_queue.empty():
                    _g_database_logger.warning("Task Compeleted, database thread exit")
                    break
            except Exception, e :
                _g_database_logger.error("commit data to database error, reason: %s"%e)

    def _commit_data(self):
        """commit insert transaction"""
        try:
            self.database.commit()
        except Exception, e :
            _g_database_logger.error("commit data to database error, reason: %s"%e)
            
    def read(self, tbn, filters=None, cln=None):
        """
        fetch data from database
        @params: tbn, string, name of table
                 filters, unicode string. used to filt data from database.Its format is u"attrib0='value0' AND attrib1='value1'"
                          if value is integer, the `'` can be negelected, eg. u"followers=99"
                          default value is `None`. 
                 cln, list, name of column, default value is `None`. If specified, method
                      just return the column value ,rather than the entire line
        eg. self.read(tbn='Users', u"education='北京大学'") will return all
            the lines which match the `filters`
            self.read(tbn='Users', u"education='北京大学'", ['name', 'user_url'])
            will return column `name` and `user_url` of line which matches `filters` 
        """
        if cln is not None:
            cl = ','.join(cln)
        else:
            cl = '*'
        if filters is not None:
            fts = "WHERE %s"%filters
        else:
            fts = ""
        cmd = r'''SELECT %s FROM %s %s'''%(cl, tbn, fts)
        try:
            self._lock.acquire(True)
            self.cur.execute(cmd)
            data = self.cur.fetchall()            
        except sqlite3.Error, e:
            _g_database_logger.warning('read data error, reason: %s'%e)
            data = []
        finally:
            self._lock.release()
            return data
            
    def is_existed(self, instance):
        """judge whether the instance is already in table `tbn`"""   
        if isinstance(instance, ZhihuAnswer):   
            data = self.read(self._answer_table_name, "id='%s' limit 1"%instance.id, ['id'])              
            
        elif isinstance(instance, ZhihuUser):
            data = self.read(self._user_table_name, "user_url='%s' limit 1"%instance.user_url, ['user_url'])
            
        elif isinstance(instance, ZhihuComment):
            data = self.read(self._comment_table_name, "ID=%d limit 1"%instance.id, ['ID'])
            
        elif isinstance(instance, ZhihuQuestion):
            data = self.read(self._question_table_name, "url='%s' limit 1"%instance.question_url, ['url'])
            
        return True if data != [] else False    
            

    def run(self):
        self.write()


gl.g_zhihu_database = ZhihuDataBase()
gl.g_fail_url = ZhihuLog.creatlogger('%s_FailURL'%datetime.datetime.now().strftime('%Y-%m-%d'))


if __name__ == "__main__":

    a = ZhihuAnswer('13199838', '1428750165', 0, '/people/zhou-jin-shan', u'周金山', 0, 0, '', [], [], '','','',False )
    b = ZhihuUser('Tsai1307', u'', '', '', '', '', '', '', '', 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '/people/tsai1307', '')
    c = ZhihuQuestion('/question/44863755', u'', '')
    gl.g_data_queue.put(c)
    d = ZhihuComment(123, 33,'', '', 8, '')
    reta = gl.g_zhihu_database.is_existed(a)
    retb = gl.g_zhihu_database.is_existed(b)
    retc = gl.g_zhihu_database.is_existed(c)
    retd = gl.g_zhihu_database.is_existed(d)
    print 1
    raw_input()

