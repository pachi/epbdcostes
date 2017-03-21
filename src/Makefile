SUSPATPATH:=../../suspat/proyectos
ifeq ($(strip $(proy)),)
PROYECTO:=CosteOptimo
#DocBase
else
PROYECTO:=$(proy)
endif
PROYECTOS:=$(patsubst %/,%,$(subst ${SUSPATPATH}/,,$(sort $(dir $(wildcard ${SUSPATPATH}/[NE]_*/)))))
PYTHON:=python

.PHONY:test
test:
	@PYTHONPATH=../../epbdcalc $(PYTHON) ./util_recogecsv.py -p $(PROYECTO); \
	@$(PYTHON) ./generavariantes.py --cleardir -p $(PROYECTO)
	@PYTHONPATH=../../epbdcalc $(PYTHON) ./generamediciones.py -p $(PROYECTO)
	@PYTHONPATH=../../epbdcalc $(PYTHON) ./generacostes.py -p $(PROYECTO)
	@PYTHONPATH=../../epbdcalc $(PYTHON) ./calculacostes.py -p $(PROYECTO)

.PHONY:getfiles
getfiles:
	@echo "=========== Recogiendo archivos CSV ==========="
	@$(foreach PROJ, ${PROYECTOS}, PYTHONPATH=../../epbdcalc $(PYTHON) ./util_recogecsv.py -p $(PROJ);)

.PHONY:getvars
genvars:
	@echo "=========== Generando variantes ==========="
	$(foreach PROJ, ${PROYECTOS}, $(PYTHON) ./generavariantes.py --cleardir -p $(PROJ);)

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
all: getfiles genvars genmediciones gencostes calculacostes

.PHONY:help
help:
	@echo 'Uso:'
	@echo '    make proy=NombreProyecto'
	@echo '    make all'
	@echo 'Procesa el proyecto 'NombreProyecto' o todos los proyectos en SUSPATPATH, generando los archivos:'
	@echo '- resultados-costes.csv: archivo con costes e indicadores energéticos del proyecto'
	@echo '- resultados_mediciones.yaml: archivo de mediciones (geométricas y energéticas) del proyecto'
diff:
# diff ../proyectos/DocBase/resultados ../proyectos/DocBase/resultados.bak -x '*.log' -x '*.yaml'
	kdiff3 ../proyectos/DocBase/resultados ../proyectos/$(PROYECTO)/resultados.bak

# ejecutar: make proy=<carpeta de proyecto>
