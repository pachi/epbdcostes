#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Cálculo de costes para estudio de coste óptimo
#
# DB-HE 2018
#

from __future__ import print_function
from collections import OrderedDict
import xlrd

"""Generador de archivo inicial de costes de soluciones

Toma un archivo de mediciones del proyecto activo y genera un archivo
plantilla de costes de soluciones.
"""

C_GG = 13.0
C_BI = 6.0
C_IVA = 21.0
C_IVA_RV = 10.0
C_HON = 10.0
C_PER = 7.0

PARAMS = {
    'C_GG': C_GG,
    'C_BI': C_BI,
    'C_IVA': C_IVA,
    'C_IVA_RV': C_IVA_RV,
    'C_HON': C_HON,
    'C_PER': C_PER,

    'FCOSTE_GENERAL': (C_GG + C_BI + C_IVA + C_HON + C_PER) / 100.0,
    'FCOSTE_REHAVIV': (C_GG + C_BI + C_IVA_RV + C_HON + C_PER) / 100.0,

    'VUTIL': {'opaco': 50, 'hueco': 30, 'sistema': 20}, # años
    'PMANT': {'opaco': 10, 'hueco': 10, 'sistema': 1}, # años/periodo
    'CMANT': {'opaco': 5.0/100, 'hueco': 10.0/100, 'sistema': 7.0/100}, # % s/cinicial/periodo
}

SOLSTRHDR = u"""# Costes de las MAE
# =================
# directorio de proyecto: "{proyecto:s}"
#
# desc: descripción de la MAE
# vutil: vida útil de la MAE (años)
#   - elementos opacos: {params[VUTIL][opaco]:d} años
#   - huecos: {params[VUTIL][hueco]:d} años
#   - instalaciones: {params[VUTIL][sistema]:d} años
# pmant: periodicidad del mantenimiento (años)
#   - elementos opacos: {params[PMANT][opaco]:d} años
#   - elementos huecos: {params[PMANT][hueco]:d} años
#   - instalaciones: {params[PMANT][sistema]:d} años
#
# COSTES:
# ======
# Para cada coste se deben aportar los costes:
#
#  - para el cálculo macroeconómico (sin impuestos ni tasas) se considera
#   - PEM
#  - para el cálculo financiero/microeconómico (con impuestos y tasas) se considera
#   - PEM +
#       - Gastos generales {params[C_GG]:.1f}%
#       - Beneficio industrial {params[C_BI]:.1f}%
#       - IVA:
#           - residencial nuevo y terciario: {params[C_IVA]:.1f}%
#           - residencial rehabilitación: {params[C_IVA_RV]:.1f}%
#       - Honorarios: {params[C_HON]:.1f}%
#       - Permisos: {params[C_PER]:.1f}%
#
# cinicial: coste inicial (€/ud)
# cmant: costes de mantenimiento (€/ud·periodo)
#   - elementos opacos: {params[CMANT][opaco]:.1f}% coste inicial c/{params[PMANT][opaco]:.1f} años
#   - huecos: {params[CMANT][hueco]:.1f}% coste inicial c/{params[PMANT][hueco]:.1f} años
#   - instalaciones: {params[CMANT][sistema]:.1f}% coste inicial c{params[PMANT][sistema]:.1f}/año
#\n\n""" #.format(proyecto=config.proyectoactivo, params=PARAMS)

SOLSTR = u"""{nombre}:
  desc: {descr}
  vutil: {vutil:.1f} #años
  pmant: {pmant:.1f} #años
  cinicial:
    macro: {cinicialmacro:.1f} # €/ud
    micro: {cinicial:.1f} # €/ud
  cmant:
    macro: {cmantmacro:.1f} # €/ud/periodo
    micro: {cmant:.1f} # €/ud/periodo

"""

