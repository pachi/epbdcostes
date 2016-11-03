#!/usr/bin/python
# -*- coding: utf-8 -*-
#

# genera variantes con sistemas a partir de un archivo de (OS) EPDBcalc
# y los compara con otros que puedan haber

import os
import generasistemas as gensis
import codecs

sourcePath = './test/in'
sourceFiles = ['origen_EN0_CS0_S0_V0.csv']#, 'EN0_CS0_S0_V0.csv', 'EN0_CS0_S0_V0_PV.csv', 'EE0_CS0_S0_V0_PV.csv']
destinoPath = './test/out'

def renombrar(datastring):
  datastring = datastring.replace(u'#CALEFACCIÓN', '#HEATING')
  datastring = datastring.replace(u'#REFRIGERACIÓN', '#COOLING')
  datastring = datastring.replace(u'#ACS', '#WATERSYSTEMS')
  datastring = datastring.replace(u'#VENTILACIÓN', '#FANS')
  return datastring

def valores_objeto(objeto):
  componentes = objeto['componentes']
  salida = {}
  for comp in componentes:
    servicio = comp['servicio']
    carrier = comp['carrier']
    if servicio not in salida.keys(): salida[servicio] = {}
    if carrier not in salida[servicio].keys():
      salida[servicio][carrier] = sum(comp['values'])
    else:
      salida[servicio][carrier] += sum(comp['values'])
  return salida

def comparaObjetos(os1, os2):
  # dos objetos son iguales si los valores para servicio_carrier son iguales
  #~ ['servicio', 'tecnologia', 'carrier', 'values', 'vectorOrigen',
  #~ 'rendimiento', 'originoruse', 'combustible', 'ctype']
  valores1 = valores_objeto(os1)
  valores2 = valores_objeto(os2)
  for servicio, carriers in valores1.items():
    for carrier, valor in carriers.items():
      if abs(valor - valores2[servicio][carrier]) > 200:
        print 'no son iguales', servicio, carrier
        print '  local:',  valor
        print ' remoto:', valores2[servicio][carrier]
  for servicio, carriers in valores2.items():
    for carrier, valor in carriers.items():
      if abs(valor - valores1[servicio][carrier]) > 2:
        print 'no son iguales src=2'
        print servicio, carrier, valor
        print valores1[servicio][carrier]

def comparar():
  for destFile in [f for f in os.listdir(destinoPath) if f.endswith('.csv') and f.startswith('origen_')]:

    if os.path.isfile(os.path.join(sourcePath, destFile)):
      print('\n______comparando %s________' %(destFile))
      datastringDestino = codecs.open(os.path.join(destinoPath, destFile),'r','UTF8').read()
      datastringDestino = renombrar(datastringDestino)
      objetosDest = generasistemas.readenergystring(datastringDestino)
      datastringSource = codecs.open(os.path.join(sourcePath, destFile),'r','UTF8').read()
      datastringSource = renombrar(datastringSource)
      objetosSource = generasistemas.readenergystring(datastringSource)

      comparaObjetos(objetosDest, objetosSource)
      print ('________________________')
    else:
      print('\n### ERROR, no existe', os.path.join(sourcePath, destFile))


def generar():
  print 'generando'
  for sourceFile in sourceFiles:
    print '___ leyendo:', sourceFile
    datastring = codecs.open(os.path.join(sourcePath, sourceFile),'r', 'UTF8').read()
    datastring = renombrar(datastring)
    objetos = generasistemas.readenergystring(datastring)

    print '___ aplicando paquetes'
    for medidaSistemas in tecnologias:
      print '___ paquete ', medidaSistemas
      string_rows = generasistemas.aplicarMedidas(objetos['componentes'], tech.medidas(medidaSistemas))
      destFile = sourceFile.replace('_S0_', '_%s_' % medidaSistemas)
      destFile = os.path.join(destinoPath, destFile)
      with open(destFile, 'w') as f:
        f.writelines('\n'.join(objetos['comentarios']))
        f.writelines('\nvector,tipo,src_dst\n')
        f.writelines('\n'.join(string_rows))


proyectoPath = '../proyectos/proyectotest'
resultado = gensis.generaArchivoMedidas(proyectoPath)
#~ print '_generados los paquetes de medidas_', resultado
resultado = gensis.procesaVariantes(proyectoPath)
#~ print '_procesadas las variantes_', resultado

