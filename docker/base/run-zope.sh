#!/bin/bash

runzope --configure <(envsubst '$HTTP_PORT' <etc/zope.conf)
