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
import datetime
import glob
import os
import yaml
import argparse
import costes
from pyepbd import readenergyfile, saveenergyfile, readfactors
from pyepbd import compute_balance, weighted_energy

###############################################################

def generaMediciones(config):
    """Guarda mediciones, con indicadores energéticos y de emisiones de variantes

    Toma los archivos de factores de paso y los factores de exportación
    y resuministro de los datos del proyecto.
    """
    fp_ep = readfactors(os.path.join(config.basedir, 'factores_paso_EP.csv'))
    fp_co2 = readfactors(os.path.join(config.basedir, 'factores_paso_CO2.csv'))
    k_rdel = 0.0
    k_exp = 0.0

    # Genera variantes
    variantes = []
    filepaths = glob.glob(os.path.join(config.variantesdir, '*.csv'))
    filepaths = [filepath for filepath in sorted(filepaths) if 'medidasSistemas' not in filepath]
    for filepath in filepaths:
        meta, data = readenergyfile(filepath)

        # Soluciones constructivas y paquete de sistemas
        soluciones = {}
        if u'PaqueteSistemas' in meta:
            soluciones[meta[u'PaqueteSistemas']] = 1
        for clave in meta:
            if clave.startswith(u'medicion_') and not clave.startswith(u'medicion_PT_'):
                soluciones[clave[len(u'medicion_'):]] = meta[clave][0]

        # Metadatos de area y volumen
        area = meta.get('Area_ref', 1)
        volumen = meta.get('Vol_ref', 1)
        meta = {'superficie': area, 'volumen': volumen}

        # Demandas
        demanda = {}
        
        # Consumos
        balance = compute_balance(data, k_rdel)
        consumos = { carrier: balance[carrier]['annual']['grid']['input']
                     for carrier in balance if carrier != 'MEDIOAMBIENTE' }

        # Energía primaria
        EP = weighted_energy(balance, fp_ep, k_exp)
        epnren, epren = EP['EP']['nren'], EP['EP']['ren']
        #epanren, eparen = EP['EPpasoA']['nren'], EP['EPpasoA']['ren']
        eprimaria = { u"EP_nren": epnren, u"EP_ren": epren, u"EP_tot": epren + epnren,
                      #u"EPA_nren": epanren, u"EPA_ren": eparen, u"EPA_tot": eparen + epanren
        }

        # Emisiones
        CO2 = weighted_energy(balance, fp_co2, k_exp)
        co2 = CO2['EP']['nren'] + CO2['EP']['ren']
        # co2a = CO2['EPpasoA']['nren'] + CO2['EPpasoA']['ren']
        emisiones = { u"CO2": co2 } # , u"CO2A": co2a }

        # timestamp = "{:%d/%m/%Y %H:%M}".format(datetime.datetime.today())
        variantes.append(
            [ # 'timestamp': timestamp,
                # os.path.basename(os.path.normpath(proyectoPath)),
                os.path.basename(filepath),
                soluciones,
                meta,
                eprimaria,
                emisiones,
                demanda,
                consumos,
            ]
        )
    return variantes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Guarda indicadores energéticos y de emisiones en variantes')
    parser.add_argument('-p', '--project', action='store', dest='proyectoactivo', metavar='PROYECTO')
    parser.add_argument('-c', '--config', action='store', dest='configfile',
                        default='./config.yaml',
                        metavar='CONFIGFILE',
                        help='usa el archivo de configuración CONFIGFILE')
    args = parser.parse_args()

    config = costes.Config(args.configfile, args.proyectoactivo)
    projectpath = config.proyectoactivo
    proyecto = os.path.basename(os.path.normpath(projectpath))
    timestamp = "{:%d/%m/%Y %H:%M}".format(datetime.datetime.today())
    # TODO: hacer a través de config
    print(u"* Generando indicadores energéticos y de emisiones de %s *" % projectpath)
    mediciones = generaMediciones(config)
    print(u"* Revisadas %i variantes" % len(mediciones))

    # Registro de medidas por variante y paquete
    logpath = os.path.join(config.logsdir, 'generamediciones.log')
    with codecs.open(logpath, 'w', 'utf-8') as ff:
        ff.write("\n".join(u"%s, %s, %s" % (timestamp, proyecto, caso[0]) for caso in mediciones))
    # Archivo de mediciones en yaml
    with codecs.open(config.medicionespath, 'w', 'utf-8') as outfile:
        header = u"""# Mediciones de soluciones constructivas, emisiones y consumos de combustible
#
# - ['id', 'soluciones', 'emisiones', 'consumos', 'eprimaria', 'metadatos']
#
# Las emisiones y consumos son los valores totales anuales de
# la variante, no anuales por m2.
#
# CO2 - emisiones de CO2 (kgCO2e/año)
# Se consideran consumos anuales para los usos de combustible
# gasoleoc - consumo de gasoleoc (kWhf/año)
# glp - consumo de glp (kWhf/año)
# electricidad - consumo de electricidad (kWhf/año)
# biomasa - consumo de biomasa (kWhf/año)
#
# Generado: %s
# Proyecto: %s
""" % (timestamp, proyecto)
        data = yaml.safe_dump(mediciones, default_flow_style=False)
        outfile.write(header + u"\n" + data)
