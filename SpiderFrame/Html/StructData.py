# -*- coding: utf-8 -*-

import sys

reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append("..")

from SpiderFrame import Global as gl
#import Global as gl


class StructData(object):
    """
    base class for target data from html
    """
    # _database_struct define the structure of table, which storage this kind of data.
    # it is a list, whose elements aret tuple. tuple's format is (attr_name, type, constrain). 
    # for example, if there is an attribute self.id, and id is an unique integer. so, the tuple
    # is ("id", "int", "primary key") or ("id", "int", "unique"). if there's another attribute
    # self.name, and has no constrain on it. So the tuple is ("name", "varchar(256)").
    # see MySQL for more information about type and constrain

    _database_struct = []
    _attr_count = None
    _primary_k = None

    def __init__(self):
        return super(StructData, self).__init__()

    @classmethod
    def table_struct(cls):
        """
        create the structure of table
        """
        assert cls._database_struct != [], \
               "check the _database_struct, make sure its count of elements is equal to the count of instance attributes"
        cls._attr_count = len(cls._database_struct)
        temp = []
        for item in cls._database_struct:
            if len(item) > 2:
                value = " %s %s %s"%item
                if 'primary' in item[2].lower():
                    cls._primary_k = item[0]
            else:
                value = " %s %s"%item
            temp.append(value)
        if cls._primary_k is None:
            raise RuntimeError("table %s has no primary key"%cls.__name__)
        structor = """create table %s ( %s );"""%(cls.__name__, ','.join(temp))
        return structor

    @classmethod
    def register(cls):
        """
        add this class to table list of database
        """
        gl.g_dbtable.append(cls.table_struct())

    def format(self):
        value = [self.__dict__[item[0]] for item in self._database_struct]
        return tuple(value)




