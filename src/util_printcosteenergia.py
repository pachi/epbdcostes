#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Cálculo de costes para estudio de coste óptimo
#
# DB-HE 2013
#

import os.path
from costes import *

parametrospath = '../proyectos/proyectotest/parametroscostes.yaml'

e10f = Escenario('micro', 10, parametrospath)
e10m = Escenario('macro', 10, parametrospath)
e6f = Escenario('micro', 6, parametrospath)

escenarios = [e10f, e10m, e6f]

print u"Costes de la energía por escenario"
print '-'*74
for escenario in escenarios:
    print '-'*6, escenario, '-'*6
    for combustible in ('gasoleoc', 'electricidad'):
        print u"Combustible:", combustible
        print escenario.preciosenergia[combustible]
        print escenario.preciosbaseenergia[escenario.tipo][combustible]
        print u"TOTAL:", sum(escenario.preciosenergia[combustible])
        print

