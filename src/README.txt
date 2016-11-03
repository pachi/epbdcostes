EPBDcostes
==========

generasistemas
--------------

Script que aplica medidas de sistemas a un caso base.

El caso base es el resultado de la simulación de un modelo de OpenStudio (OSM) con sistemas ideales y
con la medida de EPBDcalc.

Para ejecutar este scrip es necesiario que en el directorio del proyecto se encuentre el archivo medidasSistemas.yaml, que contiene:

- un primer apartado donde se describen los sistemas que se pueden aplicar, indicando datos como el servicio que cubren, el combustible, los rendimientos, etc.
- un segundo apartado donde se definen los paquetes de medidas, esto es conjuntos de tecnologías que se aplican juntas. Para cada una hay que indicar el porcentaje de servicio que cubre (en tanto por uno).
- el tercer apartado indica las combinaciones entre archivos base y paquetes de media que se le aplican

para ejecutarlo: ./generasistemas.py -p <nombre del proyecto>
