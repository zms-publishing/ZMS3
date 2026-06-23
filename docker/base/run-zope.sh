#!/bin/bash

exec runzope --configure <(envsubst '$HTTP_PORT $READ_ONLY' <etc/zope.conf)
