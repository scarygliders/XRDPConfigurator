#!/bin/bash
if ( test -e ./libxrdpconfigurator/libxrdpconfigurator.so )
then
    LD_LIBRARY_PATH=./libxrdpconfigurator python3 xrdpconfigurator.py
else
    echo "Cannot run XRDPConfigurator until the helper library has been built."
    echo "Please read the instructions on Github for more help, or browse to http://scarygliders.net for assistance."
fi
