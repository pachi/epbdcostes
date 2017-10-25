#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Ministerio de Fomento
#                    Instituto de Ciencias de la Construcción Eduardo Torroja (IETcc-CSIC)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function
import argparse
import codecs
import copy
import glob
import multiprocessing
import os
import re
import shutil
import yaml
import costes

###############################################################

DICT_ESEN = {
    u'CALEFACCIÓN': u'HEATING',
    u'REFRIGERACIÓN': u'COOLING',
    u'ACS': u'WATERSYSTEMS',
    u'VENTILACIÓN': u'FANS'
}

DICT_ENES = {
    u'HEATING': u'CALEFACCIÓN',
    u'COOLING': u'REFRIGERACIÓN',
    u'WATERSYSTEMS': u'ACS',
    u'FANS': u'VENTILACIÓN'
}

########### Radiación en un plano horizontal, por climas [kwh/m2/mes] ###################

RADHOR = {
    'A1c': [93.12, 107.00, 150.29, 171.43, 174.23, 178.06, 188.07, 160.12, 112.12, 105.00, 78.75, 77.98],
    'A2c':[93.12, 107.00, 150.29, 171.43, 206.23, 192.78, 207.59, 177.30, 123.74, 104.78, 78.67, 77.18],
    'A3c': [93.12, 107.00, 150.29, 171.43, 206.23, 202.78, 210.94, 181.39, 132.26, 104.75, 79.73, 76.17],
    'A4c': [93.12, 107.00, 150.29, 171.43, 206.23, 213.00, 224.38, 193.63, 137.79, 104.88, 78.77, 76.19],
    'alpha1c': [132.52, 144.91, 184.37, 196.69, 212.54, 178.25, 187.88, 159.95, 111.88, 128.62, 108.81, 111.73],
    'alpha2c': [132.52, 144.91, 184.37, 196.69, 212.54, 211.05, 207.54, 178.02, 137.97, 128.98, 108.15, 112.78],
    'alpha3c': [132.52, 144.91, 184.37, 196.69, 212.54, 212.52, 210.51, 180.88, 138.33, 128.92, 108.08, 112.53],
    'alpha4c': [132.52, 144.91, 184.37, 196.69, 212.54, 213.16, 224.70, 192.79, 137.67, 128.66, 107.70, 112.55],
    'B1c': [83.91, 100.40, 143.62, 165.26, 198.06, 204.70, 187.63, 160.43, 112.27, 98.79, 72.75, 69.80],
    'B2c': [83.91, 100.40, 143.62, 165.26, 198.06, 192.78, 208.07, 178.07, 122.80, 98.66, 72.98, 69.36],
    'B3c': [83.91, 100.40, 143.62, 165.26, 198.06, 203.03, 210.62, 181.26, 132.24, 98.72, 72.87, 69.14],
    'B4c': [83.91, 100.40, 143.62, 165.26, 198.06, 213.26, 224.94, 193.63, 137.18, 98.48, 73.21, 69.19],
    'C1c': [63.52, 78.93, 123.77, 142.45, 174.28, 178.50, 187.78, 160.64, 112.11, 84.31, 58.02, 51.34],
    'C2c': [63.52, 78.93, 123.77, 142.45, 174.28, 192.44, 207.99, 178.49, 122.97, 84.52, 58.48, 50.47],
    'C3c': [63.52, 78.93, 123.77, 142.45, 174.28, 203.06, 210.59, 181.93, 132.27, 84.14, 57.81, 51.06],
    'C4c': [63.52, 78.93, 123.77, 142.45, 174.28, 213.03, 225.19, 193.01, 137.70, 84.39, 57.76, 50.52],
    'D1c': [60.19, 82.62, 127.04, 150.66, 183.68, 178.65, 187.56, 161.17, 112.60, 86.61, 57.71, 48.42],
    'D2c': [60.19, 82.62, 127.04, 150.66, 183.68, 192.77, 208.06, 178.38, 123.55, 87.08, 57.29, 48.19],
    'D3c': [60.19, 82.62, 127.04, 150.66, 183.68, 203.02, 210.82, 181.33, 132.35, 87.31, 57.88, 48.58],
    'E1c': [59.29, 77.82, 122.48, 144.00, 180.71, 178.32, 188.34, 160.86, 112.26, 83.64, 54.85, 46.95],
    'A3': [99.77, 115.05, 159.58, 178.95, 210.77, 201.25, 203.27, 170.68, 123.20, 96.01, 75.09, 78.47],
    'A4': [99.77, 115.05, 159.58, 178.95, 210.77, 211.25, 216.89, 182.32, 128.36, 96.22, 74.81, 78.44],
    'B3': [90.64, 107.73, 152.05, 171.68, 202.47, 201.11, 204.07, 171.34, 123.77, 90.75, 69.51, 70.00],
    'B4': [90.64, 107.73, 152.05, 171.68, 202.47, 211.68, 217.01, 182.21, 127.93, 90.89, 68.86, 70.53],
    'C1': [68.42, 83.88, 129.87, 147.76, 176.89, 177.27, 182.08, 152.30, 105.67, 78.52, 54.86, 52.52],
    'C2': [68.42, 83.88, 129.87, 147.76, 176.89, 191.94, 200.74, 168.06, 114.87, 78.48, 55.28, 52.31],
    'C3': [68.42, 83.88, 129.87, 147.76, 176.89, 201.85, 203.09, 171.83, 123.50, 78.26, 55.15, 52.41],
    'C4': [68.42, 83.88, 129.87, 147.76, 176.89, 211.22, 216.78, 181.92, 128.46, 78.82, 56.10, 51.75],
    'D1': [64.83, 88.99, 134.59, 156.35, 187.26, 177.26, 181.87, 151.72, 105.68, 80.23, 54.19, 49.37],
    'D2': [64.83, 88.99, 134.59, 156.35, 187.26, 191.61, 200.55, 166.87, 115.34, 80.66, 54.33, 50.20],
    'D3': [64.83, 88.99, 134.59, 156.35, 187.26, 201.24, 203.69, 171.40, 123.07, 80.18, 54.57, 50.24],
    'E1': [63.57, 82.92, 128.52, 149.74, 184.59, 177.46, 181.89, 152.44, 105.87, 77.04, 52.63, 48.41]
}

