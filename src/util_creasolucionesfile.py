#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Cálculo de costes para estudio de coste óptimo
#
# DB-HE 2013
#
"""Generador de archivo inicial de costes de soluciones

Toma un archivo de mediciones del proyecto activo y genera un archivo
plantilla de costes de soluciones.
"""

import io
import os.path
from costes import *

config = Config('./config.yaml')
mediciones = cargamediciones(config.medicionespath)
if os.path.exists(config.costespath):
    costes = cargacostes(config.costespath)
else:
    costes = {}

solucionesmedidas = set([solucion for medicion in mediciones for solucion in medicion.soluciones])

solpath = os.path.join(config.proyectoactivo, 'solucionescostes-plantilla.yaml')

solstrhdr = """# Costes de las MAE
# directorio de proyecto: "./%s/"
#
# desc: descripción de la MAE
# vutil: vida útil de la MAE (años)
# pmant: periodicidad del mantenimiento (años)
# COSTES:
# Para cada coste se deben aportar los costes:
#  - para el cálculo macroeconómico (sin impuestos ni tasas)
#  - para el cálculo financiero/microeconómico (con impuestos y tasas)
#
# cinicial: coste inicial (€/ud)
# cmant: costes de mantenimiento (€/ud·año)
#\n\n""" % config.proyectoactivo

solstr = """%s:
  desc: Descripción de la solución
  vutil: 50 #años
  pmant: 10 #años
  cinicial:
    macro: 0.0 # €/m2
    micro: 0.0 # €/m2
  cmant:
    macro: 0.0 # €/m2
    micro: 0.0 # €/m2

"""

res = []
with io.open(solpath, 'w', encoding='utf-8') as ofile:
    res.append(solstrhdr)
    for solucion in sorted(solucionesmedidas):
        if solucion not in costes:
            print "Solución no encontrada: %s" % solucion
        res.append(solstr % solucion)
    ofile.writelines(res)

print ("Archivo %s generado con %i soluciones distintas a partir "
       "de %i variantes" % (solpath, len(solucionesmedidas), len(mediciones)))
