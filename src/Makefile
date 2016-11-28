ifeq ($(strip $(proy)),)
PROYECTO:=DocBase
else
PROYECTO:=$(proy)
endif

test:
	@python ./generavariantes.py --cleardir -p $(PROYECTO)
	@PYTHONPATH=../../epbdcalc python ./generamediciones.py -p $(PROYECTO)
# diff ../proyectos/DocBase/resultados ../proyectos/DocBase/resultados.bak -x '*.log' -x '*.yaml'
	@PYTHONPATH=../../epbdcalc python ./calculacostes.py -p $(PROYECTO)
diff:
	kdiff3 ../proyectos/DocBase/resultados ../proyectos/$(PROYECTO)/resultados.bak
