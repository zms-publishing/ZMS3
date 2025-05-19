#!/bin/bash
# -----------------------------------------------------------------
# The script starts a ZEO server in a container.
# The ZEO server is listening on a socket in the file system.
# -----------------------------------------------------------------

INSTANCE_DIR="/home/zope/instance"
VENV_DIR="/home/zope/venv"

# Set up environment
export PATH="$VENV_DIR/bin:$PATH"

# ---------------------------------
# [A] Start ZEO server
# ---------------------------------

### Create Data.fs if it does not exist
if ! [ -S "$INSTANCE_DIR/var/Data.fs" ]; then
  echo "New Data.fs is created that ZEO can connect to."
  $VENV_DIR/bin/python2 $INSTANCE_DIR/bin/create_zodb.py
  sleep 2
fi

nohup "$VENV_DIR/bin/runzeo" --configure "$INSTANCE_DIR/etc/zeo.conf" 1>/dev/null 2>/dev/null &
# Check if ZEO server is running on socket: $INSTANCE_DIR/var/zeosocket
if [ -S "$INSTANCE_DIR/var/zeosocket" ] && ss -xl | grep -q "$INSTANCE_DIR/var/zeosocket"; then
  echo "ZEO server already running on $INSTANCE_DIR/var/zeosocket"
  exit 0
fi
echo "Starting ZEO server..."
while ! ss -xl | grep -q "$INSTANCE_DIR/var/zeosocket"; do
  echo "Waiting for ZEO server to start..."
  sleep 1
done
echo "ZEO server started on $INSTANCE_DIR/var/zeosocket"
# ---------------------------------