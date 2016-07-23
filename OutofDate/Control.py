# -*- coding: utf-8 -*-

from HttpClient import *
import Global
import ErrorCode


cmd_func = {'quit': 'quit()',	#stop this proc
			'lstd':	'show_thread()', #
			'crt td quest': 'create_thread()', 
			'lsqsz': 'show_qsize()'			
			}


class Control(object):
    """work in main thread. and wait for user's command to do something"""
    def __init__(self):
        self.srt_td = []
        self.qst_td = []
        self.usr_td = []
        self.rtv_td = []
        self.cmt_td = []

        self.lst_tb = {'question': self.qst_td,
                      'usr': self.usr_td,
                      'retrieve': self.rtv_td,
                      'comment': self.cmt_td,
                      'SearchEngine': self.srt_td}
        self.cls_tb = {'question': QuestionAbs,
                      'usr': UserAbs,
                      'retrieve': RetrieveAgent,
                      'comment': CommentAbs,
                      'SearchEngine': SearchEngine
                      }

    def init_task(self, kw='site:zhihu.com/question', std=1 ,qtd=2, utd=3, rtd=1, ctd=0):
        """
        @param: qtd, int. thread count of question parser. default value is 2
                utd, int. thread count of user information parser. default value is 3
                rtd, int. thread count of downloader. default value is 1
                ctd, int. thread count of comment parser. default value is 0
                ATTENTION: all kinds of thread's upper limit is 9         
        """
        if std > 1: std = 1
        try:
            for i in xrange(std):
            	self.srt_td.append(SearchEngine('', kw))
            for i in xrange(qtd):
                self.qst_td.append( QuestionAbs('question%d'%i) )
            for i in xrange(utd):
                self.usr_td.append( UserAbs('usr%d'%i) )
            for i in xrange(rtd):
                self.rtv_td.append( RetrieveAgent('retrieve%d'%i) )
            for i in xrange(ctd):
                self.cmt_td.append( CommentAbs('comment%d'%i) )
        except Exception, e: 
            pass

    def show_thread(self):
        """list all the threads' information """
        print 'ThreadName		 IsAlive\n'
        self._format_td(self.srt_td)
        self._format_td(self.qst_td)
        self._format_td(self.usr_td)
        self._format_td(self.rtv_td)
        self._format_td(self.cmt_td)
        print ''

    def create_thread(self, tdn, tdc=1):
        """
        create thread
        @params: tdn, string ,name of thread
                 tdc, int, count of thread need to be create, default value is i
        """
        td_list = self.lst_tb[tdn]
        l = len(td_list)
        for i in xrange(l, l+tdc):
            self.lst_tb[tdn].append(self.cls_tb[tdn](tdn+str(i)))



    def _format_td(self, td_list):
        """"""
        for td in td_list:
            print '%s			%s'%(td.name, td.isAlive() )

    def show_qsize(self):
        """print queue size of Queue in Global module"""
        print 'QueueName				Size\n'
        print 'g_question_queue			%d'%Global.g_question_queue.qsize()
        print 'g_img_queue				%d'%Global.g_img_queue.qsize()
        print 'g_user_queue				%d'%Global.g_user_queue.qsize()
        print 'g_data_queue             %d'%Global.g_data_queue.qsize()
        print 'g_answer_comment_queue	%d'%Global.g_answer_comment_queue.qsize()        
        print ''

    def active_thread(self, td):
        """
        reactive the thread which is not alive
	    @param: td, string. name of thread, such as 'question0'
        """
        index = int(td[-1])
        name = td[:-1]
        if not self.lst_tb[name][index].isAlive():
            self.lst_tb[name][index] = self.cls_tb[name]( name+str(index) )
        else:
            print '%s is still alive'%td


    def quit(self):
        """notify all the thread to stop by sequence, it may take some time"""
        Global.g_question_exit = True


    def wait_cmd(self):
        """the loop wouldn't exit until user input command `quit`"""
        tips = 'root@linux~$ ' if Global.sys_ == 'Linux' else '>>> '
        while True:
            cmd = raw_input(tips)
            try:
                if cmd == 'lstd':
                    self.show_thread()
                elif cmd == 'lsqsz':
                    self.show_qsize()
                elif 'sttd ' in cmd :
                    td = cmd.split(' ')[1]
                    self.active_thread(td)
                elif cmd == 'quit':
                    self.quit()    
                elif cmd == '':
                    continue
            except Exception, e: 
                print 'Invalid command'