def row2yaml(row):
    rehaviv = row.get('rehaviv', False)
    fcostes = PARAMS['FCOSTE_REHAVIV'] if rehaviv else PARAMS['FCOSTE_GENERAL']
    tipo = row.get('tipo', None)
    pem = row.get('pem', 0.0) or 0.0
    pec = ((1.0 + fcostes) * pem)
    fcmant = PARAMS['CMANT'].get(tipo, 0)
    return SOLSTR.format(
        nombre=row['nombre'],
        descr=row.get('descr', u'Descripción') or u'Descripción',
        vutil=PARAMS['VUTIL'].get(tipo, 100),
        pmant=PARAMS['PMANT'].get(tipo, 100),
        cinicialmacro=pem,
        cinicial=pec,
        cmantmacro=(fcmant * pem),
        cmant=(fcmant * pec)
    )

def row2tuple(row):
    """Converte fila de datos a tupla para poder crear diccionario"""
    nombre, tipo, rehaviv, pem, descripcion = row
    pem = float(pem) if pem else None
    rehaviv = bool(rehaviv if rehaviv else None)
    tipo = tipo if tipo in [u'opaco', u'hueco', u'sistema'] else None
    rowtuple = (nombre,
                {'nombre': nombre,
                 'tipo': tipo or None,
                 'rehaviv': rehaviv,
                 'pem': pem,
                 'descr': descripcion or None})
    return rowtuple

def getvalues(workbook):
    """Diccionario ordenado con valores de la hoja de cálculo"""
    book = xlrd.open_workbook(workbook)

    if 'precios' in book.sheet_names():
        sheet = book.sheet_by_name('precios')
    else:
        sheet = book.sheet_by_index(0)

    print(u"Encontrados en %s: %i filas de precios con %i columnas"
          % (sheet.name, sheet.nrows, sheet.ncols))
    _rows = [sheet.row_values(ridx, 0, 5) for ridx in range(sheet.nrows)]
    return OrderedDict(
        row2tuple(row) for row in _rows
        if any(row) and not (row[0].startswith(u'nombre') or row[0].startswith(u'#'))
    )

if __name__ == "__main__":
    import argparse
    import io
    import os
    import costes

    parser = argparse.ArgumentParser(description='Genera archivo de costes a partir de hoja de cálculo')
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help='usa el archivo de configuración CONFIGFILE')
    args = parser.parse_args()
    
    config = costes.Config(args.configfile, args.proyectoactivo)
    projectpath = config.proyectoactivo
    costespath = config.costespath
    print(u"* cargando archivo de soluciones del proyecto %s *" % projectpath)

    mediciones = costes.cargamediciones(config.medicionespath)
    solucionesmedidas = set([solucion for medicion in mediciones for solucion in medicion.soluciones])


    xlscostespath = os.path.join(projectpath, 'precios.xls')
    rows = getvalues(xlscostespath)
    found = [solucion for solucion in sorted(solucionesmedidas)
              if solucion in rows and all(rows[solucion])]
    incomplete = [solucion for solucion in sorted(solucionesmedidas)
                   if solucion in rows and not all(rows[solucion])]
    missing = [solucion for solucion in sorted(solucionesmedidas)
               if solucion not in rows]

    print(u"*********** Soluciones bien definidas *******************")
    for solucion in found:
        print(solucion)
    print(u"*********** Soluciones incompletas **********************")
    for solucion in incomplete:
        print(solucion)
    print(u"*********** Soluciones sin precios definidos ************")
    for solucion in missing:
        print(solucion)
    print(u"*********************************************************")

    res = []
    with io.open(costespath, 'w', encoding='utf-8') as ofile:
        res.append(SOLSTRHDR.format(proyecto=config.proyectoactivo, params=PARAMS))
        for row in rows:
            res.append(row2yaml(rows[row]))
        for sol in missing:
            print(u"Incorporando solución no definida: %s" % sol)
            res.append(row2yaml({'nombre': sol}))
        ofile.writelines(res)

    print (u"Archivo de costes %s generado con %i soluciones distintas a partir "
           u"de %i variantes" % (costespath, len(solucionesmedidas), len(mediciones)))

