#!/bin/sh
gcc -D_GNU_SOURCE -lX11 -Wall -fPIC -c -o libxrdpconfigurator.o libxrdpconfigurator.c
gcc -lX11 -shared -o libxrdpconfigurator.so libxrdpconfigurator.o
