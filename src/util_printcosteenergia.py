#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Cálculo de costes para estudio de coste óptimo
#
# DB-HE 2013
#

import sys
import os.path
from costes import *

if len(sys.argv) == 2:
    parametrospath = sys.argv[1]
else:
    parametrospath = '../proyectos/proyectotest/costes_config.yaml'

e7f = Escenario('micro', 7, parametrospath)
e10f = Escenario('micro', 10, parametrospath)
#e10m = Escenario('macro', 10, parametrospath)

ESCENARIOS = [e7f, e10f]
COMBUSTIBLES = ['GASNATURAL', 'ELECTRICIDAD', 'ELECTRICIDADBALEARES', 'ELECTRICIDADCANARIAS', 'ELECTRICIDADCEUTAMELILLA',
                'BIOCARBURANTE', 'BIOMASA', 'BIOMASADENSIFICADA', 'CARBON', 'FUELOIL', 'GASOLEO', 'GLP']

TITLE1 = u"Costes de la energía por escenario".upper()

print TITLE1
print '-' * len(TITLE1)
print

for escenario in ESCENARIOS:
    TITLESEC = "%s" % escenario
    print TITLESEC + "\n" + '-' * len(TITLESEC) + "\n"
    for combustible in COMBUSTIBLES:
        print u"Combustible: %s (escenario: %s, periodo: %s años, año base: %s)" % (combustible, escenario.tipo, escenario.periodo, escenario.base)
        print ", ".join(["%.3f" % pp for pp in escenario.preciosenergia[combustible]])
        #print escenario.preciosbaseenergia[escenario.tipo][combustible]
        print u"SUMA TOTAL PERIODO: %.3f" % sum(escenario.preciosenergia[combustible])
        print

