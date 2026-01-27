# Running Py2-Zope/ZMS Apps on a Current Operating System

> _The text describes the subsequent operation of a Python2-based ZMS environment from an old OS with a previous Python2 package installation in a modern OS, where Python2 is no longer available or cannot be made available by self-compilation: the Python2 code can no longer integrate the current OpenSSL 3+ lib, among other things, and breaks accordingly when trying to compile. In addition, the parallel operation of two (incompatible) Python generations is prone to errors. If a Python 3 migration is not practicable, it is possible to continue operation in a Docker container with the old operating system.

Hint: It should be noted that the LTS support for Python2 expired in 2020 and its use should be limited to a protected intranet environment._

## Data Organization in Folders ./venv and ./instance

The Zope/ZMS installation is usually carried out in a virtual Python environment (venv). The following data organization is suggested for container operation. The `venv` folders are those of the virtual Python environment, while the Zope instance is stored in the `instance` folder:

```txt
/home/zope/venv
  /bin
  /etc
  /inlude
  /lib
  /share
  /src

/home/zope/instance
  /bin
  /etc
  /Extensions
  /import
  /log
  /Products
  /var
```

In practice, however, a real world system can be located elsewhere in the file tree. The relevant paths for starting a Zope instance are basically only two, namely:

1. the path to the Python binary used (usually the virtual Python environment) and
2. the path to the Zope instance with its productive data


## In-place dockerization

The “in-place dockerization” approach now consists of providing only the Python2 runtime environment via a Docker image and making the entire database (as it is, “in-place”) accessible to the running container as a mount-bind. This means that the Py2-Zope app server running in the container accesses the host file system _from the container_ or publishes “upstream” from the container to the web server (e.g. nginx) via the port defined in container-zope.conf. This in turn can run in its own container or on the host server.

To create the Docker constructs, the following configuration files are required; these are placed in the folder in which the Zope instances are located: 

1. **Image**, e.g.: `/home/zope/venv/instances/Dockerfile`
2. **Container**, e.g: `/home/zope/venv/instances/docker-compose`


## Docker-Image using Ubuntu 20.04

