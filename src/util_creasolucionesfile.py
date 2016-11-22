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

solstrhdr = u"""# Costes de las MAE
# directorio de proyecto: "%s"
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
#\n\n""" # % config.proyectoactivo

solstr = u"""%s:
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

if __name__ == "__main__":
    import argparse
    import io
    import os
    import costes
    
    parser = argparse.ArgumentParser(description='Genera plantilla de costes de soluciones del proyecto')
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help='usa el archivo de configuración CONFIGFILE')
    args = parser.parse_args()

    config = costes.Config(args.configfile, args.proyectoactivo)
    projectpath = config.proyectoactivo
    print(u"* Generando archivo de soluciones del proyecto %s *" % projectpath)

    mediciones = costes.cargamediciones(config.medicionespath)
    if os.path.exists(config.costespath):
        costesdict = costes.cargacostes(config.costespath)
    else:
        costesdict = {}

    solucionesmedidas = set([solucion for medicion in mediciones for solucion in medicion.soluciones])
    
    res = []
    
    solpath = os.path.join(projectpath, 'solucionescostes-plantilla.yaml')
    with io.open(solpath, 'w', encoding='utf-8') as ofile:
        res.append(solstrhdr % projectpath)
        for solucion in sorted(solucionesmedidas):
            if solucion not in costesdict:
                print u"Solución no encontrada: %s" % solucion
            res.append(solstr % solucion)
        ofile.writelines(res)

    print (u"Archivo %s generado con %i soluciones distintas a partir "
           u"de %i variantes" % (solpath, len(solucionesmedidas), len(mediciones)))
