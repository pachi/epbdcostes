#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Cálculo de costes para estudio de coste óptimo
# 2013-2016 Rafael Villar Burke, <pachi@ietcc.csic.es>
#
# DB-HE 2013
#
"""Generación de archivos de costes para estudio de coste óptimo"""

from __future__ import print_function
import io
import os.path
import argparse
import costes

VERBOSE = False

def checksum(cv, civ, cmv, crv, cop, coco2, vresidual):
    """comprobación para verificar que todos los costes suman bien"""
    calc1 = (civ + cmv + crv + cop + coco2 - vresidual)
    dif = cv - calc1
    if abs(dif) > 0.1:
        print(u"Error al calcular costes, diferencia injustificada: %s" % dif)
        return False
    else:
        return True

def calculacostes(config, costesdata, mediciones, escenarios):
    """Calcula costes para la configuración y los escenarios indicados"""
    reslines = []
    reslines.append(u"variante_id, fechacalculo, tipoedificio, usoedificio, "
                    u"superficie, volumen, zc, peninsular, "
                    u"eptot, epnren, epren, "
                    u"escenario, tasa, periodo, "
                    u"costetotal, costeinicial, costemantenimiento, costereposicion, costeoperacion, costeco2, vresidual, "
                    u"cGASNATURAL, cELECTRICIDAD, cELECTRICIDADBALEARES, cELECTRICIDADCANARIAS, "
                    u"cELECTRICIDADCEUTAMELILLA, cBIOCARBURANTE, cBIOMASA, "
                    u"cBIOMASADENSIFICADA, cCARBON, cFUELOIL, cGASOLEO, cGLP, "
                    u"cRED1, cRED2\n")
    for variante in sorted(mediciones):
        if VERBOSE:
            print(u"\n* Variante (id=%s)" % variante.id)
        for escenario in escenarios:
            ctotal = costes.coste(variante, escenario, costesdata)
            civ = costes.costeinicial(variante, escenario, costesdata)
            cmv = costes.costemantenimiento(variante, escenario, costesdata)
            crv = costes.costereposicion(variante, escenario, costesdata)
            copv = costes.costesoperacion(variante, escenario)
            cop = sum(copv[combustible] for combustible in copv)
            coco2 = costes.costeco2(variante, escenario)
            vresidual = costes.valorresidual(variante, escenario, costesdata)
            if not checksum(ctotal, civ, cmv, crv, cop, coco2, vresidual):
                print(variante)
                print(escenario)
                raise Exception("La suma de costes no coincide con el total ctotal != civ + cmv + crv + cop + coco2 - vresidual !!")
            if VERBOSE:
                msg = (u"\tCoste total ({escenario.tipo}, {escenario.tasa:.2f}%, {escenario.periodo:d} años): {ctotal:.2f}, "
                       u"Coste inicial: {civ:.2f}, Cmant: {cmv:.2f}, "
                       u"Crepo: {crv:.2f}, Cop: {cop:.2f}, CosteCO2: {coco2:.2f}, Vresidual: {vresidual:.2f}\n"
                       u"cGASNATURAL: {copv[GASNATURAL]:.2f}, cELECTRICIDAD: {copv[ELECTRICIDAD]:.2f}, "
                       u"cELECTRICIDADBALEARES: {copv[ELECTRICIDADBALEARES]:.2f}, cELECTRICIDADCANARIAS: {copv[ELECTRICIDADCANARIAS]:.2f}, "
                       u"cELECTRICIDADCEUTAMELILLA: {copv[ELECTRICIDADCEUTAMELILLA]:.2f}, "
                       u"cBIOCARBURANTE: {copv[BIOCARBURANTE]:.2f}, cBIOMASA: {copv[BIOMASA]:.2f}, "
                       u"cBIOMASADENSIFICADA: {copv[BIOMASADENSIFICADA]:.2f}, cCARBON: {copv[CARBON]:.2f}, "
                       u"cFUELOIL: {copv[FUELOIL]:.2f}, cGASOLEO: {copv[GASOLEO]:.2f}, cGLP: {copv[GLP]:.2f}, "
                       u"cRED1: {copv[RED1]:.2f}, cRED2: {copv[RED2]:.2f}"
                   ).format(escenario=escenario, ctotal=ctotal, civ=civ, cmv=cmv, crv=crv, cop=cop, coco2=coco2, vresidual=vresidual, copv=copv)
                print(msg)
            dataline = (u"{variante.id}, {variante.metadatos[fechacalculo]}, {variante.metadatos[tipoedificio]}, {variante.metadatos[usoedificio]}, "
                        u"{variante.metadatos[superficie]:.2f}, {variante.metadatos[volumen]:.2f}, {variante.metadatos[zc]}, {variante.metadatos[peninsular]}, "
                        u"{variante.eprimaria[EP_tot]:.2f}, {variante.eprimaria[EP_nren]:.2f}, {variante.eprimaria[EP_ren]:.2f}, "
                        u"{escenario.tipo}, {escenario.tasa:.2f}, {escenario.periodo:d}, "
                        u"{ctotal:.2f}, {civ:.2f}, {cmv:.2f}, {crv:.2f}, {cop:.2f}, {coco2:.2f}, {vresidual:.2f}, "
                        u"{copv[GASNATURAL]:.2f}, {copv[ELECTRICIDAD]:.2f}, {copv[ELECTRICIDADBALEARES]:.2f}, {copv[ELECTRICIDADCANARIAS]:.2f}, "
                        u"{copv[ELECTRICIDADCEUTAMELILLA]:.2f}, {copv[BIOCARBURANTE]:.2f}, {copv[BIOMASA]:.2f}, "
                        u"{copv[BIOMASADENSIFICADA]:.2f}, {copv[CARBON]:.2f}, {copv[FUELOIL]:.2f}, {copv[GASOLEO]:.2f}, {copv[GLP]:.2f}, "
                        u"{copv[RED1]:.2f}, {copv[RED2]:.2f}"
                        u"\n"
                        #TODO: demandas
            ).format (variante=variante, escenario=escenario, ctotal=ctotal, civ=civ, cmv=cmv, crv=crv, cop=cop, coco2=coco2, vresidual=vresidual, copv=copv)
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
        print(u'Generando archivo de costes para todos los proyectos', ', '.join(proyectos))
        print()
    else:
        proyectos = [args.proyectoactivo]
        print(u'Generando archivo de costes para el proyecto', args.proyectoactivo)
        print()

    for proyectoactivo in proyectos:
        config = costes.Config(args.configfile, proyectoactivo)

        print(u"* Cálculo de costes del proyecto %s *" % config.proyectoactivo)
        print(u"\tCargando costes: ", config.costespath)
        costesdata = costes.cargacostes(config.costespath)
        print(u"\tCargando mediciones: ", config.medicionespath)
        mediciones = costes.cargamediciones(config.medicionespath, costesdata)
        escenarios = [costes.Escenario(tipo, tasa, config.costesconfigpath)
                      for tipo in config.escenarios
                      for tasa in config.escenarios[tipo]]
        print(u"\tDefinidos %i escenarios" % len(escenarios))
        print(u"\tCalculando costes...")
        numcasos = calculacostes(config, costesdata, mediciones, escenarios)
        print(u"Calculados %i casos del proyecto activo: %s" % (numcasos,
                                                                config.proyectoactivo))

