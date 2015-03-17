XRDPConfigurator - Configure XRDP easily!
=======================================

**XRDPConfigurator is released under the Apache License, Version 2.0**

XRDPConfigurator Features at-a-glance
-------------------------------------


 - Configure xrdp.ini
 - Configure sesman.ini
 - GUI Keymap Generator
 - Easily customise the login screen with the Login Window Simulator 
   - A WYSIWYG editor
   - Real time colour changes
   - Resize the login dialog
   - Change the login dialog logo
   - Import and convert pictures to the BMP format used by XRDP
   - Checks picture dimensions and offers to correct if necessary
 - Easily add, remove, rename, and sort sessions
 - Easily configure xrdp.ini global options, channel overrides,
   connection types, bpp values, ip address, port, username and password
   values
 - Easily configure sesman.ini Global options, Security settings,
   Session offsets/connection limits/time limits/disconnected sessions,
   logging options, and back-end server parameters Preview the sesman
   and xrdp ini files before saving

System Requirements
-------------------

XRDPConfigurator was written on a Linux system. If you can satisfy the following requirements it may run on OSX, BSD and other systems..

 - Python 3.x  -> 3.3 recommended minimum. Conversion to run on both Python 2.7
   and 3.x is planned for the future.
 - Qt 4 Libraries
 - Python-pyside (e.g. python3-pyside package)
 - pyside-tools (contains the pyside-uic and pyside-rcc utilities)
 - GCC compiler for the helper library (e.g. apt-get install build-essential on Debian-based systems)
 - Xorg header files for compilation of the helper library

How to run XRDPConfigurator
----------

A smoother installation method is being worked on. Here's a rough guide for now (after installing the system requirements listed above)...

 1. **`git clone https://github.com/scarygliders/XRDPConfigurator.git`**
 2. **`cd XRDPConfigurator`**
 3. Run the **`./Setup.sh`** script - this will build the user interface files and the `libxrdpconfigurator.so` helper library.
 4. Run XRDPConfigurator using **`./XRDPConfigurator.sh`**

Usage
--------
If you do not already have XRDP installed on your system, you should install it before using XRDPConfigurator.

XRDP is configured by way of two INI files;

**`xrdp.ini`** - configures the XRDP back-end
**`sesman.ini`** - configures the XRDP session manager

These files are usually located under the **`/etc/xrdp`** directory on your system.

You can load both INI files into XRDPConfigurator at the same time. If you do so, the Edit menu allows you to select which INI file editing page you desire to change. The Save functions are contextual - so if you want to save the resultant edited xrdp.ini file, be sure you're in the Editing an xrp.ini file mode, and the same is true for saving a sesman.ini file.

Unless you have started XRDPConfigurator with superuser priveleges (**not recommended**), you will be unable to overwrite the INI files in /etc/xrdp. Instead, you should save your INI files in a directory which you can write to, then back up your old INI files, and copy over the new files as a priveleged user (e.g. su or sudo).

Changes to XRDP will not become active until the xrdp service has been stopped and restarted.


----------


Development
------------------
Pull requests welcome! :)

Use Qt Designer to edit the UI files - the file XRDPConfigurator_resources.qrc is used for the Qt Resources for the UI files.

I use PyCharm for the Python coding.

Donations
-------------
XRDPConfigurator was originally intended to be a commercial application. I have now released it as Open Source. If this program has been useful to you, please consider sending a donation - there is a donation link on my site at http://scarygliders.net

Regards!
