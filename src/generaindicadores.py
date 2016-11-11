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
from pyepbd import readenergyfile, saveenergyfile, readfactors, weighted_energy

###############################################################

def generaIndicadores(proyectoPath, fpeppath, fpco2path):
    """Guarda indicadores energéticos y de emisiones de variantes

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
        EP = weighted_energy(data, fp_ep, k_rdel, k_exp)
        CO2 = weighted_energy(data, fp_co2, k_rdel, k_exp)
        # TODO: guardar valores por m2?
        # EP_nren_m2 = EP_nren / A_ref
        meta[u"EP_nren"] = EP['EP']['nren']
        meta[u"EP_ren"] = EP['EP']['ren']
        meta[u"EP_tot"] = EP['EP']['nren'] + EP['EP']['ren']
        meta[u"EPA_nren"] = EP['EPpasoA']['nren']
        meta[u"EPA_ren"] = EP['EPpasoA']['ren']
        meta[u"EPA_tot"] = EP['EPpasoA']['nren'] + EP['EPpasoA']['ren']
        meta[u"CO2"] = CO2['EP']['nren'] + CO2['EP']['ren']
        meta[u"CO2A"] = CO2['EPpasoA']['nren'] + CO2['EPpasoA']['ren']
        timestamp = "{:%d/%m/%Y %H:%M}".format(datetime.datetime.today())
        meta[u"Datetime"] = timestamp
        saveenergyfile(filepath, meta, data)
        variantes.append([timestamp, os.path.basename(filepath)])

    # Registro de medidas por variante y paquete
    logpath = os.path.join(proyectoPath, 'resultados', 'generaindicadores.log')
    with codecs.open(logpath, 'w', 'utf-8') as ff:
        ff.write("\n".join(u"%s, %s" % (timestamp, filepath) for (timestamp, filepath) in variantes))

    print(u"* Revisadas %i variantes" % len(filepaths))

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
    generaIndicadores(projectpath, fpeppath, fpco2path)
