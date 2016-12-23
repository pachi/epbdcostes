#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Cálculo de costes para estudio de coste óptimo
#
# DB-HE 2013
#

from __future__ import print_function
import io
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from collections import OrderedDict, defaultdict, namedtuple
from . import costeslogging
from .utils import memoize, cached_property, memoizefunc

logger = costeslogging.setup()
debug, info, warn, error, critical = logger.debug, logger.info, logger.warn, logger.error, logger.critical

Variante = namedtuple('Variante', ['id', 'soluciones', 'emisiones', 'consumos', 'eprimaria', 'metadatos'])

class Solucion(object):
    """Solución constructiva

    Permite calcular los costes de la solución (inicial, mantenimiento o reposición)
    para un periodo.
    """
    def __init__(self, name, data):
        self.nombre = name
        self.desc = data.get('desc', "")
        self.vutil = data.get('vutil', 0.0)
        self.pmant = data.get('pmant', 0.0)
        self.cinicial = data.get('cinicial', {'macro':0.0, 'micro':0.0})
        self.creposicion = data.get('creposicion', self.cinicial)
        self.cmant = data.get('cmant', {'macro':0.0, 'micro':0.0})

    def describe(self):
        _repr = u"Solucion(%s, {'desc': %s, 'cmant': %.3f, 'pmant': %3i, 'vutil': %3i})"
        return _repr % (self.nombre, self.desc, self.cmant, self.pmant, self.vutil)

    @memoize
    def costeinicial(self, tipo):
        """Coste inicial de la solución para el tipo dado"""
        return self.cinicial[tipo]

    @memoize
    def costereposicion(self, tipo):
        """Coste de reposición de la solución para el tipo dado"""
        return self.creposicion[tipo]

    def costemantenimientoi(self, iyear, tipo):
        """Coste de mantenimiento de la solución en el año iyear"""
        if self.cmant[tipo] == 0 or self.pmant == 0:
            cmanti = 0.0
            warn(u"Periodo o coste de mantenimiento no definido para %s" % self.nombre)
        else:
            cmanti = self.cmant[tipo] if ((iyear+1) % self.pmant == 0) else 0.0
            _msg = u"Coste de mantenimiento (solución '%s', año %2i, periodicidad %2i): %.3f"
            info(_msg % (self.nombre, iyear, self.pmant, cmanti))
        return cmanti

    @memoize
    def costesmantenimiento(self, tipo, periodo):
        """Costes de mantenimiento para el periodo"""
        return [self.costemantenimientoi(iyear, tipo) for iyear in range(periodo)]

    def costereposicioni(self, iyear, tipo):
        """Coste de reposición de la solución en el año iyear"""
        if self.costereposicion(tipo) == 0 or self.vutil == 0:
            creposicioni = 0.0
            warn(u"Periodo o coste de reposición no definido para %s", self.nombre)
        else:
            creposicioni = self.costereposicion(tipo) if ((iyear+1) % self.vutil == 0) else 0.0
            _msg = u"Coste de reposición (solución '%s', año %2i, periodicidad %2i): %.3f"
            info(_msg % (self.nombre, iyear, self.vutil, creposicioni))
        return creposicioni

    @memoize
    def costesreposicion(self, tipo, periodo):
        """Costes de reposición para el periodo según tipo"""
        return [self.costereposicioni(iyear, tipo) for iyear in range(periodo)]

    @memoize
    def valorresidual(self, tipo, periodo):
        """Valor residual de la solución al final del periodo

        Se suponen realizadas las reposiciones intermedias del periodo.
        """
        if self.vutil != 0:
            nreposiciones = int(periodo / self.vutil)
            lifefractionleft = ((nreposiciones + 1.0) * self.vutil - periodo) / self.vutil
            valorresidual = self.costereposicion(tipo) * lifefractionleft
        else:
            valorresidual = 0.0
        return valorresidual

    @memoize
    def costes(self, tipo, periodo):
        """Costes anuales de la solución para el periodo dado

        Incluye coste inicial, de reposición, de mantenimiento y valor residual
        """
        costes = [a + b for a, b in zip(self.costesmantenimiento(tipo, periodo),
                                        self.costesreposicion(tipo, periodo))]
        costes[0] += self.costeinicial(tipo)
        costes[-1] -= self.valorresidual(tipo, periodo)
        return costes

    def cadenayaml(self):
        stryaml = u'%s:\n\
  desc: %s\n\
  vutil: %s #años\n\
  pmant: %s #años\n\
  cinicial:\n\
    macro: %s #€/m2\n\
    micro: %s #€/m2\n\
  creposicion:\n\
    macro: %s #€/m2\n\
    micro: %s #€/m2\n\
  cmant:\n\
    macro: %s #€/m2\n\
    micro: %s #€/m2\n'
        print(self.nombre)
        print(u'nombre %s' % self.nombre)#, self.desc, self.vutil, self.pmant, self.cinicial['macro'], self.cinicial['micro'], self.creposicion['macro'], self.creposicion['micro'], self.cmant['macro'], self.cmant['micro']


        return stryaml % (self.nombre, self.desc, self.vutil, self.pmant,
                self.cinicial['macro'], self.cinicial['micro'],
                self.creposicion['macro'], self.creposicion['micro'],
                self.cmant['macro'], self.cmant['micro'])


