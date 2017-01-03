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
import codecs
import copy
import glob
import os
import re
import yaml
import argparse
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

########### parte que genera las variantes ####################

def generaMedidas(sistemasDefs):
    """Genera lista de definición de medidas por variante y paquete"""
    paquetes = sistemasDefs['paquetes']
    tecnologias = sistemasDefs['tecnologias']
    # Genera definición de medidas por paquete de las variantes
    medidas = []
    for paquete in sorted(paquetes.keys()):
        for sistema, tipo, param1, param2 in paquetes[paquete]:
            for datos in tecnologias[sistema]:
                if tipo == 'BYSERVICE':
                    # Evaluamos expresiones para definir los rendimientos
                    rend1, rend2 = datos[3:5]
                    datos[3] = eval(rend1) if not isinstance(rend1, (int, float)) else rend1
                    datos[4] = eval(rend2) if not isinstance(rend2, (int, float)) else rend2
                medidas.append([paquete, tipo, param1, param2] + datos)
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

def transformaVector(vector, medidas):
    """Transforma vector aplicando un conjunto de medidas

    Si la medida se aplica al servicio del vector, se aplica
    Si no se aplica ninguna medida, se devuelve el vector
    """
    servicioCubierto = vector['comment'].split(',')[0].strip()
    valores = vector['values']

    string_rows = []
    for medida in medidas:
        paquete, tipo, servicio, cobertura = medida[0:4]
        if servicio == servicioCubierto:
            ctipo, src_dst, vectordestino, rend1, rend2, comentario = medida[4:]
            valoresTransformados = [round(val * cobertura / rend1 / rend2, 2) for val in valores]
            cadena = u"%s, %s, %s, %s # %s, %s" % (vectordestino, ctipo, src_dst,
                                                  u", ".join([str(v) for v in valoresTransformados]),
                                                  DICT_ENES.get(servicioCubierto, servicioCubierto),
                                                  comentario)
            string_rows.append(cadena)
    # No hay medidas definidas para el servicio cubierto por el vector
    # XXX: no se preserva el comentario completo, solo el servicio
    if string_rows == []:
        string_rows = [u"%s, %s, %s, %s # %s" % (vector['carrier'], vector['ctype'], vector['originoruse'],
                                                 u", ".join([str(v) for v in valores]),
                                                 DICT_ENES.get(servicioCubierto, servicioCubierto))]
    return string_rows

def aplicaMedidas(componentes, medidas):
    """Transforma componentes aplicando un conjunto de medidas"""
    newvectors = []
    # Genera vectores de salida transformando vectores de entrada
    for vector in componentes:
        for newvec in transformaVector(vector, medidas):
            newvectors.append(newvec)
    # Genera vectores de salida sin relación con los de entrada (p.e. generación fotovoltaica)
    for medida in medidas:
        paquete, tipo = medida[:2]
        if tipo == 'BYVALUE':
            servicio, cobertura, ctipo, src_dst, vectorDestino = medida[2:7]
            valores = [u"%s" % v for v in medida[7:-1]]
            comentario = medida[-1]
            cadena = u"%s, %s, %s, %s # %s" % (vectorDestino, ctipo, src_dst, ', '.join(valores), comentario)
            newvectors.append(cadena)
    return newvectors

def generaVariantes(config):
    """Genera archivos con variantes a partir de definición de sistemas

    La definición de sistemas incluye la definición de las tecnologías,
    los paquetes, los casos base y los paquetes que se aplican a cada
    caso base.
    """
    # Genera sistemas y medidas
    try:
        path = config.sistemaspath
        sistemas = yaml.load(open(path, 'r'))
    except:
        print('ERROR: no se encuentra el archivo de definición de sistemas %s' % path)
        exit()
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
        basesypaquetes.extend([[basename, paquetes] for basename in basenames])

    # Aplica lista de paquetes a cada variante base
    variantes = []
    for (basename, paquetesids) in basesypaquetes:
        datastring = codecs.open(os.path.join(config.variantesbasedir, basename + '.csv'), 'r', 'UTF8').read()
        data = readenergystring(datastring)
        for paqueteid in paquetesids:
            vardata = copy.deepcopy(data) # deep copy needed here!
            medidaspaquete = [medida for medida in medidas if medida[0] == paqueteid.strip()]
            vardata['meta'].append(u'#CTE_PaqueteSistemas: %s' % paqueteid)
            variante = { 'meta': vardata['meta'],
                         'componentes': aplicaMedidas(vardata['componentes'], medidaspaquete) }
            variantes.append([basename, paqueteid, variante])

    # Archivos de variantes
    variantesdir = config.variantesdir
    if not os.path.exists(variantesdir):
        os.makedirs(variantesdir)
    for (basename, paqueteid, variante) in variantes:
        with codecs.open(os.path.join(variantesdir, "%s_%s.csv" % (basename, paqueteid)),
                         'w', 'UTF8') as ff:
            ff.writelines(u'\n'.join(variante['meta'] + ["vector,tipo,src_dst"] + variante['componentes']))
    return variantes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Genera variantes aplicando medidas de sistema al caso base')
    parser.add_argument('-v', action='store_true', dest='is_verbose', help='salida detallada')
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('--cleardir', action='store_true', dest='cleardir', help='elimina variantes preexistentes' )
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help='usa el archivo de configuración CONFIGFILE')
    args = parser.parse_args()
    VERBOSE = args.is_verbose

    config = costes.Config(args.configfile, args.proyectoactivo)
    if args.cleardir:
        existingfiles = [gg for gg in glob.glob(os.path.join(config.variantesdir, '*')) if os.path.isfile(gg)]
        print(u"* Eliminando %i variantes existentes" % len(existingfiles))
        for f in existingfiles:
            os.remove(f)
    print(u"* Generando variantes con sistemas de %s" % config.proyectoactivo)
    variantes = generaVariantes(config)
    print(u"* Guardadas %i variantes" % len(variantes))
