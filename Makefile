

all:
	@echo 'Please choose between `make chromadb` or `make tests` or `make clean`'


tests:
	python -m pytest tests/

chromadb:
	python app/db.py

clean:
	rm -rf chroma.db
	rm -f  content_items.xlsx

