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
import datetime
import glob
import os
import yaml
import argparse
import costes
from pyepbd import readenergyfile, saveenergyfile, readfactors
from pyepbd import compute_balance, weighted_energy

###############################################################

def generaMediciones(proyectoPath, fpeppath, fpco2path):
    """Guarda mediciones, con indicadores energéticos y de emisiones de variantes

    Toma los archivos de factores de paso y los factores de exportación
    y resuministro de los datos del proyecto.
    """
    fp_ep = readfactors(fpeppath)
    fp_co2 = readfactors(fpco2path)
    k_rdel = 0.0
    k_exp = 0.0

    # Genera variantes
    variantes = []
    filepaths = glob.glob(os.path.join(proyectoPath, 'resultados', '*.csv'))
    filepaths = [filepath for filepath in filepaths if 'medidasSistemas' not in filepath]
    for filepath in filepaths:
        meta, data = readenergyfile(filepath)

        # Soluciones constructivas y paquete de sistemas
        soluciones = {}
        if u'PaqueteSistemas' in meta:
            soluciones[meta[u'PaqueteSistemas']] = 1
        for clave in meta:
            if clave.startswith(u'medicion') and not clave.startswith(u'medicion_PT_'):
                soluciones[clave] = meta[clave][0]
        
        # Consumos
        balance = compute_balance(data, k_rdel)
        consumos = { carrier: balance[carrier]['annual']['grid']['input']
                     for carrier in balance if carrier != 'MEDIOAMBIENTE' }

        # Energía primaria
        # TODO: guardar valores por m2?
        # EP_nren_m2 = EP_nren / A_ref
        EP = weighted_energy(balance, fp_ep, k_exp)
        epnren, epren = EP['EP']['nren'], EP['EP']['ren']
        epanren, eparen = EP['EPpasoA']['nren'], EP['EPpasoA']['ren']
        eprimaria = { u"EP_nren": epnren, u"EP_ren": epren, u"EP_tot": epren + epnren,
                      u"EPA_nren": epanren, u"EPA_ren": eparen, u"EPA_tot": eparen + epanren }

        # Emisiones
        CO2 = weighted_energy(balance, fp_co2, k_exp)
        co2 = CO2['EP']['nren'] + CO2['EP']['ren']
        co2a = CO2['EPpasoA']['nren'] + CO2['EPpasoA']['ren']
        emisiones = { u"CO2": co2, u"CO2A": co2a }

        timestamp = "{:%d/%m/%Y %H:%M}".format(datetime.datetime.today())
        variantes.append({ 'timestamp': timestamp,
                           'proyecto': os.path.basename(os.path.normpath(proyectoPath)),
                           'archivo': os.path.basename(filepath),
                           'soluciones': soluciones,
                           'consumos': consumos,
                           'eprimaria': eprimaria,
                           'emisiones': emisiones
                       })
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
    # TODO: hacer a través de config
    fpeppath = os.path.join(projectpath, 'factores_paso_EP.csv')
    fpco2path = os.path.join(projectpath, 'factores_paso_CO2.csv')
    print(u"* Generando indicadores energéticos y de emisiones de %s *" % projectpath)
    mediciones = generaMediciones(projectpath, fpeppath, fpco2path)

    # Registro de medidas por variante y paquete
    logpath = os.path.join(projectpath, 'resultados', 'generamediciones.log')
    with codecs.open(logpath, 'w', 'utf-8') as ff:
        ff.write("\n".join(u"%s, %s, %s" % (datadict['timestamp'],
                                        datadict['proyecto'],
                                        datadict['archivo']) for datadict in mediciones))

    medicionespath = os.path.join(projectpath, 'resultados', 'mediciones.yaml')
    with codecs.open(medicionespath, 'w', 'utf-8') as outfile:
        yaml.safe_dump(mediciones, outfile, default_flow_style=False)

    print(u"* Revisadas %i variantes" % len(mediciones))