########### parte que genera las variantes ####################

def generaMedidas(sistemasDefs):
    """Genera lista de definición de medidas por variante y paquete"""
    paquetes = sistemasDefs['paquetes']
    tecnologias = sistemasDefs['tecnologias']
    # Genera definición de medidas por paquete de las variantes
    medidas = []
    for paquete in sorted(paquetes.keys()):
        for sistemadef in paquetes[paquete]:
            sistema, tipo = sistemadef[:2]
            params = sistemadef[2:] # Los parámetros van en una lista de longitud variable
            for datos in tecnologias[sistema]:
                medidas.append([paquete, tipo, params] + datos)
    return medidas

def readenergystring(datastring):
    """Genera lista de componentes a partir de cadena csv con componentes EPBD"""
    components, meta = [], []
    for line in datastring.splitlines():
        line = line.strip()
        if (line == '') or line.startswith('vector'):
            continue
        elif line.startswith('#'):
            meta.append(line)
        else:
            fields = line.split('#', 1)
            data = [x.strip() for x in fields[0].split(',')]
            comment = fields[1] if len(fields) > 1 else ''
            carrier, ctype, originoruse = data[0:3]
            values = [float(v.strip()) for v in data[3:]]
            components.append({ 'carrier': carrier, 'ctype': ctype,
                                'originoruse': originoruse,
                                'values': values, 'comment': comment })
    return {'componentes': components, 'meta': meta}

