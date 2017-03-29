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
    reslines.append(u"nombre_edificio, fechacalculo, tipoedificio, usoedificio, "
                    u"envolvente, phuecos, sistemas, ventdiseno, efrecup, "
                    u"sup_util, volumen, compacidad, K, qsj, "
                    u"zc, peninsular, zci, zcv, HDD_15, CDD_25, "
                    u"eptot_m2, epnren_m2, epren_m2, "
                    u"eptot, epnren, epren, "
                    u"escenario, tasa, periodo, "
                    u"costetotal_m2, costeinicial_m2, costeoperacion_m2, "
                    u"costetotal, costeinicial, costemantenimiento, costereposicion, costeoperacion, costeco2, vresidual, "
                    u"cGASNATURAL, cELECTRICIDAD, cELECTRICIDADBALEARES, cELECTRICIDADCANARIAS, "
                    u"cELECTRICIDADCEUTAMELILLA, cBIOCARBURANTE, cBIOMASA, "
                    u"cBIOMASADENSIFICADA, cCARBON, cFUELOIL, cGASOLEO, cGLP, "
                    u"cRED1, cRED2, "
                    u"termica_prod_kWh_an, termica_exp_kWh_an, termica_nepb_kWh_an, "
                    u"electr_prod_kWh_an, electr_exp_kWh_an, electr_nepb_kWh_an, "
                    u"Demanda_calefaccion, Demanda_refrigeracion, Demanda_iluminacion_interior, "
                    u"Demanda_iluminacion_exterior, Demanda_equipos_interiores, Demanda_equipos_exteriores, "
                    u"Demanda_ventiladores, Demanda_bombas, Demanda_disipacion_calor, "
                    u"Demanda_humidificacion, Demanda_recuperacion_calor, Demanda_sistemas_agua, Cobertura_ACS_pct, "
                    u"Demanda_equipos_frigorificos, Demanda_equipos_generacion, archivo"
                    u"\n")
    for variante in sorted(mediciones):
        supvariante = variante.metadatos['superficie']
        for escenario in escenarios:
            ctotal = costes.coste(variante, escenario, costesdata)
            civ = costes.costeinicial(variante, escenario, costesdata)
            cmv = costes.costemantenimiento(variante, escenario, costesdata)
            crv = costes.costereposicion(variante, escenario, costesdata)
            copv = costes.costesoperacion(variante, escenario)
            cop = sum(copv[combustible] for combustible in copv)
            coco2 = costes.costeco2(variante, escenario)
            vresidual = costes.valorresidual(variante, escenario, costesdata)
            dem_acs = variante.demanda['Demanda_sistemas_agua']
            cobsolar_pct = (100.0 * variante.eprimaria['produccion']['termica_prod_kWh_an'] / supvariante / dem_acs) if dem_acs > 0.0 else 0.0

            if not checksum(ctotal, civ, cmv, crv, cop, coco2, vresidual):
                print(variante)
                print(escenario)
                raise Exception("La suma de costes no coincide con el total ctotal != civ + cmv + crv + cop + coco2 - vresidual !!")
            dataline = (u"{meta[name]}, {meta[fechacalculo]}, {meta[tipoedificio]}, {meta[usoedificio]}, "
                        u"{meta[envolvente]}, {meta[phuecos]}, {meta[sistemas]}, {meta[ventdiseno]}, {meta[efrecup]}, "
                        u"{meta[superficie]:.2f}, {meta[volumen]:.2f}, {meta[compacidad]:.2f}, {meta[K]:.2f}, {meta[qsj]:.2f}, "
                        u"{meta[zc]}, {meta[peninsular]}, {meta[zci]}, {meta[zcv]}, {meta[HDD_15]}, {meta[CDD_25]}, "
                        u"{ep[EP_tot_m2]:.2f}, {ep[EP_nren_m2]:.2f}, {ep[EP_ren_m2]:.2f}, "
                        u"{ep[EP_tot]:.2f}, {ep[EP_nren]:.2f}, {ep[EP_ren]:.2f}, "
                        u"{escenario.tipo}, {escenario.tasa:.2f}, {escenario.periodo:d}, "
                        u"{ctotalm2:.2f}, {civ_m2:.2f}, {cop_m2:.2f}, "
                        u"{ctotal:.2f}, {civ:.2f}, {cmv:.2f}, {crv:.2f}, {cop:.2f}, {coco2:.2f}, {vresidual:.2f}, "
                        u"{copv[GASNATURAL]:.2f}, {copv[ELECTRICIDAD]:.2f}, {copv[ELECTRICIDADBALEARES]:.2f}, {copv[ELECTRICIDADCANARIAS]:.2f}, "
                        u"{copv[ELECTRICIDADCEUTAMELILLA]:.2f}, {copv[BIOCARBURANTE]:.2f}, {copv[BIOMASA]:.2f}, "
                        u"{copv[BIOMASADENSIFICADA]:.2f}, {copv[CARBON]:.2f}, {copv[FUELOIL]:.2f}, {copv[GASOLEO]:.2f}, {copv[GLP]:.2f}, "
                        u"{copv[RED1]:.2f}, {copv[RED2]:.2f}, "
                        u"{prod[termica_prod_kWh_an]:.2f}, {prod[termica_exp_kWh_an]:.2f}, {prod[termica_nepb_kWh_an]:.2f}, "
                        u"{prod[electr_prod_kWh_an]:.2f}, {prod[electr_exp_kWh_an]:.2f}, {prod[electr_nepb_kWh_an]:.2f}, "
                        u"{dem[Demanda_calefaccion]:.2f}, {dem[Demanda_refrigeracion]:.2f}, {dem[Demanda_iluminacion_interior]:.2f}, "
                        u"{dem[Demanda_iluminacion_exterior]:.2f}, {dem[Demanda_equipos_interiores]:.2f}, {dem[Demanda_equipos_exteriores]:.2f}, "
                        u"{dem[Demanda_ventiladores]:.2f}, {dem[Demanda_bombas]:.2f}, {dem[Demanda_disipacion_calor]:.2f}, "
                        u"{dem[Demanda_humidificacion]:.2f}, {dem[Demanda_recuperacion_calor]:.2f}, {dem[Demanda_sistemas_agua]:.2f}, {cobsolar_pct:.2f}, "
                        u"{dem[Demanda_equipos_frigorificos]:.2f}, {dem[Demanda_equipos_generacion]:.2f}, {id}"
                        u"\n"
            ).format(id=variante.id, meta=variante.metadatos, ep=variante.eprimaria, escenario=escenario,
                     ctotalm2=float(ctotal / supvariante), civ_m2=float(civ / supvariante), cop_m2=float(cop / supvariante),
                     ctotal=ctotal, civ=civ, cmv=cmv, crv=crv, cop=cop, coco2=coco2, vresidual=vresidual, copv=copv,
                     prod=variante.eprimaria['produccion'], dem=variante.demanda, cobsolar_pct=cobsolar_pct)
            reslines.append(dataline)

    with io.open(os.path.join(config.basedir, 'resultados-costes.csv'), 'w', encoding='utf-8') as resfile:
        resfile.writelines(reslines)
    # Devuelve número de casos calculados
    return len(reslines)-2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=u'Calcula costes del proyecto activo para los escenarios configurados')
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help=u'usa el archivo de configuración CONFIGFILE')
    parser.add_argument('--todas', action='store_true', dest='generarlas_todas', default=False)
    args = parser.parse_args()

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
        if not os.path.exists(config.costespath):
            print(u"AVISO: No se han definido los costes del proyecto")
            continue
        print(u"- Cargando costes")
        costesdata = costes.cargacostes(config.costespath)
        print(u"- Cargando mediciones")
        mediciones = costes.cargamediciones(config.medicionespath, costesdata)
        escenarios = [costes.Escenario(tipo, tasa, config.costesconfigpath)
                      for tipo in config.escenarios
                      for tasa in config.escenarios[tipo]]
        print(u"- Calculando costes para %i escenarios" % len(escenarios))
        numcasos = calculacostes(config, costesdata, mediciones, escenarios)
        print(u"- Calculados %i casos" % numcasos)
