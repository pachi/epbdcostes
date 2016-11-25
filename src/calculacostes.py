#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Cálculo de costes para estudio de coste óptimo
# 2013-2016 Rafael Villar Burke, <pachi@ietcc.csic.es>
#
# DB-HE 2013
#
"""Generación de archivos de costes para estudio de coste óptimo"""

import io
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
    reslines = []
    reslines.append(u"# Resultados de cálculos de costes\n")
    reslines.append(u"# variante_id, escenario, tasa, periodo, costetotal, costeinicial, "
                    u"costemantenimiento, costereposicion, costeoperacion, costeco2, vresidual,"
                    u"cGASNATURAL, cELECTRICIDAD, cELECTRICIDADBALEARES, cELECTRICIDADCANARIAS, "
                    u"cELECTRICIDADCEUTAMELILLA, cBIOCARBURANTE, cBIOMASA, "
                    u"cBIOMASADENSIFICADA, cCARBON, cFUELOIL, cGASOLEO, cGLP, cRED1, cRED2\n")
    for variante in mediciones:
        if VERBOSE:
            print u"\n* Variante (id=%s)" % variante.id
        for escenario in escenarios:
            ctotal = coste(variante, escenario, costes)
            civ = costeinicial(variante, escenario, costes)
            cmv = costemantenimiento(variante, escenario, costes)
            crv = costereposicion(variante, escenario, costes)
            copv = costesoperacion(variante, escenario)
            cop = sum(copv[combustible] for combustible in copv)
            coco2 = costeco2(variante, escenario)
            vresidual = valorresidual(variante, escenario, costes)
            cGASNATURAL = copv[u'GASNATURAL']
            cELECTRICIDAD = copv[u'ELECTRICIDAD']
            cELECTRICIDADBALEARES = copv[u'ELECTRICIDADBALEARES']
            cELECTRICIDADCANARIAS = copv[u'ELECTRICIDADCANARIAS']
            cELECTRICIDADCEUTAMELILLA = copv[u'ELECTRICIDADCEUTAMELILLA']
            cBIOCARBURANTE = copv[u'BIOCARBURANTE']
            cBIOMASA = copv[u'BIOMASA']
            cBIOMASADENSIFICADA = copv[u'BIOMASADENSIFICADA']
            cCARBON = copv[u'CARBON']
            cFUELOIL = copv[u'FUELOIL']
            cGASOLEO = copv[u'GASOLEO']
            cGLP = copv[u'GLP']
            cRED1 = copv[u'RED1']
            cRED2 = copv[u'RED2']

            if not checksum(ctotal, civ, cmv, crv, cop, coco2, vresidual):
                print variante
                print escenario
                raise Exception("La suma de costes no coincide con el total ctotal != civ + cmv + crv + cop + coco2 - vresidual !!")
            if VERBOSE:
                msg = (u"\tCoste total (%s, %i%%, %i años): %.2f, Coste inicial: %.2f, Cmant: %.2f, "
                       u"Crepo: %.2f, Cop: %.2f, CosteCO2: %.2f, Vresidual: %.2f\n"
                       u"cGASNATURAL: %.2f, cELECTRICIDAD: %.2f, "
                       u"cELECTRICIDADBALEARES: %.2f, cELECTRICIDADCANARIAS: %.2f, cELECTRICIDADCEUTAMELILLA: %.2f, "
                       u"cBIOCARBURANTE: %.2f, cBIOMASA: %.2f, cBIOMASADENSIFICADA: %.2f, cCARBON: %.2f, "
                       u"cFUELOIL: %.2f, cGASOLEO: %.2f, cGLP: %.2f, cRED1: %.2f, cRED2: %.2f") % (
                           escenario.tipo, escenario.tasa, escenario.periodo,
                           ctotal, civ, cmv, crv, cop, coco2, vresidual,
                           cGASNATURAL, cELECTRICIDAD, cELECTRICIDADBALEARES, cELECTRICIDADCANARIAS, cELECTRICIDADCEUTAMELILLA,
                           cBIOCARBURANTE, cBIOMASA, cBIOMASADENSIFICADA, cCARBON, cFUELOIL, cGASOLEO, cGLP, cRED1, cRED2
                       )
                print(msg)
            dataline = u"%s, %s, %i, %i, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f\n" % (
                variante.id, escenario.tipo, escenario.tasa, escenario.periodo,
                ctotal, civ, cmv, crv, cop, coco2, vresidual,
                cGASNATURAL, cELECTRICIDAD, cELECTRICIDADBALEARES, cELECTRICIDADCANARIAS, cELECTRICIDADCEUTAMELILLA,
                cBIOCARBURANTE, cBIOMASA, cBIOMASADENSIFICADA, cCARBON, cFUELOIL, cGASOLEO, cGLP, cRED1, cRED2
            )
            reslines.append(dataline)

    with io.open(os.path.join(config.basedir, 'resultados-costes.csv'), 'w', encoding='utf-8') as resfile:
        resfile.writelines(reslines)
    # Devuelve número de casos calculados
    return len(reslines)-2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=u'Calcula costes del proyecto activo para los escenarios configurados')
    parser.add_argument('-v', action='store_true', dest='is_verbose', help='salida detallada')
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help=u'usa el archivo de configuración CONFIGFILE')
    parser.add_argument('--todas', action='store_true', dest='generarlas_todas', default=False)
    args = parser.parse_args()
    VERBOSE = args.is_verbose

    if args.generarlas_todas:
        proyectos = ['proyecto_puertoreal', 'proyecto_elviso', 'proyecto_arrahona', 'proyectoGirona', 'proyectoPPV', 'proyecto_exupery']
        print u'Generando archivo de costes para todos los proyectos', ', '.join(proyectos)
        print
    else:
        proyectos = [args.proyectoactivo]
        print u'Generando archivo de costes para el proyecto', args.proyectoactivo
        print

    for proyectoactivo in proyectos:
        config = Config(args.configfile, proyectoactivo)

        print u"* Cálculo de costes del proyecto %s *" % config.proyectoactivo
        print u"\tCargando costes: ", config.costespath
        costes = cargacostes(config.costespath)
        print u"\tCargando mediciones: ", config.medicionespath
        mediciones = cargamediciones(config.medicionespath, costes)
        escenarios = [Escenario(tipo, tasa, config.costesconfigpath)
                      for tipo in config.escenarios
                      for tasa in config.escenarios[tipo]]
        print u"\tDefinidos %i escenarios" % len(escenarios)
        print u"\tCalculando costes..."
        numcasos = calculacostes(config, costes, mediciones, escenarios)
        print u"Calculados %i casos del proyecto activo: %s" % (numcasos,
                                                                config.proyectoactivo)

