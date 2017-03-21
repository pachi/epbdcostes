#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Recoge los archivos CSV de los datapoint de cada proyecto

Usa el directorio proyectos/NOMBREPROYECTO/variantesbase como destino."""

from __future__ import print_function
import os
import os.path
import argparse
import shutil
from costes import Config

# Directorio de proyectos de suspat
SUSPATPRJDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '../../suspat/proyectos')
DEFAULTBASEPATH = os.path.abspath(os.path.join('..', 'proyectos'))

def csvpaths(proyecto, suspatdir=SUSPATPRJDIR):
    """Devuelve archivos csv de los datapoint del proyecto"""
    proyecto_path = os.path.join(suspatdir, proyecto)
    dataPointDirs = [d for d in os.listdir(proyecto_path)
                     if (os.path.isdir(os.path.join(proyecto_path, d)) and
                         d.startswith('dataPoint'))]
    results, errors = [], []
    for dataPoint in sorted(dataPointDirs):
        dataPoint_path = os.path.abspath(os.path.join(proyecto_path, dataPoint))
        try:
            csvfile = next(ff for ff in os.listdir(dataPoint_path) if ff.endswith('.csv'))
            results.append(os.path.join(dataPoint_path, csvfile))
        except Exception:
            if VERBOSE: print("- Sin archivo csv en \"%s\", (%s)" % (proyecto, dataPoint))
            errors.append(dataPoint)
    return results, errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recoge csv para variantesbase')
    parser.add_argument('-v', action='store_true', dest='is_verbose', help='salida detallada', default=False)
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('-a', '--all', action='store_true', dest='is_allprojects', default=False)
    parser.add_argument('-d', '--deleteexisting', action='store_true', dest='is_deleteexisting', default=True)
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help='usa el archivo de configuración CONFIGFILE')
    args = parser.parse_args()
    VERBOSE = args.is_verbose
    config = Config(args.configfile, args.proyectoactivo)
    params = parser.parse_args()


    if args.proyectoactivo:
        if VERBOSE: print("Localizando proyecto indicado")
        prjlist = [args.proyectoactivo]
    elif args.is_allprojects:
        if VERBOSE: print("Localizando proyectos en directorio de susPAT")
        proyectos = [d for d in os.listdir(SUSPATPRJDIR)
                     if os.path.isdir(os.path.join(SUSPATPRJDIR, d)) and
                     not d.startswith('scripts')]
        prjlist = proyectos
    else:
        if VERBOSE: print("Localizando proyecto por defecto")
        prjlist = [config.proyectoactivo]

    print("%i proyecto(s) encontrado(s)" % len(prjlist))

    for prj in prjlist:
        print("* Procesando proyecto \"%s\"" % prj)
        prjdir = os.path.join(DEFAULTBASEPATH, prj)
        config.proyectoactivo = prjdir
        if not os.path.isdir(prjdir):
            print("\t- Creando directorio de proyecto: %s" % prjdir)
            os.mkdir(prjdir)
        if os.path.isdir(config.variantesbasedir) and args.is_deleteexisting:
            existingcsv = [d for d in os.listdir(config.variantesbasedir) if d.endswith('.csv')]
            print("\t- Eliminando %i variantes base existentes" % len(existingcsv))
            for ff in existingcsv:
                os.remove(os.path.join(config.variantesbasedir, ff))
        if not os.path.isdir(config.variantesbasedir):
            print("\t- Creando directorio de variantes base")
            os.mkdir(config.variantesbasedir)
        prjcsvpaths, prjcsverrors = csvpaths(prj)
        if prjcsverrors:
            print("\t- ¡AVISO!: faltan %i archivos csv del proyecto" % len(prjcsverrors))
        print("\t- Copiando %i archivo(s) csv" % len(prjcsvpaths))
        for csvfile in prjcsvpaths:
            shutil.copyfile(csvfile,
                            os.path.join(config.variantesbasedir,
                                         os.path.basename(csvfile)))
