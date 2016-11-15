test:
	python ./generasistemas.py -p DocBase
	PYTHONPATH=../../epbdcalc python ./generamediciones.py -p DocBase
	diff ../proyectos/DocBase/resultados ../proyectos/DocBase/resultados.bak -x '*.log' -x '*.yaml'
diff:
	kdiff3 ../proyectos/DocBase/resultados ../proyectos/DocBase/resultados.bak
