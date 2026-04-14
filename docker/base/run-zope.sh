#!/bin/bash

exec runzope --configure <(envsubst '$HTTP_PORT' <etc/zope.conf)