def aplicaMedidas(meta, componentes, medidas):
    """Transforma componentes de una variante aplicándole un conjunto de medidas"""
    zonaclimatica = next(m for m in meta if m.startswith(u'#CTE_Weather_file')).split(':')[1].strip().replace('_peninsula', '').replace('_canarias', 'c')
    oldcomponentes = componentes[:]
    newvectors = []

    # 1 - Medidas independientes de los componentes de entrada (p.e. generación fotovoltaica)
    #     Las medidas VALUES simplemente incluyen líneas con valores predefinidos
    #     Las medidas PV generan producción fotovoltaica según zona climática, superficie de paneles
    #     y rendimiento de los paneles (rendimiento = kWp / superficie).
    medidas1 = [medida for medida in medidas if medida[1] in ['VALUES', 'PV']]
    for medida in medidas1:
        paquete, tipo, params = medida[:3]
        if tipo == 'VALUES':
            ctipo, src_dst, vectorDestino = medida[3:6]
            valores = [u"%s" % v for v in medida[6:-1]]
            comentario = medida[-1]
            cadena = u"%s, %s, %s, %s # %s" % (vectorDestino, ctipo, src_dst, ', '.join(valores), comentario)
            newvectors.append(cadena)
        if tipo == 'PV':
            ctipo, src_dst, vectorDestino, superficie, rendimiento, comentario = medida[3:]
            valoresproduccion = [(val * rendimiento * superficie) for val in RADHOR[zonaclimatica]]
            cadena = u"%s, %s, %s, %s # %s" % (vectorDestino, ctipo, src_dst,
                                               ', '.join('%.2f' % val for val in valoresproduccion),
                                               comentario)
            newvectors.append(cadena)

    # 2 - Medidas que modifican los componentes de entrada (p.e. PST, que reduce componente de ACS)
    #     Las medidas PST calculan la aportación solar mes a mes a un servicio según la zona climática,
    #     un rendimiento y una superficie de paneles.
    #     Las medidas PSTFRACTION calculan la aportación solar como fracción de un servicio
    #     Ambas descuentan de la demanda del servicio la parte solar aportada, y dejan la demanda
    #     remanente para que pueda ser procesada posteriormente
    medidas2 = [medida for medida in medidas if medida[1] in ['PST', 'PSTFRACTION']]
    for medida in medidas2:
        paquete, tipo, params = medida[:3]
        if tipo == 'PST':
            # a) Genera producción
            ctipo, src_dst, vectorDestino, superficie, rendimiento, comentario = medida[3:]
            valoresproduccion = [(val * rendimiento * superficie) for val in RADHOR[zonaclimatica]]
            cadena = u"%s, %s, %s, %s # %s" % (vectorDestino, ctipo, src_dst,
                                               ', '.join('%.2f' % val for val in valoresproduccion),
                                               comentario)
            newvectors.append(cadena)
            # b) Genera consumo ('CONSUMO', 'EPB', 'MEDIOAMBIENTE')
            servicio = params[0]
            idemanda, vectordemanda = next((ii, vector) for (ii, vector) in enumerate(oldcomponentes)
                                           if vector['comment'].split(',')[0].strip() == servicio)
            valoresdemanda = vectordemanda['values']
            valoresconsumo = [min(produccion, demanda) for (produccion, demanda)
                              in zip(valoresproduccion, valoresdemanda)]
            cadena = u"MEDIOAMBIENTE, CONSUMO, EPB, %s # %s, %s" % (', '.join('%.2f' % val for val in valoresconsumo),
                                                                    DICT_ENES.get(servicio, servicio),
                                                                    comentario)
            newvectors.append(cadena)
            # c) Modifica consumo existente del servicio
            newvalues = [(demanda - consumo) for (demanda, consumo) in zip(valoresdemanda, valoresconsumo)]
            # eliminamos el vector si no queda demanda sin cubrir
            if any(float(val) != 0.0 for val in newvalues):
                oldcomponentes[idemanda]['values'] = newvalues
            else:
                del oldcomponentes[idemanda]

        elif tipo == 'PSTFRACTION':
            # a) Demanda original
            servicio, cobertura = params
            idemanda, vectordemanda = next((ii, vector) for (ii, vector) in enumerate(oldcomponentes)
                                           if vector['comment'].split(',')[0].strip() == servicio)
            valoresdemanda = vectordemanda['values']
            # b) Consumo / producción fraccional
            ctipo, src_dst, vectordestino, rend1, rend2, comentario = medida[3:]
            rend1 = eval(rend1) if not isinstance(rend1, (int, float)) else rend1
            rend2 = eval(rend2) if not isinstance(rend2, (int, float)) else rend2
            valoresTransformados = [1.0 * cobertura * val / rend1 / rend2 for val in valoresdemanda]
            cadena = u"%s, %s, %s, %s # %s, %s" % (vectordestino, ctipo, src_dst,
                                                   u", ".join('%.2f' % v for v in valoresTransformados),
                                                   DICT_ENES.get(servicio, servicio),
                                                   comentario)
            newvectors.append(cadena)
            # c) Demanda modificada
            newvalues = [(1.0 - cobertura) * val for val in valoresdemanda]
            # eliminamos el vector si no queda demanda sin cubrir
            if any(float(val) != 0.0 for val in newvalues):
                oldcomponentes[idemanda]['values'] = newvalues
            else:
                del oldcomponentes[idemanda]

    # 3 - Medidas que son transformaciones de los componentes de entrada (incluida la identidad)
    #     Las transformaciones cambian el vector y aplican rendimientos de generación y dist.+em.+control
    medidas3 = [medida for medida in medidas if medida[1] in ['HEATING', 'COOLING', 'WATERSYSTEMS']]
    for ii, vector in enumerate(oldcomponentes):
        servicioCubierto = vector['comment'].split(',')[0].strip()
        valores = vector['values']
        string_rows = []
        for medida in medidas3:
            # params = [], tipo = servicio suministrado
            paquete, tipo, params = medida[:3]
            if tipo == servicioCubierto:
                ctipo, src_dst, vectordestino, rend1, rend2, comentario = medida[3:]
                rend1 = eval(rend1) if not isinstance(rend1, (int, float)) else rend1
                rend2 = eval(rend2) if not isinstance(rend2, (int, float)) else rend2
                valoresTransformados = [1.0 * val / rend1 / rend2 for val in valores]
                cadena = u"%s, %s, %s, %s # %s, %s" % (vectordestino, ctipo, src_dst,
                                                      u", ".join('%.2f' % v for v in valoresTransformados),
                                                      DICT_ENES.get(servicioCubierto, servicioCubierto),
                                                      comentario)
                string_rows.append(cadena)
        # Si no hay medidas definidas para el servicio cubierto por el vector, este se guarda
        # dejando en el comentario únicamente el servicio atendido
        if string_rows == []:
            string_rows = [u"%s, %s, %s, %s # %s" % (vector['carrier'], vector['ctype'], vector['originoruse'],
                                                     u", ".join([str(v) for v in valores]),
                                                     DICT_ENES.get(servicioCubierto, servicioCubierto))]
        newvectors.extend(string_rows)

    return newvectors