class Escenario(object):
    """Escenario de cálculo: periodo, año base, precios de CO2 y combustibles"""
    def __init__(self, tipo='macro', tasa=None,
                 parametrosfile='parametroscostes.yaml'):
        """Lee los parámetros de cálculo del archivo de configuración

        tipo: escemario para cálculo macroeconómico o microeconómico
        tasa: tasa de descuento aplicable. Se elige la indicada o la
        primera entre las del tipo indicado.
        TODO: No descontar aquí los valores de CO2 o energía
        """
        def _cargaparametros(filename):
            with io.open(filename, 'r', encoding='utf-8') as parametrosfile:
                parametros = yaml.load(parametrosfile, Loader=Loader)
            return parametros

        self._parametrosfile = parametrosfile
        self._parametros = _cargaparametros(parametrosfile)
        self.periodo = self._parametros['periodo']['duracion']
        self.base = self._parametros['periodo']['base']
        if tipo in ['macro', 'micro']:
            self.tipo = tipo
        else:
            msg = "Solamente se contemplan análisis 'macro' y 'micro'"
            critical(msg)
            raise TypeError(msg)
        self.tasa = float(tasa) if tasa else 0.0
        self.preciosbaseCO2 = self._parametros['CO2']['precios']
        self.basepreciosCO2 = self._parametros['CO2']['base']
        self.baseenergia = self._parametros['energia']['base']
        self.annosenergia = self._parametros['energia']['annos']
        self.preciosbaseenergia = self._parametros['energia']['precios']

    def __repr__(self):
        return "Escenario(%s, %i, %s)" % (self.tipo, self.tasa, self._parametrosfile)

    @property
    def preciosco2(self):
        """Costes anuales actualizados de emisiones de CO2(teq) del periodo

        Se actualizan los precios de CO2 tomando como base el año basepreciosCO2
        con la tasa de descuento del escenario
        """
        if self.base != self.basepreciosCO2:
            msg = "No coincide el año base con el de precios de CO2"
            critical(msg)
            raise Exception(msg)
        preciosco2 = []
        for iyear in range(self.periodo):
            calcyear = None
            for stepyear in sorted(self.preciosbaseCO2.keys()):
                if (iyear + self.base) <= stepyear:
                    calcyear = stepyear
                    break
            preciosco2.append(self.preciosbaseCO2[calcyear])
        return descuenta(preciosco2, self.tasa)

    @cached_property
    def preciosenergia(self):
        """Costes anuales actualizados de la energía en el periodo, por combustible

        Los precios se actualizan usando el año base de precios de energía
        y la tasa de descuento del escenario
        """
        if self.baseenergia != self.base:
            msg = "No coincide el año base con el de energía"
            critical(msg)
            raise Exception(msg)
        def _interpola(x, x1, x2, y1, y2):
            """Interpola el valor de y para x entre (x1,y1) y (x2,y2)"""
            return y1 + (x - x1) * 1.0 * (y2 - y1) / (x2 - x1)

        precios = self.preciosbaseenergia[self.tipo]
        combustibles = precios.keys()
        annosenergia = self.annosenergia

        preciosperiodo = defaultdict(list)
        for i in range(self.periodo):
            anno = self.base + i
            i2 = next(i for i,v in enumerate(annosenergia) if v > anno)
            i1 = i2 - 1
            for combustible in combustibles:
                precio = _interpola(anno,
                                    annosenergia[i1],
                                    annosenergia[i2],
                                    precios[combustible][i1],
                                    precios[combustible][i2])
                preciosperiodo[combustible].append(precio)
        for combustible in combustibles:
            pcombustible = preciosperiodo[combustible]
            preciosperiodo[combustible] = descuenta(pcombustible, self.tasa)

        return preciosperiodo

def coste(variante, escenario, soluciones):
    """Coste macroeconómico o financiero de la variante (descontado)

    variante - variante calculada, compuesta por:
    - soluciones - catálogo de costes de soluciones aplicables a la variante
    - emisiones - emisiones anuales de CO2 (ton/año)
    - consumos - consumo anual de energía, por combustible (kWh/año)
    escenario - escenario de cálculo. Determina el tipo de
                análisis (micro o macro y la tasa utilizada)
    """
    tipo = escenario.tipo
    periodo = escenario.periodo
    coste = 0.0
    tasa = escenario.tasa
    if variante.soluciones:
        for solucion in variante.soluciones:
            sol = soluciones[solucion]
            costesol = sum(descuenta(sol.costes(tipo, periodo), tasa))
            cantidad = variante.soluciones[solucion]
            coste += costesol * cantidad
    if tipo == 'macro':
        # emisiones anuales
        coste += variante.emisiones['CO2'] * sum(escenario.preciosco2)
    preciosenergia = escenario.preciosenergia
    for combustible in variante.consumos:
        coste += (variante.consumos[combustible] *
                  sum(preciosenergia[combustible]))
    return coste

