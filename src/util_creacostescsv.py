#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import argparse
from costes import *
import csv
import codecs

def actualizarcostesconmediciones(mediciones, costes):
    #para crear un coste Solucion(name, data) data es un diccionario con
    datacero = {'desc': "", 'vutil':0.0, 'cinicial': {'macro':0.0, 'micro':0.0}, 'creposicion':{'macro':0.0, 'micro':0.0}, 'cmant':{'macro':0.0, 'micro':0.0}}
    for medicion in mediciones:
        for solucion in medicion.soluciones.keys():
            if solucion in costes.keys():
                pass
            else:
                costes[solucion] = costes.Solucion(solucion, datacero)
    return costes

def incluircabecera(costesfile, proyectoactivo):
    solstrhdr = """# Costes de las MAE\n\
    # directorio de proyecto: "./%s/"\n\
    #\n\
    # desc: descripción de la MAE\n\
    # vutil: vida útil de la MAE (años)\n\
    # pmant: periodicidad del mantenimiento (años)\n\
    # COSTES:\n\
    # Para cada coste se deben aportar los costes:\n\
    #  - para el cálculo macroeconómico (sin impuestos ni tasas)\n\
    #  - para el cálculo financiero/microeconómico (con impuestos y tasas)\n\
    #\n\
    # cinicial: coste inicial (€/ud)\n\
    # cmant: costes de mantenimiento (€/ud·año)\n\
    #\n\n""" % proyectoactivo

    costesfile.writelines(solstrhdr)
    costesfile.writelines(u'#nombre\tvida util\tper.mant.\tPEM\tCosIni Mac\tCosIni mic\tCosRepo Mac\tCosRepo mic\tCosMant Mac\tCosMant mic\tdesc\n')

def salvarcostesencsv(mediciones, costes, proyectoactivo):
    clavescostes = costes.keys()
    lineas = []
    linea = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'
    for clave in sorted(clavescostes):
        coste = costes[clave]
        lineas.append(linea % (coste.nombre, coste.vutil, coste.pmant, '0.0', coste.cinicial['macro'], coste.cinicial['micro'], coste.creposicion['macro'], coste.creposicion['micro'], coste.cmant['macro'], coste.cmant['micro'], coste.desc))

    with open(os.path.join(proyectoactivo, 'solucionescostes.csv'), 'w') as costesfile: #de hecho es utf8, es como lo lee bien libreoffice
        incluircabecera(costesfile, proyectoactivo)
        costesfile.writelines(lineas)

def salvarenyaml(solucionesmedidas, proyectoactivo):
    solpath = os.path.join(proyectoactivo, 'solucionescostes_decsv.yaml')

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
    #\n\n""" % proyectoactivo

    #solstr = """%s:
    #desc: Descripción de la solución
    #vutil: 50 #años
    #pmant: 10 #años
    #cinicial:
        #macro: 0.0 # €/m2
        #micro: 0.0 # €/m2
    #cmant:
        #macro: 0.0 # €/m2
        #micro: 0.0 # €/m2
    #"""

    res = []
    with codecs.open(solpath, 'w', 'utf8') as ofile:
        res.append(solstrhdr)
        print 'exportando a yaml'
        print solucionesmedidas.keys()
        for solucion in sorted(solucionesmedidas.keys()):
            ofile.writelines(solucionesmedidas[solucion].cadenayaml())


def convertirCSVenyaml(proyectoactivo):
    print 'convertir en yaml', proyectoactivo
    solucionesmedidas = {}
    with codecs.open(os.path.join(proyectoactivo, 'solucionescostes_ed.csv'), 'r', 'latin1') as costesfile:
        linea = costesfile.readline()
        while linea:
            if '#' in linea:
                linea = costesfile.readline()
                continue
            celdas = linea.strip('\n\r ').split('\t')
            if celdas[0] == '':
                linea = costesfile.readline()
                continue
            [nombre, vutil, pmant, PEM, Mcinicial, mcinicial, Mcrepo, mcrepo, Mcmant, mcmant, desc] = celdas[0:11]
            linea = costesfile.readline()
            if nombre == 'testigo':
                continue
            else:
                print '__de csv__', nombre
                data = {'desc': "", 'vutil': vutil, 'pmant': pmant, 'cinicial': {'macro': Mcinicial, 'micro': mcinicial}, 'creposicion':{'macro': Mcrepo, 'micro': mcrepo}, 'cmant':{'macro': Mcmant, 'micro': mcmant}}
                solucionesmedidas[nombre] = Solucion(nombre, data)
            #print celdas
            linea = costesfile.readline()
        salvarenyaml(solucionesmedidas, proyectoactivo)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Trabaja con los ficheros de costes')
    parser.add_argument('-v', action='store_true', dest='is_verbose', help='salida detallada', default=True)
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='../config.yaml',
                        metavar='CONFIGFILE',
                        help='usa el archivo de configuración CONFIGFILE')
    parser.add_argument('--ayaml', action='store_true', dest='ayaml', help='traduce de csv a yaml')
    parser.add_argument('--acsv', action='store_true',  dest='acsv', help='traduce de yaml a csv')
    args = parser.parse_args()
    VERBOSE = args.is_verbose
    config = Config('./config.yaml')
    params = parser.parse_args()

    if params.acsv:
        if VERBOSE: print 'cargando mediciones'
        mediciones = cargamediciones(config.medicionespath) # son las mediciones que ha hecho sisgen
        if os.path.exists(config.costespath):
            costes = cargacostes(config.costespath) #este carga los costes en yaml, no csv.
        else:
            costes = {}
        if VERBOSE: print 'actualizando costes'
        costes = actualizarcostesconmediciones(mediciones, costes)
        if VERBOSE: print 'salvando costes'
        salvarcostesencsv(mediciones, costes, config.proyectoactivo)
    if params.ayaml:
        convertirCSVenyaml(config.proyectoactivo)

