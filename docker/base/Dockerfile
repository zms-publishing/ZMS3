FROM ubuntu:20.04
ARG BUILD_PYTHON_VERSION=2.7

ENV DEBIAN_FRONTEND=noninteractive TZ=Europe/Berlin
RUN \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    <<EOR
    set -xe

    # Ensure all system packages are up to date
    apt-get update
    apt-get --yes upgrade

    # Preconfigure timezone non-interactively
    echo "tzdata tzdata/Areas select Europe" | debconf-set-selections && \
    echo "tzdata tzdata/Zones/Europe select Berlin" | debconf-set-selections && \
    apt-get install --yes --no-install-recommends tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

    # Install dependencies
    apt-get install --yes ca-certificates
    update-ca-certificates

    apt-get install --yes bash git curl lsof netcat inetutils-ping nano iproute2
    apt-get install --yes --no-install-recommends gettext-base
    apt-get install --yes build-essential
    apt-get install --yes python2 python2-dev
    # Install pip for Python 2 (pip 20.3) since Ubuntu 20.04 does not ship python2-pip
    curl -sS https://bootstrap.pypa.io/pip/2.7/get-pip.py -o /tmp/get-pip.py && \
        python2 /tmp/get-pip.py pip==20.3 && \
        rm /tmp/get-pip.py
    # Install virtualenv for creating Python2 virtual environments
    python2 -m pip install virtualenv
    apt-get install --yes libsasl2-dev libldap2-dev libssl-dev libsqlite3-dev
    apt-get install --yes memcached libmemcached-tools
    apt-get install --yes mariadb-client default-libmysqlclient-dev
    apt-get install --yes slapd ldap-utils
    apt-get install --yes libnss3 libxss1 libasound2 libatk1.0-0 libgtk-3-0 libx11-xcb1 libxcb1
EOR

# Set host's UID/GID to allow sharing of production files as bind mounts
ARG UID=1000
ARG GID=1000
RUN <<EOR
    groupadd --gid $GID zope
    adduser --disabled-password --system --uid $UID --gid $GID zope
EOR
USER zope
WORKDIR /home/zope/

# Configure git for user
RUN <<EOR
    git config --global user.email "zmsbot@container"
    git config --global user.name "zmsbot"
EOR

# Provide ZEO health check script
COPY --chown=zope:zope docker/base/zeo_health_check.py /home/zope/bin/zeo_health_check.py

ARG INSTANCE_DIR=/home/zope/
ENV VIRTUAL_ENV=/home/zope/venv

# Create Zope Instance
ENV INSTANCE_DIR=${INSTANCE_DIR}
RUN <<EOR
    virtualenv --python=python2 $VIRTUAL_ENV
    ln -s ${VIRTUAL_ENV}/lib/python$BUILD_PYTHON_VERSION/site-packages/ ${VIRTUAL_ENV}/site-packages
EOR
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Local builds greatly accelerate, if we do not need to download all pip packages from scratch every time
ENV PIP_CACHE_DIR=/home/zope/venv/cache
ARG PIP_INSTALL="pip install --cache-dir $PIP_CACHE_DIR"

COPY --chown=zope:zope version.txt src/version.txt
COPY --chown=zope:zope requirements*.txt setup.py README.rst src/
RUN --mount=type=cache,uid=$UID,target=$PIP_CACHE_DIR,sharing=locked <<EOR
    $PIP_INSTALL --upgrade pip wheel setuptools
    $PIP_INSTALL --requirements requirements.txt
    $PIP_INSTALL --requirement src/requirements-pluggableauth.txt
    $PIP_INSTALL --requirements requirements-extra.txt
    $PIP_INSTALL ./src/
EOR

# Copy in and install zms last, to maximize layer caching
# Needs to happen before instance initialization as the instance cannot be loaded
# otherwise to generate the initial user
# Not quite sure why the source needs to land in `src/Products/zms` - the setup.py
# file declares it to be in src. But this works…
COPY --chown=zope:zope . src/Products/zms
RUN --mount=type=cache,uid=$UID,target=$PIP_CACHE_DIR,sharing=locked <<EOR
    $PIP_INSTALL --editable ./src/[dev]
EOR

# Create Zope Instance
# We do this, to make it easy to evaluate zms without having to create an initial zodb
# outside the container and map it inside.
# However: mkzopeinstance creates a file inituser in the top level of the deployment
# This file is read on the first startup of zope, and creates the actual initial user
# in the zodb consuming that file. Therefore we must be very cautious to ensuret that
# this file itself is _not_ part of the docker image. zconsole triggers that same
# startup behaviour.
RUN <<EOR
    set -ex
    mkdir cache Extensions Products customizing import
    mkzopeinstance --dir ${INSTANCE_DIR} --user admin:admin
    # consume inituser file
    echo | zopectl --configure etc/zope.conf debug
EOR

# TODO Copy in base configuration files
ARG BUILD_DIR=docker/base
COPY --chown=zope:zope $BUILD_DIR/zope.conf etc/zope.conf
COPY --chown=zope:zope $BUILD_DIR/zeo.conf etc/zeo.conf

EXPOSE 80

# Finally Start Zope by Script
# ENTRYPOINT ["/bin/sh -c"]
# ENTRYPOINT ["bash", "-c", "sleep infinity"]
# CMD ["$INSTANCE_HOME/bin/zopectl","fg"]
# CMD ["$INSTANCE_HOME/bin/runzope","-X","debug-mode=on"]

CMD ["bin/runzope", "-X", "debug-mode=on"]
