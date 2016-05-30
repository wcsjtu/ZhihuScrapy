# -*- coding: utf-8 -*-

# save text data to database and retrieve media data to file system
#
#

import time
import sys
import os
import threading
import ErrorCode
import Global as gl
import ZhihuLog
from ZhihuHtmlParser import ZhihuAnswer, ZhihuComment, ZhihuQuestion, ZhihuUser
try:
    import MySQLdb as DB
    from _mysql_exceptions import Error
    from _mysql_exceptions import OperationalError
    _mysql_flag = True
    _h = '%s' #placeholder for MySQL syntax
except ImportError:
    print "fail to import site-package `MySQLdb`, check whether it has been installed or not"
    sys.exit()
    #doesn't supoort sqlite3 anymore
    import sqlite3 as DB
    from sqlite3 import Error
    _mysql_flag = False
    _h = '%s' #placeholder for Sqlite3 syntax

reload(sys)
sys.setdefaultencoding('utf-8')

_g_database_logger = ZhihuLog.creatlogger(__name__)

def _create_database(table_list):
    '''
    @parameter:  table_list, list contains certain tables, such as question, answer, user
    @return: return the connection of database
    '''
    import copy
    p = copy.deepcopy(gl.g_mysql_params)
    del p['db']      
    #create database if not existed
    try:
        conn = DB.connect(**p)
        cur = conn.cursor()
        cur.execute('create database if not exists %s'%gl.g_mysql_params['db'])
        conn.select_db(gl.g_mysql_params['db'])
    except Error, e :
        print '%s when create database %s'%(e, gl.g_mysql_params['db'])
        sys.exit()
    #create table     
    for table in table_list:
        try:
            cur.execute(table)
            _g_database_logger.info("Succeed to create table %s in database %s"%(table, gl.g_mysql_params['db']))
        except OperationalError, e :
            _g_database_logger.error('Fail to create table in database %s, reason: %s'%(gl.g_mysql_params['db'], e.message))            
            if e[0] != 1050:
                print 'Fail to create table in database %s, reason: %s'%(gl.g_mysql_params['db'], e.message)
                sys.exit()

    return conn

class ZhihuDataBase(threading.Thread):
    '''save text data to database'''

    _DATABASE_PATH = 'zhihu.db'
    _question_table_name = 'Questions'
    _answer_table_name = 'Answers'
    _user_table_name = 'Users'
    _comment_table_name = 'Comments'
    _QUESTION_TABLE = '''CREATE TABLE %s       (   title      varchar(256),
                                                   url        varchar(32) ,
                                                   keywords   char(8),
                                                   PRIMARY KEY(url)
                                                );'''%_question_table_name
    _ANSWER_TABLE = '''CREATE TABLE %s       (   id             int ,
                                                 date           int,
                                                 anonymous      char(1),
                                                 user_url       varchar(256),
                                                 user_name      varchar(256),
                                                 vote           int,
                                                 comment_count  int,
                                                 content        mediumtext,
                                                 img_urls       text,
                                                 extern_links   text,
                                                 img_folder     varchar(256),
                                                 question_url   varchar(32),
                                                 answer_url     varchar(64),
                                                 PRIMARY KEY(id),
                                                 FOREIGN KEY(question_url) REFERENCES %s(url),
                                                 FOREIGN KEY(user_url) REFERENCES %s(user_url)
                                                ); '''%(_answer_table_name, _question_table_name, _user_table_name)
    _USER_TABLE = '''CREATE TABLE %s     (   name           varchar(256),
                                             gender         varchar(32),
                                             discription    text,
                                             location       text,
                                             position       text,
                                             business       text,
                                             employ         text,
                                             education      text,
                                             sign           text,
                                             followees      int,
                                             followers      int,
                                             upvote         int,
                                             thanks         int,
                                             asks           int,
                                             answers        int,
                                             papers         int,
                                             collection     int,
                                             public         int,
                                             weibo          varchar(256),
                                             user_url       varchar(256),
                                             avatar_url     varchar(256),
                                             avatar_path    varchar(256),
                                             PRIMARY KEY(user_url)
                                             );'''%_user_table_name

    _COMMENT_TABLE = '''CREATE TABLE %s       (  ID             int,
                                                 ReplyID        int,
                                                 CommentBy      text,
                                                 Content        text,
                                                 Supporters     int,
                                                 answer_url     varchar(64),
                                                 PRIMARY KEY(ID)
                                                ); '''%(_comment_table_name)

    _COMMIT_INTEVAL = 300
    #_create_database(_DATABASE_PATH, [_QUESTION_TABLE, _ANSWER_TABLE, _USER_TABLE, _COMMENT_TABLE])

    def __init__(self):
        threading.Thread.__init__(self, name='database')
        #if _mysql_flag:
        self.database = _create_database([self._QUESTION_TABLE, self._USER_TABLE, 
                                          self._COMMENT_TABLE, self._ANSWER_TABLE]
                                        )
        # else:
        #     with DB.connect(self._DATABASE_PATH, check_same_thread=False) as db:
        #         self.database = db
        #         self.database.text_factory = str  
        self.cur = self.database.cursor()
        self.timer = time.time()
        self.setDaemon(False)
        self._lock = threading.Lock()
        #self.start()

    def insert_data(self, instance):
        '''
        parameter: instance, instance of Zhihu data class, such as ZhihuUser, ZhihuComment 
        '''
        if isinstance(instance, ZhihuQuestion):
            data = (instance.question_title, instance.question_url, instance.keywords)
            cmd = r'''INSERT INTO %s VALUES (%s,%s,%s)'''%(self._question_table_name, _h, _h, _h)
            
        elif isinstance(instance, ZhihuAnswer):
            data = (instance.id, instance.date, int(instance.is_anonymous), instance.user_url, instance.user_name, instance.vote, instance.comment_count, instance.content,
                    '\n'.join(instance.img_urls), '\n'.join(instance.extern_links),  instance.img_folder, instance.question_url, instance.answer_url)
            cmd = r'''INSERT INTO %s VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''' % (self._answer_table_name, 
                                             _h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h)
        elif isinstance(instance, ZhihuUser):
            data = (instance.name, instance.gender, instance.discription, instance.location, instance.position,
                    instance.business, instance.employ, instance.education, instance.sign, instance.followees, 
                    instance.followers, instance.upvote, instance.thanks, instance.asks, instance.answers, instance.papers, 
                    instance.collection, instance.public, instance.weibo, instance.user_url, instance.avatar_url, instance.user_url)
            cmd = r'''INSERT INTO %s VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''%(self._user_table_name,
                                             _h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h,_h)
        elif isinstance(instance, ZhihuComment):
            data = (instance.id, instance.replyid, instance.comment_by, instance.content, instance.likes, instance.answer_url)
            cmd = r'''INSERT INTO %s VALUES (%s,%s,%s,%s,%s,%s)'''%(self._comment_table_name,
                                             _h,_h,_h,_h,_h,_h)

        try:
            self._lock.acquire(True)  
            ret = self.cur.execute(cmd, data)
            #self.database.commit()            
        except Error, e :
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
        self.cur.close()

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
        cl = ','.join(cln) if cln is not None else '*'
        fts = "WHERE %s"%filters if filters is not None else ""
        cmd = r'''SELECT %s FROM %s %s'''%(cl, tbn, fts)
        try:
            self._lock.acquire(True)
            self.cur.execute(cmd)
            data = self.cur.fetchall()            
        except Error, e:
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





