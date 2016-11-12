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
    tipo = escenario.tipo
    costessolucion = solucion.costes(tipo, periodo)
    costesdescontados = descuenta(costessolucion, tasa)
    costeglobal = sum(costesdescontados)
    costesmantenimiento = solucion.costesmantenimiento(tipo, periodo)
    costesreposicion = solucion.costesreposicion(tipo, periodo)

    txt = []
    txt.append(u"\n==================================================")
    txt.append(u"COSTES SOLUCIÓN: %s " % solucion.nombre)
    txt.append(u"Descripción:")
    descrtxt = [u"    %s" % s for s in textwrap.wrap(solucion.desc, 45)]
    txt.extend(descrtxt)
    txt.append(u"Análisis: %s" % escenario.tipo)
    txt.append(u"Tasa de descuento: %i" % tasa)
    txt.append(u"Coste inicial: %8.2f" % solucion.cinicial[escenario.tipo])
    txt.append(u"Coste de mantenimiento: %8.2f" % solucion.cmant[escenario.tipo])
    txt.append(u"Valor residual: %8.2f" % solucion.valorresidual(escenario.tipo, escenario.periodo))
    txt.append(u"==================================================")
    txt.append(u"Coste global (descontado): %8.2f" % costeglobal)
    txt.append(u"================== COSTES ========================")
    txt.append(u" i  año      cmant    crepo     ctot         cdesc")
    txt.append(u"== ====   ======== ======== ========      ========")
    for i in range(periodo):
        txt.append(u"%2i %4i - %8.2f %8.2f %8.2f  --- %8.2f" % (i, i+annobase,
                                                               costesmantenimiento[i],
                                                               costesreposicion[i],
                                                               costessolucion[i],
                                                               costesdescontados[i]))
    txt.append(u"==================================================")
    return u"\n".join(txt)

def tablapreciosco2(escenario):
    preciosco2 = escenario.preciosco2
    sep = "="*20
    txt = []
    txt.append(u"\n" + sep)
    txt.append(u"COSTES DEL CO2")
    txt.append(sep)
    txt.append(u" i  año   cCO2(%4i)" % escenario.base)
    txt.append(u"== ====   ==========")
    for i in range(escenario.periodo):
        txt.append(u"%2i %4i - %10.2f" % (i,
                                          i+escenario.base,
                                          preciosco2[i]))
    txt.append(sep)
    return u"\n".join(txt)

def tablapreciosenergia(escenario):
    costes = escenario.preciosenergia
    combustibles = costes.keys()
    enc = u''.join([u"%14s" % ("%s" % combustible) for combustible in combustibles])
    sep = u"=" * (len(enc) + 10)
    valores = [[val for val in costes[combustible]] for combustible in combustibles]

    txt = []
    txt.append(u"\n" + sep)
    txt.append(u"COSTES DE LA ENERGÍA PARA EL PERIODO (len=%i, base=%4i, analisis=%s)" % (escenario.periodo, escenario.base, escenario.tipo))
    txt.append(sep)
    txt.append(u" i  año - %s" % enc)
    txt.append(sep)
    for i in range(escenario.periodo):
        txt.append(u"%2i %4i - %s" % (i, i + escenario.base,
                                      u''.join(u"%14.3f" % costes[combustible][i] for combustible in combustibles)))
    txt.append(sep)
    return u"\n".join(txt)

if __name__ == "__main__":
    from costes import *
    from pprint import pprint

    config = Config('./config.yaml')

    costes = cargacostes(config.costespath)
    mediciones = cargamediciones(config.medicionespath, costes)
    variante = mediciones[0]

    escenario1 = Escenario('macro', 3, config.parametrospath)
    escenario2 = Escenario('micro', 3, config.parametrospath)

    solucion1 = costes['CUB1_ER_0.05']
    solucion2 = costes['F1_ER_0.15']

    print tablacostes(solucion1, escenario1)
    print tablacostes(solucion1, escenario2)
    print tablacostes(solucion2, escenario1)
    print tablacostes(solucion2, escenario2)
    print tablapreciosco2(escenario1)
    print tablapreciosenergia(escenario1)
    print tablapreciosenergia(escenario2)

    # Valor residual descontado al principio del periodo
    print solucion1.costes(escenario1.tipo, escenario1.periodo)
    print descuenta(solucion1.costes(escenario1.tipo, escenario1.periodo), escenario1.tasa)
    print sum(descuenta(solucion1.costes(escenario1.tipo, escenario1.periodo), escenario1.tasa))
    print solucion2.costes(escenario1.tipo, escenario1.periodo)
    print descuenta(solucion2.costes(escenario1.tipo, escenario1.periodo), escenario1.tasa)
    print sum(descuenta(solucion2.costes(escenario1.tipo, escenario1.periodo), escenario1.tasa))

    pprint(variante)
    print u"Coste (%s, %i%%): %8.3f" % (escenario1.tipo, escenario1.tasa, coste(variante, escenario1, costes))
    print u"Coste (%s, %i%%): %8.3f" % (escenario2.tipo, escenario2.tasa, coste(variante, escenario2, costes))
