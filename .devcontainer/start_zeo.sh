#!/bin/bash
# -----------------------------------------------------------------
# The script starts a ZEO server in a container.
# The ZEO server is listening on a socket in the file system.
# -----------------------------------------------------------------

INSTANCE="/home/zope/instance"
VENV="/home/zope/venv"

# Set up environment
export PATH="$VENV/bin:$PATH"

# ---------------------------------
# [A] Start ZEO server
# ---------------------------------
nohup  $VENV/bin/runzeo --configure $INSTANCE/etc/zeo.conf 1>/dev/null 2>/dev/null &
# Check if ZEO server is running on socket: $INSTANCE_HOME/var/zeosocket
if [ -S "$INSTANCE_HOME/var/zeosocket" ] && ss -xl | grep -q "$INSTANCE_HOME/var/zeosocket"; then
  echo "ZEO server already running on $INSTANCE_HOME/var/zeosocket"
  exit 0
fi
echo "Starting ZEO server..."
while ! ss -xl | grep -q "$INSTANCE_HOME/var/zeosocket"; do
  echo "Waiting for ZEO server to start..."
  sleep 1
done
echo "ZEO server started on $INSTANCE_HOME/var/zeosocket"
# ---------------------------------