def generavarianteforbasename(item):
    basename, paquetesids, varianteinfile, variantesoutdir, medidas, loc = item
    variantesforbasename = []
    datastring = codecs.open(varianteinfile, 'r', 'UTF8').read()
    data = readenergystring(datastring)
    for paqueteid in paquetesids:
        variantedata = copy.deepcopy(data) # deep copy needed here!
        medidaspaquete = [medida for medida in medidas if medida[0] == paqueteid.strip()]
        variantedata['meta'].append(u'#CTE_PaqueteSistemas: %s' % paqueteid)
        variante = { 'meta': variantedata['meta'],
                        'componentes': aplicaMedidas(variantedata['meta'],
                                                    variantedata['componentes'],
                                                    medidaspaquete) }
        # Cambia vector ELECTRICIDAD según criterio definido por loc
        if loc == 'PENINSULA':
            pass
        elif loc == 'CANARIAS':
            variante['componentes'] = [
                componente.replace(u'ELECTRICIDAD', u'ELECTRICIDADCANARIAS')
                for componente in variante['componentes']
            ]
        elif loc == 'CEUTAMELILLA':
            variante['componentes'] = [
                componente.replace(u'ELECTRICIDAD', u'ELECTRICIDADCEUTAMELILLA')
                for componente in variante['componentes']
            ]
        elif loc == 'BALEARES':
            variante['componentes'] = [
                componente.replace(u'ELECTRICIDAD', u'ELECTRICIDADBALEARES')
                for componente in variante['componentes']
            ]
        else:
            # Cambia vector ELECTRICIDAD a ELECTRICIDADCANARIAS si es clima canario
            metaclima = next(meta for meta in variante['meta'] if meta.startswith(u'#CTE_Weather'))
            if not u"canarias" in metaclima:
                continue
            else:
                variante['componentes'] = [
                    componente.replace(u'ELECTRICIDAD', u'ELECTRICIDADCANARIAS')
                    for componente in variante['componentes']
                ]
        # Fin de cambio de vector ELECTRICIDAD
        variante['outfile'] = os.path.join(variantesoutdir, "%s_%s.csv" % (basename, paqueteid))
        variante['basename'] = basename
        variantesforbasename.append(variante)
    return variantesforbasename

