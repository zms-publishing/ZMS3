#!/bin/bash

runzope -X debug-mode=on --configure <(envsubst '$HTTP_PORT' <etc/zope.conf)
