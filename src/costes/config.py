#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Módulo de configuración
#
# DB-HE 2013
#
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
        return self.proyectoactivo

    @property
    def variantesdir(self):
        return os.path.join(self.proyectoactivo,'variantes')

    @property
    def logsdir(self):
        return os.path.join(self.proyectoactivo,'logs')

    # archivos específicos
    @property
    def sistemaspath(self):
        return os.path.join(self.proyectoactivo, 'sistemas.yaml')

    @property
    def parametrospath(self):
        return os.path.join(self.proyectoactivo, 'parametroscostes.yaml')

    @property
    def costespath(self):
        return os.path.join(self.proyectoactivo, 'solucionescostes.yaml')

    @property
    def medicionespath(self):
        return os.path.join(self.proyectoactivo, 'resultados_mediciones.yaml')

    @property
    def resultadospath(self):
        return os.path.join(self.proyectoactivo, 'resultados_costes.csv')
