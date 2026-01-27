#!/bin/bash
# -----------------------------------------------------------------
# OBSOLETE
# The script starts ZEO and Zope instances all in the same container.
# It also creates a MySQL test database and a user with privileges.
# -----------------------------------------------------------------

INSTANCE="/home/zope/instance"
VENV="/home/zope/venv"

# Set up environment
export PATH="$VENV/bin:$PATH"

# ---------------------------------
# [A] Start ZEO server
# ---------------------------------
nohup  $VENV/bin/runzeo --configure $INSTANCE/etc/zeo.conf 1>/dev/null 2>/dev/null &
while ! nc -z localhost 9999; do
  echo "Waiting for ZEO to start..."
  sleep 1
done
echo "ZEO started on port 9999"

# ---------------------------------
# [B] Start Zope instances on ports
# 8085 => read-only
# 8086 => read-write
# 8087 => read-write
# ---------------------------------
PORTS=(8085 8086 8087) 
for PORT in "${PORTS[@]}"; do
  echo "Starting Zope instance on port $PORT..."
  nohup $VENV/bin/runzope -C $INSTANCE/etc/zope_$PORT.conf 1>/dev/null 2>/dev/null &
  while ! nc -z localhost $PORT; do
    echo "Waiting for Zope to start on port $PORT..."
    sleep 1
  done
  echo "Zope started on port $PORT"
done

# ---------------------------------
# Create MySql Test-DB
# ---------------------------------
# Check if the mysql server is running
if ! pgrep -x "mysqld" > /dev/null; then
  echo "MySQL server is not running. Starting MySQL server..."
  sudo service mysql start
  sleep 5
fi
sudo mysql -e "CREATE DATABASE testdb"
sudo mysql -e "CREATE USER 'zope'@'localhost' IDENTIFIED BY 'zope';"
sudo mysql -e "GRANT ALL PRIVILEGES ON testdb.* TO 'zope'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
# Create user-data table
sudo mysql -e "USE testdb; CREATE TABLE user_data (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255));"
sudo mysql -e "USE testdb; INSERT INTO user_data (name, email) VALUES ('John Doe', 'john.doe@example.com');"
echo "User 'zope' with password 'zope' created and granted privileges on testdb"
# ---------------------------------
