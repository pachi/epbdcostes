test:
	python ./generavariantes.py -p DocBase
	PYTHONPATH=../../epbdcalc python ./generamediciones.py -p DocBase
	# diff ../proyectos/DocBase/resultados ../proyectos/DocBase/resultados.bak -x '*.log' -x '*.yaml'
	PYTHONPATH=../../epbdcalc python ./calculacostes.py -p DocBase
diff:
	kdiff3 ../proyectos/DocBase/resultados ../proyectos/DocBase/resultados.bak
