EPBDcostes
==========

generavariantes
---------------

Genera variantes aplicando paquetes de sistemas a casos base.

Los casos base son el resultado de la simulación de un modelo de OpenStudio (OSM) con sistemas ideales y
con la medida de EPBDcalc.

Para ejecutar este script es necesiario que en el directorio del proyecto se encuentre el archivo sistemas.yaml, que contiene:

- un primer apartado donde se describen los sistemas que se pueden aplicar,
  indicando datos como el servicio que cubren, el combustible, los rendimientos, etc.
- un segundo apartado donde se definen los paquetes de medidas,
  esto es, conjuntos de tecnologías que se aplican juntas.
  Para cada una hay que indicar el porcentaje de servicio que cubre (en tanto por uno).
- el tercer apartado indica las combinaciones entre archivos base y paquetes de media que se le aplican

para ejecutarlo: ./generavariantes.py -p <nombre del proyecto>

Genera las variantes en el directorio 'resultados' del proyecto.

generamediciones
----------------

Guarda mediciones geométricas, de sistemas y de indicadores de energía y emisiones.

Parte de un proyecto con variantes en formato EPPBDcalc.

Las variantes se localizan como archivos .csv en el directorio 'variantes' del proyecto.

para ejecutarlo: ./generaindicadores.py -p <nombre del proyecto>

genera el archivo 'resultados_mediciones.yaml' en el directorio base del proyecto.

calculacostes
-------------

Guarda archivo 'resultados_costes.csv' de mediciones de variantes.

Usa el archivo 'resultados_mediciones.yaml' para el cálculo de costes y genera el archivo
'resultados_costes.csv' en el directorio base del proyecto.

