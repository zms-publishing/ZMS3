FROM ubuntu:16.04

# Get environment variables from docker-compose.yml:
# So, image file must be created with docker-compose build
# ############################
ARG INSTANCE_DIR
ARG VENV_DIR
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
RUN apt-get install -y netcat
RUN apt-get install -y build-essential
RUN apt-get install -y git
RUN apt-get install -y python2.7
RUN apt-get install -y python-pip
RUN apt-get install -y python-minimal
RUN apt-get install -y python-dev
RUN apt-get install -y python-setuptools
RUN apt-get install -y python-virtualenv
RUN apt-get install -y libsasl2-dev
RUN apt-get install -y libldap2-dev
RUN apt-get install -y libssl-dev
RUN apt-get install -y libsqlite3-dev

# Install memcached
RUN apt-get update && \
	apt-get install -y memcached libmemcached-tools && \
	rm -rf /var/lib/apt/lists/*

# Install MariaDB server and client
RUN apt-get update && \
	apt-get install -y mariadb-server mariadb-client libmysqlclient-dev && \
	rm -rf /var/lib/apt/lists/*
# Configure MySQL
RUN wget https://raw.githubusercontent.com/paulfitz/mysql-connector-c/master/include/my_config.h -O /usr/include/mysql/my_config.h

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

RUN python2 -m pip install pip==20.3

# Grant zope passwordless sudo
RUN apt-get update && \
	apt-get install -y sudo && \
	echo 'zope ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN adduser --disabled-password zope && usermod -aG sudo zope

# # Prepare MySQL runtime & data dirs and give them to zope
# RUN mkdir -p /var/run/mysqld /var/lib/mysql \
#	&& chown -R zope:zope /var/run/mysqld /var/lib/mysql

USER zope
# Create Zope Instance
ENV INSTANCE_DIR=${INSTANCE_DIR}
ENV VIRTUAL_ENV=${VENV_DIR}
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN virtualenv --python=python2 $VIRTUAL_ENV
WORKDIR $VIRTUAL_ENV

RUN pip install -r https://raw.githubusercontent.com/zms-publishing/zms3/master/requirements.txt
RUN pip install git+https://github.com/zms-publishing/ZMS3.git#egg=ZMS
RUN pip install Products.PluginRegistry==1.4
RUN pip install Products.LDAPUserFolder==2.27
RUN pip install Products.PluggableAuthService==1.11.0
RUN pip install Products.LDAPMultiPlugins==1.14
RUN pip install Products.ZSQLMethods==2.13.4
RUN pip install MySQL-python==1.2.5
RUN pip install Products.ZSQLiteDA==0.6.1
RUN pip install Products.ZMySQLDA==3.1.1
RUN pip install Products.SQLAlchemyDA
RUN pip install --no-deps Products.mcdutils==2.0
RUN pip install SQLAlchemy
RUN pip install Pillow
RUN pip install feedparser
RUN pip install python-memcached==1.59


# # Create Zope Instance
# RUN mkzopeinstance -d $INSTANCE_HOME -u admin:admin
# COPY ./var $INSTANCE_HOME/var

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
