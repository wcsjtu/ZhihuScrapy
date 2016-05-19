# -*- coding: utf-8 -*-

import cv2
import numpy


def show_captcha():
    ''''''
    try:
        captcha = cv2.imread('captcha.gif')
        cv2.imshow('captcha', captcha)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception, e:
        return False
