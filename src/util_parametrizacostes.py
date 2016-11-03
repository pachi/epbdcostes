#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Parametrización de costes para estudio de coste óptimo
#
# DB-HE 2013
#

"""Cálculo de costes de soluciones por interpolación de soluciones existentes

   $ parametrizacostes.py -h para ayuda de uso

Ejemplo:

$ python parametrizacostes.py -v -p proyectoGirona

#TODO: Ver si se quiere pasar lista de valores del parámetro para calcular en todos los casos
#TODO: Ver si se quiere volcar a archivo el resultado, ya en yaml, para reusar en calculacostes
"""

import argparse
import re
import os.path
from collections import defaultdict
from numpy import polyfit, array, poly1d
from costes import *

VALIDSUFFIXES = ('05', '10', '15', '20')

def findkeys(costes):
    """Localiza claves de soluciones parametrizables en base de datos de costes"""
    def hasvalidsuffix(key):
        "Valen las claves con sufijos válidos acabados opcionalmente en 'i' o 'e'"
        if key.rstrip('ei')[-2:] in VALIDSUFFIXES:
            return True
        else:
            return False
    return [key for key in costes if hasvalidsuffix(key)]

def findgroups(keys):
    """Localiza grupos en las claves y guarda clave y parámetro de cada grupo"""
    prefixes = defaultdict(dict)
    for key in keys:
        prefix = key.rstrip('ei' + ''.join(VALIDSUFFIXES))
        suffix = key[len(prefix):]
        suffixval = suffix.strip('ei')
        suffixtail = suffix[len(suffixval):len(suffix)]
        paramval = int(suffixval)
        abstractkey = prefix + '$'*len(suffixval) + suffixtail
        d = prefixes[abstractkey]
        if 'claves' not in d:
            d['claves'] = {}
        d['claves'][key] = paramval
    return prefixes

def computecosts(groups, costes):
    """Completa información y funciones para ajuste de costes

    Los costes inicial y de mantenimiento se ajustan usando un polinomio
    del grado más alto posible con los puntos disponibles. Se obliga al
    paso por el punto (0,0).

    En los costes se almacenan los coeficientes de ajuste. Se puede obtener
    un valor para el coste usando numpy.poly1d(coefs)(x) siendo x el
    parámetro deseado (normalmente espesor de aislamiento).
    """
    for groupname in groups:
        group = groups[groupname]
        keys = sorted(group['claves'].keys())
        degree = len(keys) # añadimos el punto (0,0) -> se incrementa el grado
        X = array([0] + [group['claves'][key] for key in keys])
        Ycinicialmacro =  array([0.0] + [costes[key].cinicial['macro'] for key in keys])
        Ycinicialmicro =  array([0.0] + [costes[key].cinicial['micro'] for key in keys])
        Ycmantmacro =  array([0.0] + [costes[key].cmant['macro'] for key in keys])
        Ycmantmicro =  array([0.0] + [costes[key].cmant['micro'] for key in keys])

        sol0 = costes[keys[0]]
        group['desc'] = sol0.desc
        group['vutil'] = sol0.vutil
        group['pmant'] = sol0.pmant
        group['cinicial'] = {'macro': polyfit(X, Ycinicialmacro, degree),
                             'micro': polyfit(X, Ycinicialmicro, degree)}
        group['cmant'] = {'macro': polyfit(X, Ycmantmacro, degree),
                          'micro': polyfit(X, Ycmantmicro, degree)}
    return groups

def getsolforparam(name, sol, x):
    """Obtiene diccionario de datos de la solución genérica para el valor x del parámetro"""
    res = {'desc': sol['desc'], 'vutil': sol['vutil'], 'pmant': sol['pmant'],
           'cinicial': {'macro': round(poly1d(sol['cinicial']['macro'])(x), 2),
                        'micro': round(poly1d(sol['cinicial']['micro'])(x), 2)},
           'cmant': {'macro': round(poly1d(sol['cmant']['macro'])(x), 2),
                     'micro': round(poly1d(sol['cmant']['micro'])(x), 2)}
    }
    nombre = name.replace('$$', "%02i" % x)
    return nombre, res

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parametrización de costes')
    parser.add_argument('-v', action='store_true', dest='is_verbose',
                        help='salida detallada')
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo',
                        metavar='PROYECTO',
                        help='cambia el proyecto activo a PROYECTO')
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help='usa el archivo de configuración CONFIGFILE')
    args = parser.parse_args()

    VERBOSE = args.is_verbose
    config = Config(args.configfile, args.proyectoactivo)

    print "* Parametrización de costes del proyecto %s *" % config.proyectoactivo
    print "\tCargando costes: ", config.costespath
    costes = cargacostes(config.costespath)

    keys = findkeys(costes)
    groups = findgroups(keys)
    groups = computecosts(groups, costes)

    if VERBOSE:
        print keys
        print groups
    msg = "Localizados %i grupos con %i soluciones (%i soluciones definidas)"
    print msg % (len(groups), len(keys), len(costes))

    # Imprime los valores de una solución
    # Con estos datos se puede construir una solución Solucion(solname, soldata)
    name, data = groups.iteritems().next() # Tomamos un elemento de los disponibles
    solname, soldata = getsolforparam(name, data, 5) # Calculamos los costes para parámetro = 5
    print "Cálculo de la solución genérica %s, para el valor del parámetro = %i -> %s" % (name, 5, solname)
    print "Diccionario para construir la solución: Solucion(name, data):\n", soldata
