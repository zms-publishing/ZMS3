# Running Py2-Zope/ZMS Apps on a Current Operating System

> _The text describes the subsequent operation of a Python2-based ZMS environment from an old OS with a previous Python2 package installation in a modern OS, where Python2 is no longer available or cannot be made available by self-compilation: the Python2 code can no longer integrate the current OpenSSL 3+ lib, among other things, and breaks accordingly when trying to compile. In addition, the parallel operation of two (incompatible) Python generations is prone to errors. If a Python 3 migration is not practicable, it is possible to continue operation in a Docker container with the old operating system.

Hint: It should be noted that the LTS support for Python2 expired in 2020 and its use should be limited to a protected intranet environment._

## Data Organization

The Zope/ZMS installation is usually carried out in a virtual Python environment (venv). The following data organization is suggested for container operation. The `venv` folders are those of the virtual Python environment, while the Zope instance is stored in the `/home/zope` folder:

```txt
/home/zope
  /bin
    start_instance.sh
    start_zeo.sh
  /etc
    site.zcml
    zeo.conf
    zope.conf.tmpl
  /customizing
    overrides.zcml
  /Extensions
  /import
  /Products
  /var
    /log
    /mediafolder
    Data.fs
    zeosocket
  /venv
    /bin
    /etc
    /inlude
    /lib
    /share
    /src

```

In practice, however, a real world system can be located elsewhere in the file tree. The relevant paths for starting a Zope instance are basically only two, namely:

1. the path to the Python binary used (usually the virtual Python environment) and
2. the path to the Zope instance with its productive data


## In-place dockerization

The “in-place dockerization” approach now consists of providing only the Python2 runtime environment via a Docker image and making the entire database (as it is, “in-place”) accessible to the running container as a mount-bind. This means that the Py2-Zope app server running in the container accesses the host file system _from the container_ or publishes “upstream” from the container to the web server (e.g. nginx) via the port defined in container-zope.conf. This in turn can run in its own container or on the host server.

To create the Docker constructs, the following configuration files are utilized: 

