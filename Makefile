
PYTHONPATH=$(pwd)


VERSION:=$(shell cat VERSION.txt)
IMAGE=x-language-search


all:	app/*.py tests/*.py requirements.txt Dockerfile docker-compose.yml
	@echo "Building $(IMAGE):$(VERSION)"
	docker build -t $(IMAGE):$(VERSION) . --network=host && docker compose down && docker compose  --env-file .env up -d


docker-build:	app/*.py tests/*.py requirements.txt Dockerfile docker-compose.yml
	@echo "Building $(IMAGE):$(VERSION)"
	docker build -t $(IMAGE):$(VERSION) . --network=host 


restart:
	docker compose down && docker compose  --env-file .env up -d

docker-rmi:
	docker compose down
	docker rmi  $(IMAGE):$(VERSION)

tests:
	python -m pytest tests/

lint:
	python -m pycodestyle --config=pycodestyle app/*.py  tests/*.py

chromadb:
	python app/db.py

clean:
	docker rmi $(IMAGE):$(VERSION)
	rm -rf chroma.db
	rm -f  content_items.xlsx
	rm -rf app/__pycache__

