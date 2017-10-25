# Directorio de proyectos de susPAT
SUSPATPATH:=../../suspat/proyectos
# Podemos seleccionar el proyecto activo usando una variable de entorno
ifeq ($(strip $(proy)),)
PROYECTO:=CosteOptimo
#DocBase
else
PROYECTO:=$(proy)
endif

# Podemos forzar localización con una variable de entorno
ifeq ($(strip $(loc)),)
LOC:=CLIMA
else
LOC:=$(loc)
endif

# Proyectos en directorio de suspat que empiezan por N_ o E_
PROYECTOS:=$(patsubst %/,%,$(subst ${SUSPATPATH}/,,$(sort $(dir $(wildcard ${SUSPATPATH}/[NE]_*/)))))
# Filtra proyectos de suspat con archivo 'noprocesar'
PROYECTOS:=$(foreach dd, $(PROYECTOS), $(if $(wildcard $(SUSPATPATH)/$(dd)/noprocesar), ,$(dd)))
# Intérprete de python, por si queremos usar pypy
PYTHON:=python


.PHONY:singleproj
singleproj:
	# @PYTHONPATH=../../epbdcalc $(PYTHON) ./util_recogecsv.py -v -p $(PROYECTO)
	@$(PYTHON) ./generavariantes.py --cleardir --loc $(LOC) -p $(PROYECTO)
	PYTHONPATH=../../epbdcalc $(PYTHON) ./generamediciones.py -p $(PROYECTO)
	PYTHONPATH=../../epbdcalc $(PYTHON) ./generacostes.py -p $(PROYECTO)
	PYTHONPATH=../../epbdcalc $(PYTHON) ./calculacostes.py -p $(PROYECTO)

.PHONY:getfiles
getfiles:
	@echo "=========== Recogiendo archivos CSV ==========="
	@$(foreach PROJ, ${PROYECTOS}, PYTHONPATH=../../epbdcalc $(PYTHON) ./util_recogecsv.py -v -p $(PROJ);)

.PHONY:genvars
genvars:
	@echo "=========== Generando variantes ==========="
	@$(foreach PROJ, ${PROYECTOS}, $(PYTHON) ./generavariantes.py --cleardir --loc $(LOC) -p $(PROJ);)

.PHONY:genmediciones
genmediciones:
	@echo "=========== Generando mediciones ==========="
	@$(foreach PROJ, ${PROYECTOS}, PYTHONPATH=../../epbdcalc $(PYTHON) ./generamediciones.py -p $(PROJ);)

.PHONY:gencostes
gencostes:
	@echo "=========== Generando costes ==========="
	@$(foreach PROJ, ${PROYECTOS}, PYTHONPATH=../../epbdcalc $(PYTHON) ./generacostes.py -p $(PROJ);)

.PHONY:calculacostes
calculacostes:
	@echo "=========== Calculando costes ==========="
	@$(foreach PROJ, ${PROYECTOS}, PYTHONPATH=../../epbdcalc $(PYTHON) ./calculacostes.py -p $(PROJ);)

.PHONY:all
all: genvars genmediciones gencostes calculacostes

.PHONY:help
help:
	@echo 'Uso:'
	@echo '    make proy=NombreProyecto'
	@echo '    make all'
	@echo 'Procesa el proyecto 'NombreProyecto' o todos los proyectos en SUSPATPATH, excepto aquellos que contengan un archivo "noprocesar" generando los archivos:'
	@echo '- resultados-costes.csv: archivo con costes e indicadores energéticos del proyecto'
	@echo '- resultados_mediciones.yaml: archivo de mediciones (geométricas y energéticas) del proyecto'
diff:
# diff ../proyectos/DocBase/resultados ../proyectos/DocBase/resultados.bak -x '*.log' -x '*.yaml'
	kdiff3 ../proyectos/DocBase/resultados ../proyectos/$(PROYECTO)/resultados.bak

# ejecutar: make proy=<carpeta de proyecto>
