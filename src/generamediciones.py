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
try:
    from yaml import CSafeDumper as SafeDumper
except ImportError:
    print("Usando loader de YAML en Python (no acelerado). Instale libyaml-dev")
    from yaml import SafeDumper
###############################################################

# Equivalencias en grados día
GD = {
    'pen':  {
        'HDD_15': {'A': 870, 'B': 1130, 'C': 1650, 'D': 2225, 'E': 2750},
        'CDD_25': {'1': 30, '2': 75, '3': 175, '4': 250}
    },
    'can': {
        'HDD_15': {'alpha': 150, 'A': 750, 'B': 1125, 'C': 1575, 'D': 2175, 'E': 2750},
        'CDD_25': {'1': 2, '2': 10, '3': 50, '4': 125}
    }
}

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

        soluciones['VENT%sV%0.3iR%0.3i' % (
            meta.get('Name','').upper(),
            meta.get('Design_flow_rate', 0.0) * 100.0,
            meta.get('Heat_recovery', 0.0) * 100.0)
        ] = 1 # Recuperador de calor

        # Metadatos generales (fecha, area, volumen, zc, peninsularidad)
        arearef = float(meta.get('Area_ref', 1.0))
        weatherfile = meta.get('Weather_file', '').split('_')
        zc = weatherfile[0]
        pen = 2 if len(weatherfile) < 2 else (1 if weatherfile[1].startswith('pen') else 0)
        zcv = zc[-1]
        zci = zc[:-1]
        gd = GD['can'] if pen == 0 else GD['pen']
        hdd = gd['HDD_15'].get(zci, '-')
        cdd = gd['CDD_25'].get(zcv, '-')
        metadata = {
            'name': meta.get('Name', ''),
            'fechacalculo': meta.get('Datetime', ''),
            'tipoedificio': meta.get('Tipo_edificio', ''),
            'usoedificio': meta.get('Uso_edificio', ''),
            'superficie': arearef,
            'volumen': meta.get('Vol_ref', 1.0),
            'compacidad': meta.get('Compacidad', 0.0),
            'K': meta.get('K', 0.0),
            'qsj': meta.get('qsj', 0.0),
            'zc': zc,
            'peninsular': pen,
            'zci': zci,
            'zcv': zcv,
            'HDD_15': hdd,
            'CDD_25': cdd,
            'sistemas': meta.get('PaqueteSistemas', ''),
            'envolvente': meta.get('ConstructionSet', ''),
            'phuecos': meta.get('Permeabilidad_ventanas', ''),
            'ventdiseno': meta.get('Design_flow_rate', 0.0),
            'efrecup': meta.get('Heat_recovery', 0.0)
        }

        # Demandas, ya por m2 de superficie
        dems = ['Demanda_calefaccion', 'Demanda_refrigeracion', 'Demanda_iluminacion_interior',
                'Demanda_iluminacion_exterior', 'Demanda_equipos_interiores', 'Demanda_equipos_exteriores',
                'Demanda_ventiladores', 'Demanda_bombas', 'Demanda_disipacion_calor', 'Demanda_humidificacion',
                'Demanda_recuperacion_calor', 'Demanda_sistemas_agua', 'Demanda_equipos_frigorificos',
                'Demanda_equipos_generacion']
        demanda = {clave: 1.0 * meta.get(clave, 0.0) / arearef for clave in dems}

        # Consumos
        balance = compute_balance(data, k_rdel)
        consumos = {carrier: balance[carrier]['annual']['grid'].get('input', 0.0)
                    for carrier in balance if carrier != 'MEDIOAMBIENTE'}

        termicaproducida = sum([balance['MEDIOAMBIENTE']['annual'][orig].get('input', 0.0)
                                for orig in ['INSITU', 'COGENERACION']
                                if 'MEDIOAMBIENTE' in balance])
        termicaexportada = sum([balance['MEDIOAMBIENTE']['annual'][orig].get('to_grid', 0.0)
                                for orig in ['INSITU', 'COGENERACION']
                                if 'MEDIOAMBIENTE' in balance])
        termicanepb = sum([balance['MEDIOAMBIENTE']['annual']['INSITU'].get('to_nEPB', 0.0)
                           for orig in ['INSITU', 'COGENERACION']
                           if 'MEDIOAMBIENTE' in balance])
        elecproducida = sum([balance[carrier]['annual'][orig].get('input', 0.0)
                             for orig in ['INSITU', 'COGENERACION']
                             for carrier in balance
                             if carrier.startswith("ELECTRICIDAD")])
        elecexportada = sum([balance[carrier]['annual'][orig].get('to_grid', 0.0)
                             for orig in ['INSITU', 'COGENERACION']
                             for carrier in balance
                             if carrier.startswith("ELECTRICIDAD")])
        elecnepb = sum([balance[carrier]['annual']['INSITU'].get('to_nEPB', 0.0)
                        for orig in ['INSITU', 'COGENERACION']
                        for carrier in balance
                        if carrier.startswith("ELECTRICIDAD")])

        producciones = {
            'termica_prod_kWh_an': termicaproducida,
            'termica_exp_kWh_an': termicaexportada,
            'termica_nepb_kWh_an': termicanepb,
            'electr_prod_kWh_an': elecproducida,
            'electr_exp_kWh_an': elecexportada,
            'electr_nepb_kWh_an': elecnepb
        }

        # Energía primaria y energía eléctrica o térmica producida, exportada a nEPB o a la red
        EP = weighted_energy(balance, fp_ep, k_exp)
        epnren, epren = EP['EP']['nren'], EP['EP']['ren']
        #epanren, eparen = EP['EPpasoA']['nren'], EP['EPpasoA']['ren']
        eprimaria = {u"EP_nren": epnren,
                     u"EP_ren": epren,
                     u"EP_tot": epren + epnren,
                     u"EP_nren_m2": epnren / arearef,
                     u"EP_ren_m2": epren / arearef,
                     u"EP_tot_m2": (epren + epnren) / arearef,
                     #u"EPA_nren": epanren,
                     #u"EPA_ren": eparen,
                     #u"EPA_tot": eparen + epanren
                     u"produccion": producciones,
                 }

        # Emisiones
        CO2 = weighted_energy(balance, fp_co2, k_exp)
        co2 = CO2['EP']['nren'] + CO2['EP']['ren']
        # co2a = CO2['EPpasoA']['nren'] + CO2['EPpasoA']['ren']
        emisiones = {u"CO2": co2} # , u"CO2A": co2a }

        # timestamp = "{:%d/%m/%Y %H:%M}".format(datetime.datetime.today())
        variantes.append(
            [ # 'timestamp': timestamp,
                # os.path.basename(os.path.normpath(proyectoPath)),
                os.path.basename(filepath),
                soluciones,
                metadata,
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
    print(u"- Revisadas %i variantes" % len(mediciones))

    # Registro de medidas por variante y paquete
    if not os.path.exists(config.logsdir):
        os.makedirs(config.logsdir)
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
        data = yaml.dump(mediciones, default_flow_style=False, Dumper=SafeDumper)
        outfile.write(header + u"\n" + data)
