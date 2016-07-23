# -*- coding: utf-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage



class Courier(object):
    """send and recieve email"""
    
    def __init__(self, host, port, username, password):
        """
        constructor
        @parameters: host, domain name or ipaddress of smtp server. eg. 'smtp.163.com'
                     port, port of smtp server. default port of NetEase's smtp server, which based on SSL, is 465 or 994 
                     username and password are the account information at the smtp server above
        """
        self.host = host
        self.port = port
        self.username = username
        self.pswd = password
        self.courier = None
        self.is_quit = False
        
        
    def send(self, msg):
        pass
        
    def recv(self):
        """"""
        pass

    def message(self, **kwargs):
        """create mime message to send"""





