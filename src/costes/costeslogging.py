#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Librería de cálculo de costes
#
# DB-HE 2013
#

import logging

def setup(logfilename='costes.log', name='costes'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.WARN)

    filelog = logging.FileHandler(logfilename, 'a')
    conlog = logging.StreamHandler()
    filelog.setLevel(logging.WARN)
    conlog.setLevel(logging.ERROR)

    _fmt = u"%(asctime)s - %(levelname)s: %(message)s"
    _datefmt = u"%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(_fmt, _datefmt)
    conlog.setFormatter(formatter)
    filelog.setFormatter(formatter)

    logger.addHandler(conlog)
    logger.addHandler(filelog)

    return logger