1. **Image**: [Dockerfile](https://github.com/zms-publishing/ZMS3/blob/main/docker/variants/ubuntu/Dockerfile)
2. **Container**: [docker-compose](https://github.com/zms-publishing/ZMS3/blob/main/docker/variants/ubuntu/docker-compose.yml)


## Docker-Image using Ubuntu 20.04

The Docker image is based on Ubuntu 20.04 which still allows the additional installation of Python2. Zope 2.13.29 and ZMS3 are installed from github and any Python modules that may need to be extended for specific projects from pypi. For the sake of traceability, the virtual Python in the container will be installed in the path hierarchy `/home/zope/venv/`. The [Dockerfile](https://github.com/zms-publishing/ZMS3/blob/main/docker/variants/ubuntu/Dockerfile) starts with a section for arguments (usually given by an [.env-file](https://github.com/zms-publishing/ZMS3/blob/main/docker/variants/ubuntu/.env)), then installing the Libraries that are needed for compiling Python-Libraries and the ZMS/Zope-installation. 

## Environment-Variabes are set by .env-File

```yml
# User and group IDs
UID=1000
GID=1000

# Zope/ZMS paths
HOME_DIR=/home/zope
VENV_DIR=${HOME_DIR}/venv

INSTANCE_DIR=${HOME_DIR}
INSTANCE_MOUNT=${HOME_DIR}/instance/zms3_dev

SRC_DIR=${VENV_DIR}/src
SRC_MOUNT=${INSTANCE_MOUNT}/src
```

## Run Zope/ZMS in the Docker Container

Only one Zope instance now runs in a container - monotonously on port 8080. The always identical container-internal port will be mapped/externalized to a unified port such as 8085, 8086, 8087 etc; this is accomplished by environment variables at Zope startup. Since `zope.conf` unfortunately cannot accept variables directly, the complete `zope.conf` file will be  generated dynamically by the shell script that starts the Zope instance. The crucial variables are:

1. HTTP_PORT 
2. READ_ONLY

These environment variables are defined by the docker-compose file and processed by the shell-script that starts the Zope instance: `start_instance.sh` (docker/variants/ubuntu/start_instance.sh)

```yml
x-instance-common: &instance_common
  image: zms3:base
  build:
    context: .
    dockerfile: ./Dockerfile
    args:
      - INSTANCE_DIR=${INSTANCE_DIR}
      - VENV_DIR=${VENV_DIR}
      - IS_DEBUG=false
      - UID=${UID}
      - GID=${GID}
  depends_on:
    - zeo
  user: zope
  volumes:
    - .:${INSTANCE_DIR}/:rw
    - ${SRC_MOUNT}/:${SRC_DIR}/:rw
  command: >
    bash -c "
      memcached -u zope -m 64 -p 11211 &
      ${INSTANCE_DIR}/bin/start_instance.sh &&
      sleep infinity
    "
  networks:
    - zms_network

networks:
  zms_network:
    driver: bridge

services:
  ### Zope: Zope Application Server
  instance1:
    <<: *instance_common
    environment:
      - INSTANCE_DIR=${INSTANCE_DIR}
      - INSTANCE_MOUNT=${INSTANCE_MOUNT}
      - VENV_DIR=${VENV_DIR}
      - IS_DEBUG=true
      - UID=${UID}
      - GID=${GID}
    ports:
      - "8085:8080"

  instance2:
    <<: *instance_common
    environment:
      - INSTANCE_DIR=${INSTANCE_DIR}
      - INSTANCE_MOUNT=${INSTANCE_MOUNT}
      - VENV_DIR=${VENV_DIR}
      - IS_DEBUG=false
      - UID=${UID}
      - GID=${GID}
    ports:
      - "8086:8080"

  instance3:
    <<: *instance_common
    environment:
      - INSTANCE_DIR=${INSTANCE_DIR}
      - INSTANCE_MOUNT=${INSTANCE_MOUNT}
      - VENV_DIR=${VENV_DIR}
      - IS_DEBUG=false
      - UID=${UID}
      - GID=${GID}
    ports:
      - "8087:8080"

  ### ZEO: Zope Enterprise Objects
  zeo:
    <<: *instance_common
    depends_on: []
    command: >
      bash -c "
      ${INSTANCE_DIR}/bin/start_zeo.sh &
      sleep infinity
      "
```

Instead of creating a separate docker-composefile for each Zope instance, the sequence with its specific variables is called for each container on the basis of a template `&instance_common` in order to create the respective container.
So, the number of Zope instances is set in the Docker Compose file by duplicating a minimalist description for the Zope instance (i.e. not via a port number iteration in the start script as before. The Zope start script now starts a single instance per container and, in addition to starting Zope, has the new task of automatically generating a suitable `zope.conf` beforehand so that it can then be called). 
By copying and adapting the following block, you can create new Zope instances in the docker-compose file:

```yml
  zmsclient1:
    <<: *instance_common
    environment:
      - PYTHONUNBUFFERED="1"
      - SOFTWARE_HOME="${VENV_DIR}/bin"
      - PYTHON="${VENV_DIR}bin/python"
      - HTTP_PORT=8087
      - READ_ONLY=false
    ports:
      - "8087:8080"
```


## Container-Consistent Zope Configuration 

As the conf files used by the container originate from the host FS, they must correspond to the path situation *within* the container. As only one single Zope instance runs in each container under the same path `/home/zope/` using the virtual Python from `/home/zope/venv`, the runzope file is always the same.
These pathes are applied to the runzeo-script as well.

### $INSTANCE/bin/runzope

```sh
#! /bin/sh
INSTANCE_HOME="/home/zope"
CONFIG_FILE="/home/zope/etc/zope.conf"
ZOPE_RUN="/home/zope/venv/bin/runzope"
export INSTANCE_HOME
exec "$ZOPE_RUN" -C "$CONFIG_FILE" "$@"
```

### $INSTANCE/bin/runzeo

```sh
#! /bin/sh
#!/bin/sh
# ZEO instance start script
INSTANCE_HOME="/home/zope"
PYTHON="/home/zope/venv/bin/python"
ZODB3_HOME="/home/zope/venv/lib/python2.7/site-packages"
CONFIG_FILE="$INSTANCE_HOME/etc/zeo.conf"
PYTHONPATH="$ZODB3_HOME"
export PYTHONPATH INSTANCE_HOME
exec "$PYTHON" -m ZEO.runzeo -C "$CONFIG_FILE" ${1+"$@"}
```

### Template based Creation of $INSTANCE/etc/zope.conf

To create an instance-specific `zope.conf` file, a text template is used, which is specified using the Linux command envsubst with the values of two variables:

1. READ_ONLY: Set to true to start Zope in read-only mode.
2. HTTP_PORT: The container port on which the Zope port is mapped to.

The template shown below is processed using the following shell script call (docker/variants/ubuntu/start_instance.sh)

```sh
envsubst '$HTTP_PORT $READ_ONLY' < "${INSTANCE_DIR}/etc/zope.conf.tmpl" > "${INSTANCE_DIR}/etc/zope_$HTTP_PORT.conf"
```

The Zope path variables are fixed within the [zope.conf template](https://github.com/zms-publishing/ZMS3/blob/main/docker/variants/ubuntu/instance/etc/zope.conf.tmpl) because only a single Zope instance runs under `/home/zope` within a container:

```xml

# Environment variable substitution:
# Created at $CONF_TS
# - READ_ONLY: Set to true to start Zope in read-only mode.
# - HTTP_PORT: The container port on which the Zope port is mapped to.
%define READ_ONLY $READ_ONLY
%define HTTP_PORT $HTTP_PORT


# Zope configuration variables
%define INSTANCE_HOME /home/zope
%define VIRTUAL_ENV /home/zope/venv
%import ZEO

instancehome $INSTANCE_HOME
# ip-address 0.0.0.0

# debug-mode on

<http-server>
	# In the container Zope is running on default port 8080
	address 8080
</http-server>

<zodb_db main>
	mount-point /
	cache-size 5000
	<zeoclient>
		# server localhost:9999
		server $INSTANCE_HOME/var/zeosocket
		storage 1
		name zeostorage
		var $INSTANCE_HOME/var
		cache-size 20MB
		client $INSTANCE_HOME/var/zms_zeo_$HTTP_PORT
		read-only $READ_ONLY
	</zeoclient>
</zodb_db>

<zodb_db temporary>
	# Temporary storage database (for sessions)
	<temporarystorage>
		name temporary storage for sessioning
	</temporarystorage>
	mount-point /temp_folder
	container-class Products.TemporaryFolder.TemporaryContainer
</zodb_db>

<eventlog>
  level info
  <logfile>
    path $INSTANCE_HOME/var/log/event_$HTTP_PORT.log
    level info
  </logfile>
</eventlog>

<logger access>
  level WARN
  <logfile>
    path $INSTANCE_HOME/var/log/Z2_$HTTP_PORT.log
    format %(message)s
  </logfile>
</logger>

```

## Coordinated start process

In the _docker-compose_ file any service section (derived from the _instance_common_-template)  will call the [_start_instance_-script](https://github.com/zms-publishing/ZMS3/blob/main/docker/variants/ubuntu/instance/bin/start_instance.sh):

```sh
${SRC_DIR}/docker/variants/ubuntu/instance/bin/start_instance.sh
```

The script contains some waiting-loops to make sure for any Zope-instance that ZEO has started and the ZODB-connection is available and a report about the starting process is sent to the console:

```sh
zope@dev: ~/src/zms/docker/variants/ubuntu$ docker compose -f docker-compose.yml up

✔ Image zms3:base
✔ Network devcontainer_zms_network
✔ Container devcontainer-zeo-1
✔ Container devcontainer-instance1-1 
✔ Container devcontainer-instance2-1
✔ Container devcontainer-instance3-1 
Attaching to instance1-1, instance2-1, instance3-1, zeo-1
zeo-1  | Starting ZEO server...
zeo-1  | ZEO-starting script is waiting for ZEO server to start...
instance2-1  | HTTP_PORT is set to 8086
instance2-1  | READ_ONLY is set to false
instance2-1  | Waiting for ZEO server to start listening on socket...
instance2-1  | Waiting for ZEO server to start... (0 seconds)
instance1-1  | HTTP_PORT is set to 8085
instance1-1  | READ_ONLY is set to true
instance1-1  | Waiting for ZEO server to start listening on socket...
instance1-1  | Waiting for ZEO server to start... (0 seconds)
instance3-1  | HTTP_PORT is set to 8087
instance3-1  | READ_ONLY is set to false
instance3-1  | Waiting for ZEO server to start listening on socket...
instance3-1  | Waiting for ZEO server to start... (0 seconds)
zeo-1        | ZEO server has started on /home/zope/instance/var/zeosocket
instance2-1  | ZEO server is now listening on socket
instance2-1  | Starting Zope instance ...
instance2-1  | Waiting for Zope to start ...
instance1-1  | ZEO server is now listening on socket
instance1-1  | Starting Zope instance ...
instance1-1  | Waiting for Zope to start ...
instance3-1  | ZEO server is now listening on socket
instance3-1  | Starting Zope instance ...
instance3-1  | Waiting for Zope to start ...
instance2-1  | Zope started on port 8080 and publishing on 8086
instance1-1  | Zope started on port 8080 and publishing on 8085
instance3-1  | Zope started on port 8080 and publishing on 8087
```

The debug-Container (having VSCode-Server) starts only ZEO and not Zope. This will be done manually with the VSCode-Python-Debugger:

```sh
zope@dev: ~/src/zms/docker/variants/ubuntu$ docker compose -f docker-compose.yml up
```

The VSCode-GUI will appear in the web-browser on port 8888 and the launch-name for debugging will be "Docker: ZMS3-Py2".After launching Zope will be published on port 8080.


## Potential issues

1. file permissions on the mounted folders do not match the container user
2. the hostsystem-user (for creating the container) is not part of the docker group
3. the hostsystem-user is defined by a remote system (e.g. afs) that does not allow writing the .docker-config-folder into the the user's home-folder 

