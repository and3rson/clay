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

# paplay --server=172.17.0.1 LRMonoPhase4.wav
# --privileged \

.PHONY: docs
docs:
	make -C docs html

