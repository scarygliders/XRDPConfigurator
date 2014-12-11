#!/bin/bash
echo "Compiling the User Interface files..."
pyside-uic -d -o ./user_interface/XRDPConfiguratorMainWindow.py ./user_interface/XRDPConfiguratorMainWindow.ui
pyside-uic -d -o ./user_interface/SessionFrame.py ./user_interface/SessionFrame.ui
pyside-uic -d -o ./user_interface/PreviewWindow.py ./user_interface/PreviewWindow.ui
pyside-uic -d -o ./user_interface/NewSession.py ./user_interface/NewSession.ui
pyside-uic -d -o ./user_interface/About.py ./user_interface/About.ui
pyside-uic -d -o ./user_interface/AreYouSure.py ./user_interface/AreYouSure.ui
pyside-uic -d -o ./user_interface/InfoWindow.py ./user_interface/InfoWindow.ui
pyside-uic -d -o ./user_interface/LogoCustomization.py ./user_interface/LogoCustomization.ui
pyside-uic -d -o ./user_interface/dialogSize.py ./user_interface/dialogSize.ui
pyside-uic -d -o ./user_interface/logoPosition.py ./user_interface/logoPosition.ui
pyside-uic -d -o ./user_interface/labelsAndBoxes.py ./user_interface/labelsAndBoxes.ui
pyside-uic -d -o ./user_interface/LoginWindowSimulator.py ./user_interface/LoginWindowSimulator.ui
pyside-uic -d -o ./user_interface/DialogButtons.py ./user_interface/DialogButtons.ui
pyside-uic -d -o ./user_interface/ImageImport.py ./user_interface/ImageImport.ui
pyside-rcc -py3 -compress 9 XRDPConfigurator_resources.qrc -o XRDPConfigurator_resources_rc.py
echo "Building the libxrdpconfigurator.so helper library..."
cd libxrdpconfigurator
./buildlib.sh
cd ..
echo "All done. Run ./XRDPConfigurator.sh to start the application."
