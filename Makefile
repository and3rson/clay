build:
	docker build -t clay .

run: | build
	docker run -it clay

