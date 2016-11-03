#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Test del Cálculo de costes
#
# DB-HE 2013
#

import textwrap


def tablacostes(solucion, escenario):
    """Imprime tabla de costes de la solución para el escenario dado"""

    annobase = escenario.base
    periodo = escenario.periodo
    tasa = escenario.tasa
    costessolucion = solucion.costes(escenario)
    costesdescontados = descuenta(solucion.costes(escenario), tasa)
    costesmantenimiento = [solucion.costemantenimiento(i, escenario) for i in range(periodo)]
    costesreposicion = [solucion.costereposicion(i, escenario) for i in range(periodo)]

    txt = []
    txt.append("\n==================================================")
    txt.append("COSTES SOLUCIÓN: %s " % solucion.nombre)
    txt.append("Descripción:")
    descrtxt = ["    %s" % s for s in textwrap.wrap(unicode(solucion.desc).encode('utf8'),45)]
    txt.extend(descrtxt)
    txt.append("Análisis: %s" % escenario.tipo)
    txt.append("Tasa de descuento: %i" % tasa)
    txt.append("Coste inicial: %8.2f" % solucion.cinicial[escenario.tipo])
    txt.append("Coste de mantenimiento: %8.2f" % solucion.cmant[escenario.tipo])
    txt.append("Valor residual: %8.2f" % solucion.valorresidual(escenario))
    txt.append("==================================================")
    txt.append("Coste global (descontado): %8.2f" % solucion.costeglobal(escenario))
    txt.append("================== COSTES ========================")
    txt.append(" i  año      cmant    crepo     ctot         cdesc")
    txt.append("== ====   ======== ======== ========      ========")
    for i in range(periodo):
        txt.append("%2i %4i - %8.2f %8.2f %8.2f  --- %8.2f" % (i, i+annobase,
                                                               costesmantenimiento[i],
                                                               costesreposicion[i],
                                                               costessolucion[i],
                                                               costesdescontados[i]))
    txt.append("==================================================")
    return "\n".join(txt)

def tablapreciosco2(escenario):
    preciosco2 = escenario.preciosco2
    sep = "="*20
    txt = []
    txt.append("\n" + sep)
    txt.append("COSTES DEL CO2")
    txt.append(sep)
    txt.append(" i  año   cCO2(%4i)" % escenario.base)
    txt.append("== ====   ==========")
    for i in range(escenario.periodo):
        txt.append("%2i %4i - %10.2f" % (i,
                                        i+escenario.base,
                                        preciosco2[i]))
    txt.append(sep)
    return "\n".join(txt)

def tablapreciosenergia(escenario):
    costes = escenario.preciosenergia
    combustibles = costes.keys()
    enc = ''.join(["%14s" % ("%s" % combustible) for combustible in combustibles])
    sep = "=" * (len(enc) + 10)
    valores = [[val for val in costes[combustible]] for combustible in combustibles]

    txt = []
    txt.append("\n" + sep)
    txt.append("COSTES DE LA ENERGÍA PARA EL PERIODO (len=%i, base=%4i, analisis=%s)" % (escenario.periodo, escenario.base, escenario.tipo))
    txt.append(sep)
    txt.append(" i  año - %s" % enc)
    txt.append(sep)
    for i in range(escenario.periodo):
        txt.append("%2i %4i - %s" % (i, i + escenario.base,
                                     ''.join("%14.3f" % costes[combustible][i] for combustible in combustibles)))
    txt.append(sep)
    return "\n".join(txt)

if __name__ == "__main__":
    from costes import *
    from pprint import pprint

    config = Config('./config.yaml')

    costes = cargasoluciones(config.costespath)
    mediciones = cargamediciones(config.medicionespath, costes)
    variante = mediciones[0]

    escenario1 = Escenario('macro', 3, config.parametrospath)
    escenario2 = Escenario('micro', 3, config.parametrospath)

    solucion1 = costes['HUm2a']
    solucion2 = costes['HUv1']

    print tablacostes(solucion1, escenario1)
    print tablacostes(solucion1, escenario2)
    print tablacostes(solucion2, escenario1)
    print tablacostes(solucion2, escenario2)
    print tablapreciosco2(escenario1)
    print tablapreciosenergia(escenario1)
    print tablapreciosenergia(escenario2)

    # Valor residual descontado al principio del periodo
    print solucion1.costes(escenario1)
    print descuenta(solucion1.costes(escenario1), escenario1.tasa)
    print solucion1.costeglobal(escenario1)
    print solucion2.costes(escenario1)
    print descuenta(solucion2.costes(escenario1), escenario1.tasa)
    print solucion2.costeglobal(escenario1)

    pprint(variante)
    print "Coste (%s, %i%%): %8.3f" % (escenario1.tipo, escenario1.tasa, coste(variante, escenario1, costes))
    print "Coste (%s, %i%%): %8.3f" % (escenario2.tipo, escenario2.tasa, coste(variante, escenario2, costes))
