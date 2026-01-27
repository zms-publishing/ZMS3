FROM centos:7

EXPOSE 80

ARG CI_COMMIT_SHA=development
ENV CI_COMMIT_SHA=$CI_COMMIT_SHA

# Ensure all system packages are up to date
ENV DEBIAN_FRONTEND=noninteractive

# Install Zope/ZEO Dependencies
RUN \
    --mount=type=cache,target=/var/cache/yum,sharing=locked \
    <<EOR
    sed -i 's/^mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
    sed -ri 's|#\s?baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

    yum --assumeyes install libldap2-dev libsasl2-dev libffi-devel git python-virtualenv
    yum --assumeyes groupinstall 'Development Tools'
EOR

# Drop root privileges
# We need hardcoded uid/gid so we can later share the production files as bind mounts with the correct uid/gid
ENV UID=1000
ENV GID=1000
RUN groupadd --gid $GID zope ; useradd --system --create-home --uid $UID --gid $GID zope
USER zope
WORKDIR /home/zope/

# Configure git for user
RUN <<EOR
    git config --global user.email "zmsbot@container"
    git config --global user.name "zmsbot"
EOR


# Create venv and permanently enable it
ARG CREATE_VENV_COMMAND="virtualenv"
ENV VIRTUAL_ENV=/home/zope/venv
RUN <<EOR
    $CREATE_VENV_COMMAND $VIRTUAL_ENV
    # simplify access to site-packages
    ln -s ${VIRTUAL_ENV}/lib/python$BUILD_PYTHON_VERSION/site-packages/ ${VIRTUAL_ENV}/site-packages
EOR
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Local builds greatly accelerate, if we do not need to download all pip packages from scratch every time
ENV PIP_CACHE_DIR=/home/zope/venv/cache

# Enable caching of pip packages to speed up rebuild times
# uv also cannot install editable eggs from git repos, but I think we don't need that
# may need to switch back to pip if the pyproject.toml requirement kicks in
ARG PIP_INSTALL="pip install --cache-dir $PIP_CACHE_DIR"


# Only install dependenies now, to maximize layer caching
COPY --chown=zope:zope setup.py version.txt requirements*.txt ./src/
RUN --mount=type=cache,uid=$UID,target=$PIP_CACHE_DIR,sharing=locked <<EOR
    set -xe
    $PIP_INSTALL --upgrade pip wheel setuptools
    $PIP_INSTALL --requirement src/requirements.txt
    $PIP_INSTALL --requirement src/requirements-pluggableauth.txt
    $PIP_INSTALL src/
    $PIP_INSTALL --upgrade git+https://github.com/sntl-projects/Products.zmsPluggableAuthService.git#egg=Products.zmsPluggableAuthService[nginx-sso]
    # $PIP_INSTALL ZEO
EOR

# Create Zope Instance
# We do this, to make it easy to evaluate zms without having to create an initial zodb outside the container and map it inside.
# However: mkwsgiinstance creates a file inituser in the top level of the deployment
# This file is read on the first startup of zope, and creates the actual initial user in the zodb
# consuming that file. Therefore we must be very cautious to ensuret that this file itself is _not_
# part of the docker image. zconsole triggers that same startup behaviour.
RUN <<EOR
    set -ex
    mkdir cache Extensions Products customizing import
    mkwsgiinstance --dir . --user admin:admin
    echo | zconsole debug etc/zope.conf
EOR

# Configure Zope Instance
ARG BUILD_DIR=docker
COPY --chown=zope:zope $BUILD_DIR/zope.conf etc/zope.conf

# Copy in and install zms last, to maximize layer caching
COPY --chown=zope:zope . src/
RUN --mount=type=cache,uid=$UID,target=$PIP_CACHE_DIR,sharing=locked <<EOR
    $PIP_INSTALL --editable ./src/[dev]
EOR

# consider if we need the test code to be in the container to run
# in github actions or similar circumstances
# locally it is mapped into the container via bindmounts
# COPY --chown=zope:zope selenium_tests test_output tests ./

CMD ["runwsgi", "--verbose", "etc/zope.ini", "http_port=80"]