The Docker image is based on Ubuntu 20.04 which still allows the additional installation of Python2. Zope 2.13.29 and ZMS3 are installed from github and any Python modules that may need to be extended for specific projects from pypi. For the sake of traceability, the virtual Python in the container will be installed in the path hierarchy `/home/zope/venv/`. The [Dockerfile](https://github.com/zms-publishing/ZMS3/blob/main/docker/variants/ubuntu/Dockerfile) starts with a section for arguments (usually given by an [.env-file](https://github.com/zms-publishing/ZMS3/blob/main/docker/variants/ubuntu/.env)), then installing the Libraries that are needed for compiling Python-Libraries and the ZMS/Zope-installation, in short: 


```yml
FROM ubuntu:20.04

# Image name: zms3:base
LABEL org.opencontainers.image.title="zms3:base"

# ############################
ARG INSTANCE_DIR=$(INSTANCE_DIR;default:/home/zope/instance)
ARG VENV_DIR=$(INSTANCE_DIR;default:/home/zope/venv)
ARG IS_DEBUG=$(IS_DEBUG;default:false)
ARG UID=$(UID;default:1000)
ARG GID=$(GID;default:1000)
# ############################

RUN apt-get update

RUN apt-get install -y ca-certificates
# COPY zerts-pem/* /usr/local/share/ca-certificates/
RUN update-ca-certificates
RUN apt-get -y upgrade

RUN apt-get install -y bash
RUN apt-get install -y wget
RUN apt-get install -y curl
RUN apt-get install -y --no-install-recommends gettext-base 
RUN apt-get install -y lsof netcat inetutils-ping nano
RUN apt-get install -y build-essential
RUN apt-get install -y git
RUN apt-get install -y python2 python2-dev
# Install pip for Python 2 (pip 20.3) since Ubuntu 20.04 does not ship python2-pip
RUN curl -sS https://bootstrap.pypa.io/pip/2.7/get-pip.py -o /tmp/get-pip.py && \
	python2 /tmp/get-pip.py pip==20.3 && \
	rm /tmp/get-pip.py
# Install virtualenv for creating Python2 virtual environments
RUN python2 -m pip install virtualenv
RUN apt-get install -y libsasl2-dev
RUN apt-get install -y libldap2-dev
RUN apt-get install -y libssl-dev
RUN apt-get install -y libsqlite3-dev


# Set host's UID/GID to allow sharing of production files as bind mounts
RUN groupadd --gid $GID zope
RUN adduser --disabled-password --uid $UID --gid $GID zope

USER zope
# Create Zope Instance
ENV INSTANCE_DIR=${INSTANCE_DIR}
ENV VIRTUAL_ENV=${VENV_DIR}
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN virtualenv --python=python2 $VIRTUAL_ENV
WORKDIR $VIRTUAL_ENV/bin
RUN bash -c "source activate"

RUN ./pip install -r https://raw.githubusercontent.com/zms-publishing/zms3/master/requirements.txt
RUN ./pip install git+https://github.com/zms-publishing/ZMS3.git#egg=ZMS
RUN ./pip install Products.PluginRegistry==1.4
RUN ./pip install Products.LDAPUserFolder==2.27
RUN ./pip install Products.PluggableAuthService==1.11.0
RUN ./pip install Products.LDAPMultiPlugins==1.14
RUN ./pip install Products.ZSQLMethods==2.13.4
RUN ./pip install Products.ZSQLiteDA==0.6.1
RUN ./pip install mysqlclient==1.4.6
RUN ./pip install --no-deps Products.ZMySQLDA==4.11
RUN ./pip install Products.SQLAlchemyDA
RUN ./pip install --no-deps Products.mcdutils==2.0
RUN ./pip install SQLAlchemy
RUN ./pip install Pillow

# Create Zope Instance
RUN ./mkzopeinstance --dir ${INSTANCE_DIR} --user admin:admin
```

This example code actually just shows the most important installation steps. Our [Dockerfile](https://github.com/zms-publishing/ZMS3/blob/main/docker/variants/ubuntu/Dockerfile) will install some components (memcache, VSCode-Server, MariaDB etc.) 
This container image forms the basis for the containers that perform the mount-binding to the host file system and start the application.

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
    - ./instance/:${INSTANCE_DIR}/:rw
    - ${SRC_MOUNT}/:${SRC_DIR}/:rw
  command: >
    bash -c "
      memcached -u zope -m 64 -p 11211 &
      ${SRC_DIR}/docker/variants/ubuntu/start_instance.sh &&
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
      - PYTHONUNBUFFERED="1"
      - SOFTWARE_HOME="${VENV_DIR}/bin"
      - PYTHON="${VENV_DIR}bin/python"
      - HTTP_PORT=8085
      - READ_ONLY=true
    ports:
      - "8085:8080"

  instance2:
    <<: *instance_common
    environment:
      - PYTHONUNBUFFERED="1"
      - SOFTWARE_HOME="${VENV_DIR}/bin"
      - PYTHON="${VENV_DIR}bin/python"
      - HTTP_PORT=8086
      - READ_ONLY=false
    ports:
      - "8086:8080"

  instance3:
    <<: *instance_common
    environment:
      - PYTHONUNBUFFERED="1"
      - SOFTWARE_HOME="${VENV_DIR}/bin"
      - PYTHON="${VENV_DIR}bin/python"
      - HTTP_PORT=8087
      - READ_ONLY=false
    ports:
      - "8087:8080"

  ### ZEO: Zope Enterprise Objects
  zeo:
    <<: *instance_common
    depends_on: []
    command: >
      bash -c "
      ${SRC_DIR}/docker/variants/ubuntu/start_zeo.sh &
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
      - HTTP_PORT=8085
      - READ_ONLY=true
    ports:
      - "8085:8080"
```


## Container-Consistent Zope Configuration 

As the conf files used by the container originate from the host FS, they must correspond to the path situation *within* the container. As only one single Zope instance runs in each container under the same path `/home/zope/instance` using the virtual Python from `/home/zope/venv`, the runzope file is always the same.
These pathes are applied to the runzeo-script as well.

### $INSTANCE/bin/runzope

```sh
#! /bin/sh
INSTANCE_HOME="/home/zope/instance"
CONFIG_FILE="/home/zope/instance/etc/zope.conf"
ZOPE_RUN="/home/zope/venv/bin/runzope"
export INSTANCE_HOME
exec "$ZOPE_RUN" -C "$CONFIG_FILE" "$@"
```

### $INSTANCE/bin/runzeo

```sh
#! /bin/sh
#!/bin/sh
# ZEO instance start script
INSTANCE_HOME="/home/zope/instance"
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

The Zope path variables are fixed within the zope.conf template because only a single Zope instance runs under `/home/zope/instance` within a container:

```xml
# Template fpr zope.conf
%define READ_ONLY $READ_ONLY
%define HTTP_PORT $HTTP_PORT

# Zope configuration variables
%define INSTANCE_HOME /home/zope/instance
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
		path $INSTANCE_HOME/log/event_$HTTP_PORT.log
		level info
	</logfile>
</eventlog>

<logger access>
	level WARN
	<logfile>
		path $INSTANCE_HOME/log/Z2_$HTTP_PORT.log
		format %(message)s
	</logfile>
</logger>
```

## Coordinated start process

In the _docker-compose_ file any service section (derived from the _instance_common_-template)  will call the [_start_instance_-script](https://github.com/zms-publishing/ZMS3/blob/main/docker/variants/ubuntu/start_instance.sh):

```sh
${SRC_DIR}/docker/variants/ubuntu/start_instance.sh
```

The script contains some waiting-loops to make sure for any Zope-instance that ZEO has started and the ZODB-connection is available and a report about the starting process is sent to the console:

```sh
zope@dev: ~/src/ZMS3/docker/variants/ubuntu$ docker compose -f docker-compose.yml up

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
zope@dev: ~/src/ZMS3/docker/variants/ubuntu$ docker compose -f docker-compose.yml up
```

The VSCode-GUI will appear in the web-browser on port 8888 and the launch-name for debugging will be "Docker: ZMS3-Py2".After launching Zope will be published on port 8080.


## Potential issues

1. file permissions on the mounted folders do not match the container user
2. the hostsystem-user (for creating the container) is not part of the docker group
3. the hostsystem-user is defined by a remote system (e.g. afs) that does not allow writing the .docker-config-folder into the the user's home-folder 