def generaVariantes(config, loc=None):
    """Genera archivos con variantes a partir de definición de sistemas

    La definición de sistemas incluye la definición de las tecnologías,
    los paquetes, los casos base y los paquetes que se aplican a cada
    caso base.
    """
    # Genera sistemas y medidas
    try:
        path = config.sistemaspath
        if not os.path.exists(path):
            print('ERROR: no se encuentra el archivo de definición de sistemas %s' % path)
            exit()
        sistemas = yaml.load(open(path, 'r'))
    except (Exception) as e:
        print('ERROR: archivo de definición de sistemas mal formado %s' % path)
        raise e
    medidas = generaMedidas(sistemas)

    # Escribe registro de medidas por variante y paquete
    logsdir = config.logsdir
    if not os.path.exists(logsdir):
        os.makedirs(logsdir)
    medidaslogpath = os.path.join(logsdir, 'generamedidas.log')
    with codecs.open(medidaslogpath, 'w', 'UTF8') as ff:
        ff.writelines(", ".join(u"%s" % val for val in medida) + u"\n" for medida in medidas)

    # Genera lista de variantes y paquetes a partir de regex y lista de paquetes para cada regex
    #    variantes: [[regex1, [paquete1, ..., paqueten]]... ]
    allfiles = [os.path.splitext(os.path.basename(pathentry))[0]
                for pathentry in glob.glob(os.path.join(config.variantesbasedir, '*'))
                if os.path.isfile(pathentry)]
    basesypaquetes = []
    for (regexstring, paquetes) in sistemas['variantes']:
        basenames = [name for name in allfiles if re.search(regexstring, name) is not None]
        basesypaquetes.extend([
            [basename,
             paquetes,
             os.path.join(config.variantesbasedir, basename + '.csv'), # varianteinfile
             config.variantesdir,
             medidas,
             loc] for basename in basenames
        ])

    # Aplica lista de paquetes a cada variante base
    # basesypaquetes: [(basename, paquetesids, varianteinfile, variantesoutdir, medidas, loc), ... ]
    pool = multiprocessing.Pool()
    result = pool.map(generavarianteforbasename, basesypaquetes)
    variantes = [vv for res in result for vv in res]
    # variantes = [vv for item in basesypaquetes for vv in generavarianteforbasename(item)]

    # Guarda archivos de variantes
    if not os.path.exists(config.variantesdir):
        os.makedirs(config.variantesdir)

    for variante in variantes:
        with codecs.open(variante['outfile'], 'w', 'UTF8') as ff:
            ff.writelines(u'\n'.join(variante['meta'] + ["vector,tipo,src_dst"] + variante['componentes']))
    return variantes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Genera variantes aplicando medidas de sistema al caso base')
    parser.add_argument('-v', action='store_true', dest='is_verbose', help='salida detallada')
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('--cleardir', action='store_true', dest='cleardir', help='elimina variantes preexistentes')
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help='usa el archivo de configuración CONFIGFILE')
    parser.add_argument('--loc', action='store', dest='loc', default='CLIMA', metavar='LOCALIZACION',
                        choices=['CLIMA', 'PENINSULA', 'CANARIAS', 'BALEARES', 'CEUTAMELILLA'],
                        help='localización para vector ELECTRICIDAD')
    args = parser.parse_args()
    VERBOSE = args.is_verbose

    config = costes.Config(args.configfile, args.proyectoactivo)
    print(u"* Generando variantes con sistemas de %s" % config.proyectoactivo)
    if args.cleardir:
        existingfiles = [gg for gg in glob.glob(os.path.join(config.variantesdir, '*')) if os.path.isfile(gg)]
        print(u"- Eliminando %i variantes existentes" % len(existingfiles))
        shutil.rmtree(config.variantesdir)
    if not os.path.exists(config.variantesdir):
        os.makedirs(config.variantesdir)
    variantes = generaVariantes(config, args.loc)
    print(u"- Guardadas %i variantes" % len(variantes))
