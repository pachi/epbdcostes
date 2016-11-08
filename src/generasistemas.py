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

import codecs
import os
import yaml
import argparse
import costes

################## parte que genera el archivo de las tecnologias #####
def getMedidasSistemas(proyectoPath):
    try:
        medidasSistemasFile = os.path.join(proyectoPath, 'medidasSistemas.yaml')
        medidasSistemas = yaml.load(open(medidasSistemasFile, 'r'))
    except:
        print('ERROR: este proyecto no tiene el archivo de definición de los sistemas')
        exit()
    return medidasSistemas

def generaFilasMedida(clave, medidasSistemas):
    paquete = medidasSistemas['paquetes'][clave]
    tecnologias = medidasSistemas['tecnologias']
    salida = []
    for sistema, cobertura in paquete:
        for filaSistema in tecnologias[sistema]:
            salida.append([clave] + [filaSistema[0]] + [cobertura] + filaSistema[1:])
    return salida

def generaArchivoMedidas(proyectoPath):
    medidasSistemas = getMedidasSistemas(proyectoPath)
    destinoPath = os.path.join(proyectoPath, 'resultados', 'medidasSistemas.csv')
    with codecs.open(destinoPath, 'w', 'UTF8') as f:
        salida = []
        for clave in medidasSistemas['paquetes']:
            for medida in generaFilasMedida(clave, medidasSistemas):
                salida.append(u", ".join([u"%s" % m for m in medida])+ u"\n")
        f.writelines(salida)

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
def renombrar(datastring):
    datastring = datastring.replace(u'CALEFACCIÓN', u'HEATING')
    datastring = datastring.replace(u'REFRIGERACIÓN', u'COOLING')
    datastring = datastring.replace(u'ACS', u'WATERSYSTEMS')
    datastring = datastring.replace(u'VENTILACIÓN', u'FANS')
    return datastring

def readenergystring(datastring):
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

            #TODO: este parsing del comentario es mejor hacerlo en los puntos de uso final, no aquí
            if '-->' in comment:
                servicio, tecnologia, vectorOrigen, combustible, rendimiento = [x.strip() for x in comment.replace('-->', ',').split(',')]
            else:
                servicio = comment.split(',')[0]
                tecnologia, vectorOrigen, combustible, rendimiento = None, None, None, None

            components.append(
                {'carrier': carrier, 'ctype': ctype, 'originoruse': originoruse, 'values': values, 'comment': comment,
                 #TODO: buscar el uso de estas claves
                 'servicio': servicio, 'tecnologia': tecnologia, 'vectorOrigen': vectorOrigen,
                 'combustible': combustible, 'rendimiento': rendimiento})
    return {'componentes': components, 'meta': meta}

def aplicarTecnologia(vector, medidas):
    servicioCubierto = vector['servicio']
    valores = vector['values']
    string_rows = []
    for medida in medidas:
        if medida[1] == u'produccion':
            continue
        [clave, servicio, cobertura, ctipo, src_dst, vectorDestino, rend1, rend2, comentario] = medida
        if servicio == servicioCubierto:
            if not isinstance(rend1, (float, int)):
                rend1 = eval(rend1)
            if not isinstance(rend2, (float, int)):
                rend2 = eval(rend2)
            valoresTransformados = [round(v * cobertura / rend1 / rend2, 2) for v in valores]
            cadena = u"%s, %s, %s, %s # %s, %s" % (vectorDestino, ctipo, src_dst,
                                                  ', '.join([str(v) for v in valoresTransformados]),
                                                  DICT_ENES.get(servicioCubierto, servicioCubierto),
                                                  comentario)
            string_rows.append(cadena)
    if string_rows != []:
        return string_rows
    else:
        cadena = u"%s, %s, %s, %s # %s" % (vector['carrier'],vector['ctype'],vector['originoruse'],
                                          ', '.join([str(v) for v in valores]),
                                          DICT_ENES.get(servicioCubierto, servicioCubierto))
    return [cadena]

def aplicaMedidas(energias, medidas):
    string_rows = []
    for vector in energias:
        resultado = aplicarTecnologia(vector, medidas)
        if isinstance(resultado, list):
            for l in resultado:
                string_rows.append(l)
        else:
            string_rows.append(resultado)

    for medida in medidas:
        if medida[1] == 'produccion':
            [clave, servicio, cobertura, ctipo, src_dst, vectorDestino] = medida[:6]
            valores = [u"%s" % v for v in medida[6:18]]
            comentario = medida[-1]
            cadena = u"%s, %s, %s, %s # %s" % (vectorDestino, ctipo, src_dst, ', '.join(valores), comentario)
            string_rows.append(cadena)

    return string_rows

def seleccionarMedida(archivomedida, medidaaplicada):
    def esNumero(cadena):
        cadena = cadena.strip()
        try:
            salida = float(cadena)
        except:
            salida = cadena
        return salida

    salida = []
    with codecs.open(archivomedida, 'r', 'UTF8') as f:
        for l in f:
            medida = [esNumero(e) for e in l.split(',')]
            if medida[0] == medidaaplicada.strip():
                salida.append(medida)
    return salida

def generaVariante(archivobase, archivomedida, medidaaplicada):
    medidaespecificada = seleccionarMedida(archivomedida, medidaaplicada)

    datastring = codecs.open(archivobase,'r', 'UTF8').read()
    datastring = DICT_ESEN.get(datastring, datastring)
    objetos = readenergystring(datastring)

    string_rows = aplicaMedidas(objetos['componentes'], medidaespecificada)
    variante = {'meta': objetos['meta'], 'componentes': string_rows}

    return variante

def procesaVariantes(proyectoPath):
    medidasSistemas = getMedidasSistemas(proyectoPath)
    # Genera archivos de variantes
    variantes = []
    for (archivoBase, clavesMedidas) in medidasSistemas['variantes']:
        archivomedidas = os.path.join(proyectoPath, 'resultados',  'medidasSistemas.csv')
        archivoSalidaPath = os.path.join(proyectoPath, archivoBase + '.csv')
        for claveMedida in clavesMedidas:
            variante = generaVariante(archivoSalidaPath, archivomedidas, claveMedida)
            variantes.append([archivoBase, claveMedida, variante])
    # Genera registro de variantes
    for (kk, (archivoBase, claveMedida, variante)) in enumerate(variantes):
        basename = os.path.basename(archivoBase)
        filepath = os.path.join(proyectoPath, 'resultados', basename + "_%s.csv" % claveMedida)
        outrows = variante['meta']
        outrows.append("vector,tipo,src_dst")
        outrows = outrows + variante['componentes']
        with codecs.open(filepath, 'w', 'UTF8') as f:
            f.writelines('\n'.join(outrows))
    print(u"* Guardadas %i variantes" % (kk + 1))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Genera variantes aplicando medidas de sistema al caso base')
    parser.add_argument('-v', action='store_true', dest='is_verbose', help='salida detallada')
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help='usa el archivo de configuración CONFIGFILE')
    args = parser.parse_args()
    VERBOSE = args.is_verbose

    config = costes.Config(args.configfile, args.proyectoactivo)
    projectpath = config.proyectoactivo
    print(u"* Generando variantes con sistemas de %s *" % projectpath)
    generaArchivoMedidas(projectpath)
    procesaVariantes(projectpath)