def costeinicial(variante, escenario, soluciones):
    """Coste inicial de las medidas en la variante (descontado)

    variante - variante calculada, compuesta por:
    - soluciones - soluciones aplicadas en la variante
    - emisiones - emisiones anuales de CO2 (ton/año)
    - consumos - consumo anual de energía, por combustible (kWh/año)
    escenario - escenario de cálculo. Determina el tipo de
                análisis (micro o macro y la tasa utilizada)
    """
    tipo = escenario.tipo
    coste = 0.0
    if variante.soluciones:
        for solucion in variante.soluciones:
            cantidad = variante.soluciones[solucion]
            coste += (soluciones[solucion].costeinicial(tipo) *
                      cantidad)
    return coste

def costemantenimiento(variante, escenario, soluciones):
    """Coste de mantenimiento de la variante en el periodo (descontado)"""
    tipo = escenario.tipo
    periodo = escenario.periodo
    coste = 0.0
    if variante.soluciones:
        for solucion in variante.soluciones:
            sol = soluciones[solucion]
            cantidad = variante.soluciones[solucion]
            coste += sum(descuenta(sol.costesmantenimiento(tipo, periodo), escenario.tasa)) * cantidad
    return coste

def costereposicion(variante, escenario, soluciones):
    """Coste de reposición de la variante en el periodo (descontado)"""
    tipo = escenario.tipo
    periodo = escenario.periodo
    coste = 0.0
    if variante.soluciones:
        for solucion in variante.soluciones:
            sol = soluciones[solucion]
            cantidad = variante.soluciones[solucion]
            coste += sum(descuenta(sol.costesreposicion(tipo, periodo), escenario.tasa)) * cantidad
    return coste

def costesoperacion(variante, escenario):
    """Costes de operación por combustible de la variante en el periodo (descontado)"""
    preciosenergia = escenario.preciosenergia
    costes = defaultdict(float)
    for combustible in variante.consumos:
        costes[combustible] = variante.consumos[combustible] * sum(preciosenergia[combustible])
    return costes

def costeco2(variante, escenario):
    """Coste de las emisiones de la variante en el periodo (descontado)"""
    if escenario.tipo == 'macro':
        # emisiones anuales
        coste = variante.emisiones['CO2'] * sum(escenario.preciosco2)
    else:
        coste = 0.0
    return coste

def valorresidual(variante, escenario, soluciones):
    """Valor residual de la variante al final del periodo (descontado)"""
    tipo = escenario.tipo
    periodo = escenario.periodo
    tasa = escenario.tasa
    valor = 0.0
    if variante.soluciones:
        for solucion in variante.soluciones:
            sol = soluciones[solucion]
            cantidad = variante.soluciones[solucion]
            valor += sol.valorresidual(tipo, periodo) * cantidad
    return factordescuento(periodo - 1, tasa) * valor

@memoizefunc
def factordescuento(iyear, rate):
    """Factor de descuento para el año iyear con la tasa rate

    iyear: el año base se considera el año 0
    rate: tasa de descuento en tanto por ciento
    """
    return (1.0 / (1.0 + rate / 100.0)**(iyear))

def descuenta(costlist, rate):
    """Devuelve costes descontados al año de inicio con tasa rate

    Se consideran años correlativos en la lista
    """
    return [factordescuento(i, rate) * cost for i, cost in enumerate(costlist)]

def cargacostes(filename='solucionescostes.yaml'):
    with io.open(filename, 'r', encoding='utf-8') as costesfile:
        costesdata = yaml.load(costesfile, Loader=Loader)
        costes = OrderedDict()
        for name in costesdata:
            costes[name] = Solucion(name, costesdata[name])
    return costes

def cargamediciones(filename='mediciones.yaml', solucionesdefinidas=None):
    mediciones = []
    with io.open(filename, 'r', encoding='utf-8') as medicionesfile:
        medicionesdata = yaml.load(medicionesfile, Loader=Loader)
        for linea in medicionesdata:
            variante = Variante._make(linea)
            mediciones.append(variante)
            if solucionesdefinidas:
                for solucion in variante.soluciones:
                    if solucion not in solucionesdefinidas:
                        msg = (u"Solución '%s' no presupuestada en el caso %s"
                               % (solucion, variante.id))
                        critical(msg)
                        raise KeyError(msg)
    return mediciones

