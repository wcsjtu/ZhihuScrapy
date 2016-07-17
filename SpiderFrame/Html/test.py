# -*- coding: utf-8 -*-

import StructData
import Parser
import sys

class MyData(StructData.StructData):

    _database_struct = [('id', 'int', 'primary key'),
                        ('name', 'varchar(256)'),
                        ('age', 'int'),
                        ('gender', 'char(2)')]

    def __init__(self, id, name, age, gender):
        
        self.id = id
        self.name = name
        self.age = age
        self.gender = gender
        return super(MyData, self).__init__()
MyData.register()

if __name__ == "__main__":
    
    pp = Parser.ParserProc("html")
    stc = MyData.table_struct()
    myd = MyData(123, 'wangchao', 22, "M")
    myd2 = MyData(11, 'ff', 14, 'F')
    tmyd  =tuple(myd)
    tmyd2 = tuple(myd2)

    print 11