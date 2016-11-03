#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Cálculo de costes para estudio de coste óptimo
# 2013 Rafael Villar Burke, <pachi@ietcc.csic.es>
#
# DB-HE 2013
#
"""Generación de archivos de costes para estudio de coste óptimo"""

import os.path
import argparse
from costes import *

VERBOSE = False
config = Config('./config.yaml')

def checksum(cv, civ, cmv, crv, cop, coco2, vresidual):
    """comprobación para verificar que todos los costes suman bien"""
    calc1 = (civ + cmv + crv + cop + coco2 - vresidual)
    dif = cv - calc1
    if abs(dif) > 0.1:
        print "Error al calcular costes, diferencia injustificada:", dif
        return False
    else:
        return True

def calculacostes(config, costes, mediciones, escenarios):
    """Calcula costes para la configuración y los escenarios indicados"""
    txt = ("\tCoste (%s, %i%%): %.2f, Coste inicial: %.2f, Cmant: %.2f, "
           "Crepo: %.2f, Cop: %.2f, Copgas: %.2f, Copele: %.2f, CCO2: %.2f, Vresidual: %.2f, periodo: %i")
    ftxt = "%s, %s, %i, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %i\n"
    reslines = []
    reslines.append("# Resultados de cálculos de costes\n")
    reslines.append("# variante_id, escenario, tasa, coste, costeinicial, "
                    "costemantenimiento, costereposicion, operacion, "
                    "operaciongasoleoc, operacionelec, costeco2, vresidual, periodo\n")
    for variante in mediciones:
        if VERBOSE:
            print "\n* Variante (id=%s)" % variante.id
        for escenario in escenarios:
            cv = coste(variante, escenario, costes)
            civ = costeinicial(variante, escenario, costes)
            cmv = costemantenimiento(variante, escenario, costes)
            crv = costereposicion(variante, escenario, costes)
            copv = costesoperacion(variante, escenario)
            copgas = copv['gasoleoc']
            copele = copv['electricidad']
            cop = sum(copv[combustible] for combustible in copv)
            vresidual = valorresidual(variante, escenario, costes)
            coco2 = costeco2(variante, escenario)
            periodo = escenario.periodo # duración del periodo de cálculo
            if not checksum(cv, civ, cmv, crv, cop, coco2, vresidual):
                print variante
                print escenario
                print txt % (escenario.tipo, escenario.tasa,
                             cv, civ, cmv, crv, cop, copgas,
                             copele, coco2, vresidual, periodo), "\nCoste CO2:", coco2
                raise
            if VERBOSE:
                print txt % (escenario.tipo, escenario.tasa,
                             cv, civ, cmv, crv, cop, copgas, copele, coco2, vresidual, periodo)
            reslines.append(ftxt % (variante.id, escenario.tipo, escenario.tasa,
                                    cv, civ, cmv, crv, cop, copgas, copele, coco2, vresidual, periodo))

    dirname = os.path.dirname(config.resultadospath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(config.resultadospath, 'w') as resfile:
        resfile.writelines(reslines)
    # Devuelve número de casos calculados
    return len(reslines)-2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calcula costes del proyecto activo para los escenarios configurados')
    parser.add_argument('-v', action='store_true', dest='is_verbose', help='salida detallada')
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help='usa el archivo de configuración CONFIGFILE')
    parser.add_argument('--todas', action='store_true', dest='generarlas_todas', default=False)
    args = parser.parse_args()
    VERBOSE = args.is_verbose

    if args.generarlas_todas:
        proyectos = ['proyecto_puertoreal', 'proyecto_elviso', 'proyecto_arrahona', 'proyectoGirona', 'proyectoPPV', 'proyecto_exupery']
        print 'Generando archivo de costes para todos los proyectos', ', '.join(proyectos)
        print
    else:
        proyectos = [args.proyectoactivo]
        print 'Generando archivo de costes para el proyecto', args.proyectoactivo
        print

    for proyectoactivo in proyectos:
        config = Config(args.configfile, proyectoactivo)

        print "* Cálculo de costes del proyecto %s *" % config.proyectoactivo
        print "\tCargando costes: ", config.costespath
        costes = cargacostes(config.costespath)
        print "\tCargando mediciones: ", config.medicionespath
        mediciones = cargamediciones(config.medicionespath, costes)
        escenarios = [Escenario(tipo, tasa, config.parametrospath)
                      for tipo in config.escenarios
                      for tasa in config.escenarios[tipo]]
        print "\tDefinidos %i escenarios" % len(escenarios)
        print "\tCalculando costes..."
        numcasos = calculacostes(config, costes, mediciones, escenarios)
        print "Calculados %i casos del proyecto activo: %s" % (numcasos,
                                                               config.proyectoactivo)

