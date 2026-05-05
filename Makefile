.PHONY: setup

setup:
	pip install -r requirements.txt
	mkdir -p data
	@echo "Ambiente configurado. Coloque seus CSVs em data/"
