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
RUN apt-get install -y lsof netcat inetutils-ping nano iproute2
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
RUN ./pip install -r https://raw.githubusercontent.com/zms-publishing/zms3/master/requirements-extra.txt

# # Create Zope Instance
# RUN ./mkzopeinstance --dir ${INSTANCE_DIR} --user admin:admin
# COPY ./var ${INSTANCE_DIR}/var

# EXPOSE 3306
# EXPOSE 8080
# EXPOSE 8085
# EXPOSE 8086
# EXPOSE 8087

# Finally Start Zope by Script
# ENTRYPOINT ["/bin/sh -c"]
# ENTRYPOINT ["bash", "-c", "sleep infinity"]
# CMD ["$INSTANCE_HOME/bin/zopectl","fg"]
# CMD ["$INSTANCE_HOME/bin/runzope","-X","debug-mode=on"]cd
