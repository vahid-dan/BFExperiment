#!/bin/bash

ulimit -c unlimited 
echo /var/cores/core.%e.%p.%h.%t > /proc/sys/kernel/core_pattern 
/bin/sh -c /sbin/init
