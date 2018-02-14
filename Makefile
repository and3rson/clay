CMD ?= "./clay/app.py"

build:
	echo $(shell id -u)
	docker build -t clay --build-arg HOST_USER=${USER} --build-arg HOST_UID=$(shell id -u) .

run: | build
	docker run -it \
	--rm \
	--name clay \
	-v ${HOME}/.config/clay:/home/${USER}/.config/clay \
	-v /dev/shm:/dev/shm \
	-v /etc/machine-id:/etc/machine-id \
	-v /run/user/${UID}/pulse:/run/user/${UID}/pulse \
	-v /var/lib/dbus:/var/lib/dbus \
	-v ${HOME}/.pulse:/home/${USER}/.pulse \
	-v ${HOME}/.config/pulse:/home/${USER}/.config/pulse \
	--tty \
	-u ${USER} \
	clay \
	${CMD}

.PHONY: docs
docs:
	make -C docs html

check:
	pylint clay --ignore-imports=y
	radon cc -a -s -nB -e clay/vlc.py clay
