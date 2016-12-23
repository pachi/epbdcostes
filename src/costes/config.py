#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Módulo de configuración
#
# DB-HE 2013
#

from __future__ import print_function
import sys
import os.path
import yaml

DEFAULTBASEPATH = os.path.abspath(os.path.join('..', 'proyectos'))

class Config(object):
    """Objeto de configuración global"""
    def __init__(self, filename=None, proyectoactivo=None, basepath=DEFAULTBASEPATH):
        """Carga el archivo de configuración y fija el proyecto activo"""
        if filename:
            self.load(filename)
        if proyectoactivo:
            # permite cambiar el proyecto activo respecto al del archivo de configuración
            self.proyectoactivo = os.path.abspath(os.path.join(basepath, proyectoactivo))
        if not(os.path.isdir(self.proyectoactivo)):
            msg = u"ERROR: No se localiza el directorio del proyecto activo: %s\n"
            sys.stderr.write(msg % self.proyectoactivo)
            sys.exit(1)

    def load(self, filename):
        if not filename:
            filename = os.path.abspath(os.path.join(__file__, '..', 'config.yaml'))
        try:
            with open(filename, 'r') as configfile:
                self._config = yaml.load(configfile)
        except:
            print(u"Archivo de configuración no encontrado: ", os.path.abspath(filename))
        self.proyectoactivo = self._config['proyectoactivo']
        self.escenarios = self._config['escenarios']

    # directorios generales
    @property
    def basedir(self):
        "Directorio base del proyecto"
        return self.proyectoactivo

    @property
    def variantesbasedir(self):
        "Directorio de variantes base"
        return os.path.join(self.proyectoactivo,'variantesbase')

    @property
    def variantesdir(self):
        "Directorio de variantes generadas"
        return os.path.join(self.proyectoactivo,'variantes')


    @property
    def logsdir(self):
        "Directorio de registros de actividad (logs)"
        return os.path.join(self.proyectoactivo,'logs')

    # archivos específicos
    @property
    def sistemaspath(self):
        "Ruta de archivo de definición de sistemas y paquetes de sistemas"
        return os.path.join(self.proyectoactivo, 'variantes_sistemas.yaml')

    @property
    def costesconfigpath(self):
        "Ruta de archivo de configuración general de costes (escenarios, precios energía"
        return os.path.join(self.proyectoactivo, 'costes_config.yaml')

    @property
    def costespath(self):
        "Ruta de archivo de costes de soluciones constructivas y sistemas del proyecto"
        return os.path.join(self.proyectoactivo, 'costes_soluciones.yaml')

    @property
    def medicionespath(self):
        "Ruta del archivo de resultados de mediciones"
        return os.path.join(self.proyectoactivo, 'resultados_mediciones.yaml')

    @property
    def resultadospath(self):
        "Ruta del archivo de resultados del cálculo de costes"
        return os.path.join(self.proyectoactivo, 'resultados_costes.csv')

