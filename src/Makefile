SUSPATPATH:=../../suspat/proyectos
ifeq ($(strip $(proy)),)
PROYECTO:=CosteOptimo
#DocBase
else
PROYECTO:=$(proy)
endif
PROYECTOS=$(patsubst %/,%,$(subst ${SUSPATPATH}/,,$(sort $(dir $(wildcard ${SUSPATPATH}/[NE]_*/)))))

test:
	@python ./generavariantes.py --cleardir -p $(PROYECTO)
	@PYTHONPATH=../../epbdcalc python ./generamediciones.py -p $(PROYECTO)
	@PYTHONPATH=../../epbdcalc python ./generacostes.py -p $(PROYECTO)
	@PYTHONPATH=../../epbdcalc python ./calculacostes.py -p $(PROYECTO)
all:
	@echo ${PROYECTOS}
	@$(foreach PROJ, ${PROYECTOS}, \
		python ./generavariantes.py --cleardir -p $(PROJ); \
		PYTHONPATH=../../epbdcalc python ./generamediciones.py -p $(PROJ); \
		PYTHONPATH=../../epbdcalc python ./generacostes.py -p $(PROJ); \
		PYTHONPATH=../../epbdcalc python ./calculacostes.py -p $(PROJ) \
	)
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
