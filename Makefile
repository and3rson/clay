build:
	docker build -t clay .

run: | build
	docker run -it clay

.PHONY: docs
docs:
	make -C docs html

