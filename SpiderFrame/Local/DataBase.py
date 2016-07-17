# -*- coding: utf-8 -*-

import time
import sys
import os
import threading

reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append("..")

#import Global as gl
from SpiderFrame import Global as gl
from ..Logger import ZhihuLog
import Config
from ..Html.StructData import StructData

try:
    import MySQLdb as DB
    from _mysql_exceptions import Error
    from _mysql_exceptions import OperationalError
    _h = '%s' #placeholder for MySQL syntax
except ImportError:
    print "fail to import site-package `MySQLdb`, check whether it has been installed or not"
    sys.exit()
    #doesn't supoort sqlite3 anymore
    import sqlite3 as DB
    from sqlite3 import Error
    _h = '?' #placeholder for Sqlite3 syntax


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

class DataBase(threading.Thread):
    """
    base class for database class
    """

    _COMMIT_INTEVAL = 300

    def __init__(self):
        threading.Thread.__init__(self, name='database')        
        Config.mysql_params()
        #if _mysql_flag:
        self.database = _create_database(gl.g_dbtable)
        # else:
        #     with DB.connect(self._DATABASE_PATH, check_same_thread=False) as db:
        #         self.database = db
        #         self.database.text_factory = str  
        self.exit = False
        self.cur = self.database.cursor()
        self.timer = time.time()
        self.setDaemon(False)
        #self._lock = threading.Lock()
        self.start()

    def insert_data(self, obj):
        """
        insert data into database.
        @params: obj, instance of StructData's subclass, which user defined.
        """
        assert issubclass(obj.__class__, StructData), \
            "invalid parameter `obj`. make sure it's the instance of StructData's subclass"
        cmd_part = "INSERT INTO %s VALUES ("%obj.__class__.__name__

        cmd = ''.join([cmd_part, ','.join(["%s"]*obj._attr_count), ")"])
        place_hd = tuple([_h]*obj._attr_count)
        sql = cmd%place_hd

        try:
            #self._lock.acquire(True)  
            ret = self.cur.execute(sql, obj.format())
            #self.database.commit()            
        except Error, e :
            _g_database_logger.warning("insert data error, reason: %s"%str(e))
        finally:
            #self._lock.release()
            pass


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
            
                if (gl.g_url_queue.empty() and gl.g_data_queue.empty() and gl.g_html_queue.empty()) or self.exit:
                    _g_database_logger.warning("Task Compeleted, database thread exit")
                    break
            except Exception, e :
                _g_database_logger.error("commit data to database error, reason: %s"%str(e))
        self.cur.close()

    def _commit_data(self):
        """commit insert transaction"""
        try:
            self.database.commit()
        except Exception, e :
            _g_database_logger.error("commit data to database error, reason: %s"%str(e))


    def read(self, tbn, filters=None, cln=None):
        """
        fetch data from database
        @params: tbn, string, name of table
                 filters, unicode string. used to filt data from database.Its format is u"attrib0='value0' AND attrib1='value1'"
                          if value is integer, the `'` can be negelected, eg. u"followers=99"
                          default value is `None`. 
                 cln, list, name of column, default value is `None`. If specified, method
                      just return the column value ,rather than the entire line
        eg. self.read(tbn='Users', u"education='???????'") will return all
            the lines which match the `filters`
            self.read(tbn='Users', u"education='???????'", ['name', 'user_url'])
            will return column `name` and `user_url` of line which matches `filters` 
        """
        cl = ','.join(cln) if cln is not None else '*'
        fts = "WHERE %s"%filters if filters is not None else ""
        cmd = r'''SELECT %s FROM %s %s'''%(cl, tbn, fts)
        try:
            #self._lock.acquire(True)
            self.cur.execute(cmd)
            data = self.cur.fetchall()            
        except Error, e:
            _g_database_logger.warning('read data error, reason: %s'%e)
            data = ()
        finally:
            #self._lock.release()
            return data

    def is_existed(self, obj):
        """judge whether the obj is already in table `tbn`"""   
        assert issubclass(obj.__class__, StructData), \
            "invalid parameter `obj`. make sure it's the instance of StructData's subclass"
        data = self.read(obj.__class__.__name__, "%s='%s' limit 1"%(obj._primary_k, obj.__dict__[obj._primary_k]), [obj._primary_k])            
        return True if data != () else False    

    @classmethod
    def set_intval(cls, interval):
        """
        set the interval betweent two commit operations
        @params: interval, integer. seconds betweent two commit operations
        """
        cls._COMMIT_INTEVAL = interval
        
    def quit(self):
        """force thread to exit"""
        self.exit = True


    def run(self):
        self.write()
