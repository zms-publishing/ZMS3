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

The Docker image is based on Ubuntu 20.04 which still allows the additional installation of Python2. Zope 2.13.29 and ZMS3 are installed from github and any Python modules that may need to be extended for specific projects from pypi. For the sake of traceability, the virtual Python in the container will be installed in the path hierarchy `/home/zope/venv/`:


```yml
FROM ubuntu:20.04

# Image name: zms3:base
LABEL org.opencontainers.image.title="zms3:base"

# Get environment variables from docker-compose.yml:
# So, image file must be created with docker-compose build
# ############################
ARG INSTANCE_DIR=$(INSTANCE_DIR;default:/home/zope/instance)
ARG VENV_DIR=$(INSTANCE_DIR;default:/home/zope/venv)
ARG IS_DEBUG=$(IS_DEBUG;default:false)
ARG UID=$(UID;default:1000)
ARG GID=$(GID;default:1000)
# ############################

# Non-interactive installs and default timezone to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive TZ=Europe/Berlin

# Preconfigure timezone non-interactively
RUN apt-get update && \
	echo "tzdata tzdata/Areas select Europe" | debconf-set-selections && \
	echo "tzdata tzdata/Zones/Europe select Berlin" | debconf-set-selections && \
	apt-get install -y --no-install-recommends tzdata && \
	ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
	dpkg-reconfigure -f noninteractive tzdata && \
	rm -rf /var/lib/apt/lists/*
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

# Install memcached
RUN apt-get update && \
	apt-get install -y memcached libmemcached-tools && \
	rm -rf /var/lib/apt/lists/*

# Install only MariaDB client libs
RUN apt-get update && \
	apt-get install -y mariadb-client default-libmysqlclient-dev && \
	rm -rf /var/lib/apt/lists/*

# Install slapd and ldap-utils without prompting for password
RUN echo "slapd slapd/internal/generated_adminpw password password" | debconf-set-selections && \
	echo "slapd slapd/internal/adminpw password password" | debconf-set-selections && \
	echo "slapd slapd/password2 password password" | debconf-set-selections && \
	echo "slapd slapd/password1 password password" | debconf-set-selections && \
	echo "slapd slapd/dump_database_destdir string /var/backups/slapd-VERSION" | debconf-set-selections && \
	echo "slapd slapd/domain string example.com" | debconf-set-selections && \
	echo "slapd shared/organization string Example Inc." | debconf-set-selections && \
	apt-get update && \
	apt-get install -y slapd ldap-utils && \
	rm -rf /var/lib/apt/lists/*

# ------------------------------
# Add Packages needed for VSCode
RUN apt-get update && apt-get install -y apt-transport-https ca-certificates gnupg curl && \
	curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg && \
	echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/vscode stable main" > /etc/apt/sources.list.d/vscode.list && \
	rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
	apt-get install -y libnss3 libxss1 libasound2 libatk1.0-0 libgtk-3-0 libx11-xcb1 libxcb1 && \
	rm -rf /var/lib/apt/lists/*
# ------------------------------

# Set host's UID/GID to allow sharing of production files as bind mounts
RUN groupadd --gid $GID zope
RUN adduser --disabled-password --uid $UID --gid $GID zope

# Grant zope passwordless sudo for development purposes if IS_DEBUG is set to true
RUN if [ "$IS_DEBUG" = "true" ]; then \
	echo "Debug mode is ON. Granting zope passwordless sudo." && \
	apt-get update && \
	apt-get install -y sudo && \
	echo 'zope ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
	adduser zope sudo; \
else \
	echo "Debug mode is OFF. Not granting zope passwordless sudo."; \
fi

# ----------------------------
# MariaDB service is provided in dockerfile-compose.mysql.yml
# ------------------------------
# # Prepare MySQL runtime & data dirs and give them to zope
# RUN mkdir -p /var/run/mysqld /var/lib/mysql \
#	&& chown -R zope:zope /var/run/mysqld /var/lib/mysql

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
# RUN ./pip install MySQL-python==1.2.5 # Not working with Python 2.7.18 on Ubuntu 20.04
RUN ./pip install mysqlclient==1.4.6
RUN ./pip install --no-deps Products.ZMySQLDA==4.11
RUN ./pip install Products.SQLAlchemyDA
RUN ./pip install --no-deps Products.mcdutils==2.0
RUN ./pip install SQLAlchemy
RUN ./pip install Pillow
RUN ./pip install feedparser
RUN ./pip install python-memcached==1.59
RUN ./pip install xhtml2pdf==0.2.4
RUN ./pip install requests beautifulsoup4 lxml Markdown pyScss python-docx

# Create Zope Instance
RUN ./mkzopeinstance --dir ${INSTANCE_DIR} --user admin:admin
```

This container image forms the basis for the containers that perform the mount-binding to the host file system and start the application.

## Run Zope/ZMS in the Docker Container

Only one Zope instance now runs in a container - monotonously on port 8080. The always identical container-internal port will be mapped/externalized to a unified port such as 8085, 8086, 8087 etc; this is accomplished by environment variables at Zope startup. Since zope.conf unfortunately cannot accept variables directly, the complete zope.conf file will be  generated dynamically by the shell script that starts the Zope instance. The crucial variables are:

1. HTTP_PORT 
2. READ_ONLY

These environment variables are defined by the docker-compose file and processed by the shell-script that starts the Zope instance: `start_instance.sh` (.devcontainer/start_instance.sh)

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
    - ./instance/bin/:${INSTANCE_DIR}/bin/:rw
    - ./instance/etc/:${INSTANCE_DIR}/etc/:rw
    - ${INSTANCE_MOUNT}/:${INSTANCE_DIR}/:rw
    - ${CUSTOM_MOUNT}/:${CUSTOM_DIR}/:rw
    - ${SRC_MOUNT}/:${SRC_DIR}/:rw
    - ${HOME_DIR}/.vscode-server-py2:${HOME_DIR}/.vscode-server:rw
    - /afs:/afs
  command: >
    bash -c "
      memcached -u zope -m 64 -p 11211 &
      ${CUSTOM_DIR}/.devcontainer/start_instance.sh &&
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
      ${CUSTOM_DIR}/.devcontainer/start_zeo.sh &
      sleep infinity
      "

### MariaDB service is provided in dockerfile-compose.mysql.yml
```
Instead of creating a separate docker-composefile for each Zope instance, the sequence with its specific variables is called for each container on the basis of a template `&instance_common` in order to create the respective container.
So, the number of Zope instances is set in the Docker Compose file by duplicating a minimalist description for the Zope instance (i.e. not via a port number iteration in the start script as before. The Zope start script now starts a single instance per container and, in addition to starting Zope, has the new task of automatically generating a suitable zope.conf beforehand so that it can then be called). 
By copying and adapting the following block, you can create new Zope instances in the docker-compose file:

```yml
  zmsclient1:
    <<: *zmsclient_common
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

To create an instance-specific zope.conf file, a text template is used, which is specified using the Linux command envsubst with the values of two variables:

1. READ_ONLY: Set to true to start Zope in read-only mode.
2. HTTP_PORT: The container port on which the Zope port is mapped to.

The template shown below is processed using the following shell script call (.devcontainer/start_instance.sh)

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
