# XRDPConfigurator
# Copyright (c) 2014 Kevin Cave
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys
import socket
import locale
from time import strftime
from ctypes import c_char_p, c_int, Structure, cast, c_void_p, CDLL, POINTER
from PySide import *
from configparser import ConfigParser
from io import StringIO
from user_interface.XRDPConfiguratorMainWindow import Ui_XRDPConfigurator
from user_interface.LoginWindowSimulator import Ui_LoginWindowSimulator
from user_interface.SessionFrame import Ui_sessionConfigForm
from user_interface.PreviewWindow import Ui_PreviewWindow
from user_interface.NewSession import Ui_NewSession
from user_interface.About import Ui_About
from user_interface.AreYouSure import Ui_AreYouSure
from user_interface.InfoWindow import Ui_InfoWindow
from user_interface.LogoCustomization import Ui_LogoCustomization
from user_interface.ImageImport import Ui_ImageImport
from user_interface.dialogSize import Ui_dialogSize
from user_interface.logoPosition import Ui_logoPosition
from user_interface.labelsAndBoxes import Ui_labelsAndBoxes
from user_interface.DialogButtons import Ui_DialogButtonsCustomizationForm


class BoxShades(QtGui.QGraphicsItemGroup):
    # Draws shade lines for the dialog boxes in the Login Window Simulator.
    # Enables easy moving and resizing.
    def __init__(self, parent, boxlength=210, xpos=200, ypos=200):
        super(BoxShades, self).__init__(parent)

        self.parent = parent
        self.boxlength = boxlength
        self.xpos = xpos
        self.ypos = ypos

        pen_width = 1
        pen = QtGui.QPen(QtGui.QColor(128, 128, 128))
        pen.setWidth(pen_width)
        self.topline = QtGui.QGraphicsLineItem(parent=parent)
        self.topline.setPen(pen)
        self.topline.setParentItem(parent)

        pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        pen.setWidth(pen_width)
        self.topline2 = QtGui.QGraphicsLineItem(parent=parent)
        self.topline2.setPen(pen)

        pen = QtGui.QPen(QtGui.QColor(128, 128, 128))
        pen.setWidth(pen_width)
        self.leftline = QtGui.QGraphicsLineItem(parent=parent)
        self.leftline.setPen(pen)

        pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        pen.setWidth(pen_width)
        self.leftline2 = QtGui.QGraphicsLineItem(parent=parent)
        self.leftline2.setPen(pen)

        pen = QtGui.QPen(QtGui.QColor(255, 255, 255))
        pen.setWidth(pen_width)
        self.bottomline = QtGui.QGraphicsLineItem()
        self.bottomline.setPen(pen)

        self.rightline = QtGui.QGraphicsLineItem(parent=parent)
        self.rightline.setPen(pen)

        self.position(xpos, ypos, boxlength)

    def position(self, xpos, ypos, boxlength):  # Place the rectangle at a specified position
        self.topline.setLine(xpos, ypos, xpos + boxlength, ypos)
        self.topline2.setLine(xpos + 1, ypos + 1, xpos + boxlength - 1, ypos + 1)
        self.leftline.setLine(xpos, ypos, xpos, ypos + 17)
        self.leftline2.setLine(xpos + 1, ypos + 1, xpos + 1, ypos + 1 + 17)
        self.bottomline.setLine(xpos, ypos + 18, xpos + boxlength, ypos + 18)
        self.rightline.setLine(xpos + boxlength, ypos, xpos + boxlength, ypos + 18)

    def move(self, x_amount, y_amount):  # Used when moving the rectangle's around
        self.topline.setPos(x_amount, y_amount)
        self.topline2.setPos(x_amount + 1, y_amount + 1)
        self.leftline.setPos(x_amount, y_amount)
        self.leftline2.setPos(x_amount + 1, y_amount + 1)
        self.bottomline.setPos(x_amount, y_amount + 18)
        self.rightline.setPos(x_amount, y_amount)


class LoginWindowSimulator(QtGui.QDialog, Ui_LoginWindowSimulator):
    def __init__(self, parent, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)
        self.setupUi(self)

    resized = QtCore.Signal(QtGui.QResizeEvent)

    def resizeEvent(self, event):
        self.resized.emit(event)


class ColourWidget(QtGui.QColorDialog):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QColorDialog.__init__(self, parent, f)


class LabelsAndBoxesWidget(QtGui.QWidget, Ui_labelsAndBoxes):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)
        self.setupUi(self)


class DialogButtonsCustomizationWidget(QtGui.QDialog, Ui_DialogButtonsCustomizationForm):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)
        self.setupUi(self)


class ImageImport(QtGui.QDialog, Ui_ImageImport):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QPixmap(":/icons/images/icons/XRDPConfiguratorWindowIcon.png"))


class LogoCustomizationWidget(QtGui.QDialog, Ui_LogoCustomization):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QPixmap(":/icons/images/icons/XRDPConfiguratorWindowIcon.png"))


class DialogSizeWidget(QtGui.QWidget, Ui_dialogSize):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)
        self.setupUi(self)


class LogoPositionWidget(QtGui.QWidget, Ui_logoPosition):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)
        self.setupUi(self)


# This form fills in the Session Tabs...
class sessionConfigForm(QtGui.QWidget, Ui_sessionConfigForm):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)
        self.setupUi(self)


class PreviewWindow(QtGui.QDialog, Ui_PreviewWindow):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)
        self.setupUi(self)


# New session pop-up window...
class NewSession(QtGui.QDialog, Ui_NewSession):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)
        self.setupUi(self)


# The About window...
class AboutWindow(QtGui.QDialog, Ui_About):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        cprfile = QtCore.QFile(":/html/html/copyright.html")
        if not cprfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            return
        copyright_text = QtCore.QIODevice.readAll(cprfile)
        self.textBrowser.setText(str(copyright_text))

# The Are You Sure You Want To Quit window...
class AreYouSure(QtGui.QDialog, Ui_AreYouSure):
    def __init__(self, text):
        super(AreYouSure, self).__init__()
        self.setupUi(self)
        self.label.setText(text)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


# A generic Information window...
class InfoWindow(QtGui.QDialog, Ui_InfoWindow):
    def __init__(self, text):
        super(InfoWindow, self).__init__()
        self.setupUi(self)
        self.label.setText(text)
        self.setWindowIcon(QtGui.QPixmap(":/icons/images/icons/XRDPConfiguratorWindowIcon.png"))
        self.buttonBox.accepted.connect(self.accept)


# This class defines the Login Window Dialog item group
class LoginWindowGroup(QtGui.QGraphicsItemGroup):
    def __init__(self, restrict_rect, parent=None):
        QtGui.QGraphicsItemGroup.__init__(self, parent)
        self.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, True)
        self.setHandlesChildEvents(False)
        # Prevent the loginwindow from being moved out of the display area
        self.restrict_rect = restrict_rect

    def mouseMoveEvent(self, event):
        if self.restrict_rect.contains(event.scenePos()):
            QtGui.QGraphicsItemGroup.mouseMoveEvent(self, event)


# Used for both Login Dialog labels and Boxes
class LoginWindowGenericGroup(QtGui.QGraphicsItemGroup):
    def __init__(self, parent=None):
        QtGui.QGraphicsItemGroup.__init__(self, parent)
        self.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, True)
        self.setHandlesChildEvents(False)


# Used for displaying resize arrow and logo pixmaps
# Adds clicked moved and released signals to a QLabel, which normally it doesn't have.
class ClickableQLabel(QtGui.QLabel):
    def __init__(self, image, parent=None):
        super(ClickableQLabel, self).__init__(parent)
        self.setPixmap(image)
        self.setGeometry(0, 0, self.pixmap().width(), self.pixmap().height())

    clicked = QtCore.Signal(QtGui.QMouseEvent)
    moved = QtCore.Signal(QtGui.QMouseEvent)
    released = QtCore.Signal(QtGui.QMouseEvent)

    def mousePressEvent(self, event):
        self.clicked.emit(event)

    def mouseMoveEvent(self, event):
        self.moved.emit(event)

    def mouseReleaseEvent(self, event):
        self.released.emit(event)


# This class defines a Login Dialog Window, banner, and shade lines...
class LoginWindow(QtGui.QWidget):
    def __init__(self):
        super(LoginWindow, self).__init__()
        self.loginrect = QtGui.QGraphicsRectItem()
        self.topline = QtGui.QGraphicsLineItem(self.loginrect)
        self.leftline = QtGui.QGraphicsLineItem(self.loginrect)
        self.bottomline = QtGui.QGraphicsLineItem(self.loginrect)
        self.rightline = QtGui.QGraphicsLineItem(self.loginrect)
        self.loginbanner = QtGui.QGraphicsRectItem(self.loginrect)
        self.bannertext = QtGui.QGraphicsTextItem(self.loginrect)
        self.arrowPixmap = QtGui.QPixmap(":/dragpoint/images/dragpoints/Arrow_bottomright.png")
        self.resizearrow = ClickableQLabel(self.arrowPixmap)
        self.dialog_width = 0
        self.dialog_height = 0

    def createDialog(self, x_pos, y_pos, dialog_width, dialog_height, dialog_colour, pen_width, new_version_flag):
        self.resizearrow.setGeometry(0, 0, self.arrowPixmap.width(), self.arrowPixmap.height())
        self.dialog_width = 0
        self.dialog_height = 0
        hostname = socket.gethostname()
        pen_width = pen_width
        font = QtGui.QFont()
        font.setFamily("Sans")
        font.setPointSize(10)
        font.setStyleStrategy(QtGui.QFont.NoAntialias)

        # Add the main grey rectangle...
        dialog_pen = QtGui.QPen(dialog_colour)
        dialog_brush = QtGui.QBrush(dialog_colour)

        self.loginrect.setPen(dialog_pen)
        self.loginrect.setBrush(dialog_brush)
        self.loginrect.setRect(x_pos, y_pos, dialog_width, dialog_height)

        # Add the top and left "shade lines" - these will be controlled by "white=" in INI
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255))
        pen.setWidth(pen_width)

        self.topline.setPen(pen)
        self.topline.setLine(x_pos + 1, y_pos + 1, x_pos + dialog_width, y_pos + 1)

        self.leftline.setPen(pen)
        self.leftline.setLine(x_pos + 1, y_pos + dialog_height - 1, x_pos + 1, y_pos + 1)

        # Add the bottom and right "shade lines" - these will be controlled by "dark_grey=" in INI
        pen = QtGui.QPen(QtGui.QColor(128, 128, 128))
        pen.setWidth(pen_width)

        self.bottomline.setPen(pen)
        self.bottomline.setLine(x_pos + 1, y_pos + dialog_height, x_pos + dialog_width, y_pos + dialog_height)

        self.rightline.setPen(pen)
        self.rightline.setLine(x_pos + dialog_width, y_pos + dialog_height, x_pos + dialog_width, y_pos)

        # Add the "banner"...
        pen = QtGui.QPen(QtGui.QColor(0, 0, 255))
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))

        self.loginbanner.setPen(pen)
        self.loginbanner.setBrush(brush)
        self.loginbanner.setRect(x_pos + 3, y_pos + 3, dialog_width - 6, 17)

        self.bannertext.setFont(font)
        self.bannertext.setDefaultTextColor(QtGui.QColor(255, 255, 255))
        if new_version_flag:
            self.bannertext.setPlainText("Login to " + hostname)
        else:
            self.bannertext.setPlainText("Login to xrdp")
        self.dialog_width = dialog_width
        self.dialog_height = dialog_height
        self.bannertext.setPos(x_pos, y_pos)
        self.positionResizeArrow(x_pos, y_pos)

        return self.loginrect

    def released(self, event):
        pass

    def adjustDialogSize(self, x_pos, y_pos, dialog_width, dialog_height):
        #        print("x_pos : "+str(int(x_pos))+
        #              ", y_pos : "+str(int(y_pos))+
        #              ", dialog_width : "+str(int(dialog_width))+
        #              ", dialog_height : "+str(int(dialog_height)))
        self.loginrect.setRect(x_pos, y_pos, dialog_width, dialog_height)
        self.topline.setLine(x_pos + 1, y_pos + 1, x_pos + dialog_width, y_pos + 1)
        self.bottomline.setLine(x_pos + 1, y_pos + dialog_height, x_pos + dialog_width, y_pos + dialog_height)
        self.leftline.setLine(x_pos + 1, y_pos + dialog_height - 1, x_pos + 1, y_pos + 1)
        self.rightline.setLine(x_pos + dialog_width, y_pos + dialog_height, x_pos + dialog_width, y_pos)
        self.loginbanner.setRect(x_pos + 3, y_pos + 3, dialog_width - 6, 17)
        self.dialog_width = dialog_width
        self.dialog_height = dialog_height
        self.positionResizeArrow(x_pos, y_pos)

    def positionResizeArrow(self, x_pos, y_pos):
        self.resizearrow.move(x_pos + self.dialog_width - self.arrowPixmap.width(),
                              y_pos + self.dialog_height - self.arrowPixmap.height())

    def resizeVisible(self):
        self.resizearrow.setVisible(True)

    def resizeInvisible(self):
        self.resizearrow.setVisible(False)


# This is the main program logic.
def getColour(value):
    webcolour = '#' + value
    colour = QtGui.QColor(0, 0, 0)
    colour.setNamedColor(webcolour)
    return colour


def verifyXrdpIni(fname):
    in_file = ConfigParser()
    in_file.read(fname)
    if (in_file.has_section("globals")) and (in_file.has_section("xrdp1")):  # and (file.has_section("channels")):
        return True
    else:
        message_window = InfoWindow(
            "<html><head/><body><p>The file you attempted to open did not</p><p>appear to be an xrdp.ini file.</p></body></html>")
        message_window.exec_()
        return False


def verifySesmanIni(fname):
    in_file = ConfigParser()
    in_file.read(fname)
    if (in_file.has_section("Globals")) and (in_file.has_section("Security")) and (in_file.has_section("Sessions")):
        return True
    else:
        message_window = InfoWindow(
            "<html><head/><body><p>The file you attempted to open did not</p><p>appear to be a sesman.ini file.</p></body></html>")
        message_window.exec_()
        return False


class XRDPConfigurator(QtGui.QMainWindow, Ui_XRDPConfigurator):
    def __init__(self):
        super(XRDPConfigurator, self).__init__()

        self.setupUi(self)

        #  Connect menu item signals to their relevant functions...
        self.actionKeymaps.triggered.connect(self.showkeymapgenpage)
        self.actionLogin_Window.triggered.connect(self.showLoginWindowSim)
        self.actionOpenSesman_ini.triggered.connect(self.fileOpenSesmanIni)
        self.actionOpenXrdp_ini.triggered.connect(self.fileOpenXrdpIni)
        self.actionQuit.triggered.connect(self.fileQuit)
        self.actionSave.triggered.connect(self.fileSave)
        self.actionSave_as.triggered.connect(self.fileSaveAs)
        self.actionSesman_ini.triggered.connect(self.showSesmanIniPage)
        self.actionXrdp_ini.triggered.connect(self.showXrdpIniPage)
        self.actionPreview.triggered.connect(self.xrdpIniPreview)
        self.actionAbout.triggered.connect(self.showAbout)  # connect help-about to About Window

        # Connect GUI signals to their relevant functions...
        self.addNewSessionButton.clicked.connect(self.addNewSession)
        self.additionalPamErrorTextCheckbox.clicked.connect(self.pamErrorTextHandler)
        self.allowMultimonCheckBox.clicked.connect(self.allowMultimonChanged)
        self.allowRootLoginCheckBox.clicked.connect(self.allowRootLoginCheckBoxChanged)
        self.alwaysCheckGroupCheckBox.clicked.connect(self.alwaysCheckGroupCheckBoxChanged)
        self.autoRunComboBox.currentIndexChanged.connect(self.autorunSessionChanged)
        self.cryptLevelComboBox.currentIndexChanged.connect(self.cryptLevelChanged)
        self.defaultWindowManagerEntryBox.returnPressed.connect(self.defaultWindowManagerEntryBoxChanged)
        self.deleteSessionButton.clicked.connect(self.deleteSession)
        self.disableNewCursorsCheckBox.clicked.connect(self.disableNewCursorsChanged)
        self.disconnectedTimeLimitSpinBox.valueChanged.connect(self.disconnectedTimeLimitSpinBoxChanged)
        self.enableChannelsCheckBox.clicked.connect(self.enableChannelsChanged)
        self.enableSesmanSyslogCheckBox.clicked.connect(self.sesmanEnableSyslogChanged)
        self.enableSyslogCheckBox.clicked.connect(self.enableSyslogChanged)
        self.enableUserWindowManager.clicked.connect(self.sesmanEnableUserWindowManagerChanged)
        self.forkSessionsCheckBox.clicked.connect(self.forkSessionsChanged)
        self.hideLogWindowCheckBox.clicked.connect(self.hideLogWindowChanged)
        self.idleTimeLimitSpinBox.valueChanged.connect(self.idleTimeLimitSpinBoxChanged)
        self.killDisconnectedCheckBox.clicked.connect(self.killDisconnectedCheckBoxChanged)
        self.logFileNameEntryBox.editingFinished.connect(self.logFileNameChanged)
        self.logLevelComboBox.currentIndexChanged.connect(self.logLevelChanged)
        self.maxBppComboBox.currentIndexChanged.connect(self.maxBppChanged)
        self.maxLoginRetrySpinBox.valueChanged.connect(self.maxLoginRetrySpinBoxChanged)
        self.maxSessionsSpinBox.valueChanged.connect(self.maxSessionsSpinBoxChanged)
        self.pamErrorText.editingFinished.connect(self.pamErrorTextHandler)
        self.requireCredentialsCheckbox.clicked.connect(self.requireCredentialsChanged)
        self.savekeymapasbutton.clicked.connect(self.saveKeymapFile)
        self.selected_keymap_combobox.currentIndexChanged.connect(self.updateKeymapCode)
        self.sesmanListeningAddressEntryBox.returnPressed.connect(self.sesmanListeningIPAddressChanged)
        self.listeningPortEntryBox.returnPressed.connect(self.sesmanListenPortChanged)
        self.sesmanLogFileNameEntryBox.returnPressed.connect(self.sesmanLogFileNameEntryBoxChanged)
        self.sesmanLogLevelComboBox.currentIndexChanged.connect(self.sesmanLogLevelComboBoxChanged)
        self.sesmanSysLogLevelComboBox.currentIndexChanged.connect(self.sesmanSyslogLevelChanged)
        self.sysLogLevelComboBox.currentIndexChanged.connect(self.xrdpSyslogLevelChanged)
        self.tcpKeepAliveCheckBox.clicked.connect(self.tcpKeepaliveChanged)
        self.tcpNoDelayCheckBox.clicked.connect(self.tcpNodelayChanged)
        self.terminalServiceAdminsEntryBox.returnPressed.connect(self.terminalServiceAdminsEntryBoxChanged)
        self.terminalServiceUsersEntryBox.returnPressed.connect(self.terminalServiceUsersEntryBoxChanged)
        self.useBitMapCacheCheckBox.clicked.connect(self.useBitMapCacheChanged)
        self.useBitMapCompCheckBox.clicked.connect(self.useBitMapCompChanged)
        self.useBulkCompCheckBox.clicked.connect(self.useBulkCompChanged)
        self.useClipRdrCheckBox.clicked.connect(self.useClipRdrChanged)
        self.useDrDynVcCheckBox.clicked.connect(self.useDrDynVcChanged)
        self.useRAILCheckBox.clicked.connect(self.useRAILChanged)
        self.useRdpDrCheckBox.clicked.connect(self.useRdpDrChanged)
        self.useRdpSndCheckBox.clicked.connect(self.useRdpSndChanged)
        self.useXrdpVrCheckBox.clicked.connect(self.useXrdpVrChanged)
        self.userWindowManagerEntryBox.returnPressed.connect(self.userWindowManagerEntryBoxChanged)
        self.x11DisplayOffsetSpinBox.valueChanged.connect(self.x11DisplayOffsetSpinBoxChanged)
        self.x11rdpParamsLineEdit.returnPressed.connect(self.xserverParamsChanged)
        self.xvncParamsLineEdit.returnPressed.connect(self.xserverParamsChanged)
        self.listeningPortEntryBox.editingFinished.connect(self.listeningportchanged)
        self.listeningAddressEntryBox.editingFinished.connect(self.listeningaddresschanged)

        self.about_window = AboutWindow()

        self.xrdp_ini_filename = ""  # Name of currently opened xrdp.ini file.
        self.locale_detected = ""  # The detected system locale.
        self.keymapname = ""  # Name of the keymap.
        self.keymappreview = []
        self.keymappreview = StringIO()
        self.sessions_channel_override_active_list = []
        self.overridearray = []
        self.xrdpfilename = ""
        self.xrdp_ini_file = ConfigParser()
        self.xrdp_debug_checkbox = None
        self.editingSesman = False
        self.editingXrdpIni = False
        self.sesman_ini_filename = ""
        self.winSim = None
        self.x_pos = 0
        self.y_pos = 0
        self.helpbtn_width = 0
        self.helpbtn_height = 0
        self.user_text_xpos = 0
        self.user_text_ypos = 0
        self.pass_text_xpos = 0
        self.pass_text_ypos = 0
        self.mod_box_xpos = 0
        self.mod_box_ypos = 0
        self.user_box_xpos = 0
        self.user_box_ypos = 0
        self.pass_box_xpos = 0
        self.pass_box_ypos = 0
        self.helpbtn_xpos = 0
        self.helpbtn_ypos = 0
        self.tab_bar = self.sessionsTab.findChild(QtGui.QTabBar, "qt_tabwidget_tabbar")
        self.tab_bar.tabMoved[int, int].connect(self.reordersessiontabs)
        self.boxlength = 0
        self.dialog_width = 0
        self.dialog_height = 0
        self.mod_text_xpos = 0
        self.mod_text_ypos = 0
        self.okbtn_xpos = 0
        self.okbtn_ypos = 0
        self.okbtn_width = 0
        self.okbtn_height = 0
        self.cancelbtn_xpos = 0
        self.cancelbtn_ypos = 0
        self.cancelbtn_width = 0
        self.cancelbtn_height = 0
        self.logo_xpos = 0
        self.logo_ypos = 0
        self.simscene = None
        self.simbackgroundscene = None
        self.simwindowscene = None
        self.simtitleBgndscene = None
        self.simtextscene = None
        self.simboxesscene = None
        self.simbotRightscene = None
        self.simdarkBluescene = None
        self.dark_blue = QtGui.QColor(0, 0, 127)

    Version = "1.0"
    hilight_background_running = 0
    highlight_text_running = 0
    something_sesman_changed = 0
    something_xrdp_changed = 0
    xrdp_ini_file_opened = 0
    sesman_ini_file_opened = 0
    new_version_flag = 0
    hostname = socket.gethostname()
    logo_filename = ""

    # This array is for use with channel overrides handler.
    # It comprises of the Globals channel name, the Sessions channel name, and the
    # corresponding Qt Widget name for the channel override tickboxes which are in
    # each of the Sessions tabs...
    SESSIONOVERRIDESLIST = [['rdpdr', 'channel.rdpdr', 'useRdpDrCheckBox'],
                            ['rdpsnd', 'channel.rdpsnd', 'useRdpSndCheckBox'],
                            ['drdynvc', 'channel.drdynvc', 'useDrDynVcCheckBox'],
                            ['cliprdr', 'channel.cliprdr', 'useClipRdrCheckBox'],
                            ['rail', 'channel.rail', 'useRAILCheckBox'],
                            ['xrdpvr', 'channel.xrdpvr', 'useXrdpVrCheckBox']]

    # Used for parsing channels...
    CHANNEL_LIST = ["useRdpDrCheckBox", "useRdpSndCheckBox", "useDrDynVcCheckBox", "useClipRdrCheckBox",
                    "useRAILCheckBox", "useXrdpVrCheckBox"]

    # initialise keymaps...
    keymap = [[]]
    KEYMAP_LIST = """0436 af Afrikaans
041C sq Albanian
0001 ar Arabic
0401 ar-sa Arabic (Saudi Arabia)
0801 ar-iq Arabic (Iraq)
0C01 ar-eg Arabic (Egypt)
1001 ar-ly Arabic (Libya)
1401 ar-dz Arabic (Algeria)
1801 ar-ma Arabic (Morocco)
1C01 ar-tn Arabic (Tunisia)
2001 ar-om Arabic (Oman)
2401 ar-ye Arabic (Yemen)
2801 ar-sy Arabic (Syria)
2C01 ar-jo Arabic (Jordan)
3001 ar-lb Arabic (Lebanon)
3401 ar-kw Arabic (Kuwait)
3801 ar-ae Arabic (U.A.E.)
3C01 ar-bh Arabic (Bahrain)
4001 ar-qa Arabic (Qatar)
042D eu Basque
0402 bg Bulgarian
0423 be Belarusian
0403 ca Catalan
0004 zh Chinese
0404 zh-tw Chinese (Taiwan)
0804 zh-cn Chinese (China)
0C04 zh-hk Chinese (Hong Kong SAR)
1004 zh-sg Chinese (Singapore)
041A hr Croatian
0405 cs Czech
0406 da Danish
0413 nl Dutch (Netherlands)
0813 nl-be Dutch (Belgium)
0009 en English
0409 en-us English (United States)
0809 en-gb English (United Kingdom)
0C09 en-au English (Australia)
1009 en-ca English (Canada)
1409 en-nz English (New Zealand)
1809 en-ie English (Ireland)
1C09 en-za English (South Africa)
2009 en-jm English (Jamaica)
2809 en-bz English (Belize)
2C09 en-tt English (Trinidad)
0425 et Estonian
0438 fo Faeroese
0429 fa Farsi
040B fi Finnish
040C fr French (France)
080C fr-be French (Belgium)
0C0C fr-ca French (Canada)
100C fr-ch French (Switzerland)
140C fr-lu French (Luxembourg)
043C gd Gaelic
0407 de German (Germany)
0807 de-ch German (Switzerland)
0C07 de-at German (Austria)
1007 de-lu German (Luxembourg)
1407 de-li German (Liechtenstein)
0408 el Greek
040D he Hebrew
0439 hi Hindi
040E hu Hungarian
040F is Icelandic
0421 in Indonesian
0410 it Italian (Italy)
0810 it-ch Italian (Switzerland)
0411 ja Japanese
0412 ko Korean
0426 lv Latvian
0427 lt Lithuanian
042F mk FYRO Macedonian
043E ms Malay (Malaysia)
043A mt Maltese
0414 no Norwegian (Bokmal)
0814 no Norwegian (Nynorsk)
0415 pl Polish
0416 pt-br Portuguese (Brazil)
0816 pt Portuguese (Portugal)
0417 rm Rhaeto-Romanic
0418 ro Romanian
0818 ro-mo Romanian (Moldova)
0419 ru Russian
0819 ru-mo Russian (Moldova)
0C1A sr Serbian (Cyrillic)
081A sr Serbian (Latin)
041B sk Slovak
0424 sl Slovenian
042E sb Sorbian
040A es Spanish (Traditional Sort)
080A es-mx Spanish (Mexico)
0C0A es Spanish (International Sort)
100A es-gt Spanish (Guatemala)
140A es-cr Spanish (Costa Rica)
180A es-pa Spanish (Panama)
1C0A es-do Spanish (Dominican Republic)
200A es-ve Spanish (Venezuela)
240A es-co Spanish (Colombia)
280A es-pe Spanish (Peru)
2C0A es-ar Spanish (Argentina)
300A es-ec Spanish (Ecuador)
340A es-cl Spanish (Chile)
380A es-uy Spanish (Uruguay)
3C0A es-py Spanish (Paraguay)
400A es-bo Spanish (Bolivia)
440A es-sv Spanish (El Salvador)
480A es-hn Spanish (Honduras)
4C0A es-ni Spanish (Nicaragua)
500A es-pr Spanish (Puerto Rico)
0430 sx Sutu
041D sv Swedish
081D sv-fi Swedish (Finland)
041E th Thai
0431 ts Tsonga
0432 tn Tswana
041F tr Turkish
0422 uk Ukrainian
0420 ur Urdu
042A vi Vietnamese
0434 xh Xhosa
043D ji Yiddish
0435 zu Zulu
"""

    changed_background_colour = "8feda4"
    line_edit_changed_stylesheet = "QLineEdit{background: #" + changed_background_colour + "; font: bold 'Ariel'; }"
    spinbox_changed_stylesheet = "QSpinBox{background: #" + changed_background_colour + "; font: bold 'Ariel'; }"
    checkbox_changed_stylesheet = "QCheckBox{background: #" + changed_background_colour + "; font: bold 'Ariel'; }"
    combobox_changed_stylesheet = "QComboBox{background: #" + changed_background_colour + "; font: bold 'Ariel'; }"
    colourbutton_stylesheet = "QPushButton{background: #" + changed_background_colour + "; font: bold 'Ariel'; }"

    # noinspection PyTypeChecker
    def initkeymaplocales(self):
        #test='zh-sg'
        #l = list(test)
        l = list(str(locale.getlocale()[0]).lower())
        try:
            ind = l.index('_')
            l[ind] = '-'
        except ValueError:
            pass

        loc = "".join(l)

        if len(self.keymap) == 1:
            self.keymap[0] = ['    ', 'Select a country...']
            i = 1
            for lines in self.KEYMAP_LIST.split('\n'):
                code = lines[:4]
                unf = lines[5:].split(' ')
                frm = str('{0: <7}'.format(unf[0]))
                for j in range(1, len(unf)):
                    frm = frm + ' ' + unf[j]
                self.keymap.append([])
                self.keymap[i].extend([code, frm])

                if loc == unf[0]:
                    self.locale_detected = i
                i += 1
            for i in range(len(self.keymap)):
                if self.keymap[i]:
                    self.selected_keymap_combobox.addItem(self.keymap[i][1])
            self.selected_keymap_combobox.removeItem(i)
            #return self.locale_detected

    def showkeymapgenpage(self):
        self.initkeymaplocales()
        self.selected_keymap_combobox.setCurrentIndex(self.locale_detected)
        self.actionPreview.setEnabled(False)
        self.setWindowTitle("XRDPConfigurator : Keymap Generator")
        self.stackedWidget.setVisible(True)
        self.stackedWidget.setCurrentIndex(3)
        self.filenameFrame.setVisible(False)
        self.generatekeymap()

    # noinspection PyUnusedLocal
    def updateKeymapCode(self, arg):
        index = self.selected_keymap_combobox.currentIndex()
        if index != 0:
            mapcode = self.keymap[index][0]
            if index == self.locale_detected:
                self.locale_autodetected_label.setVisible(True)
            else:
                self.locale_autodetected_label.setVisible(False)
            self.keymapname = "km-" + str(mapcode.lower()) + ".ini"
            self.keymapNameLabel.setText(self.keymapname)
            self.step3group.setEnabled(True)
        else:
            self.keymapNameLabel.setText('')
            self.step3group.setEnabled(False)
        self.keymapcodelabel.setText(self.keymap[index][0])

    def generatekeymap(self):
        # This function generates a keymap, based on keycodes as seen by the X server you are running this application
        # under.
        # It uses Python's ctypes foreign function library to allow calling functions in shared libraries
        # I could do just about everything within Python, except for calling some Xlib functions, for some reason.
        # Because of this, a small helper library written in C, called libxrdpconfigurator was created, which needs to be
        # compiled and installed somewhere the system can supply it to this program - /usr/lib for example.
        # Perhaps some time in the future, a way can be found to call the necessary Xlib functions within this function,
        # and the C helper library could be dispensed with.
        if 'self.keymappreview' in globals():
            del self.keymappreview

        self.keymapbrowser.clear()

        class Display(Structure):
            pass

        sects = ["noshift", "shift", "altgr", "capslock", "shiftcapslock", "shiftaltgr"]
        sectcount = len(sects)

        states = [c_int(0), c_int(1), c_int(0x80), c_int(2), c_int(3), c_int(0x81)]

        lib = CDLL("libxrdpconfigurator.so")

        GetLookupString = lib.getlookupstring
        GetLookupString.restype = c_void_p
        lib.freeme.argtypes = []
        lib.freeme.restype = c_void_p

        xlib = CDLL('libX11.so.6')
        xlib.XOpenDisplay.argtypes = [c_char_p]
        xlib.XOpenDisplay.restype = POINTER(Display)
        xdisplay = xlib.XOpenDisplay(None)

        if not xdisplay:
            print("ERROR: could not open DISPLAY.")
            return

        index = 0
        while index < sectcount:
            secname = sects[index]
            name = str("[" + secname + "]\n")
            self.keymappreview.write(name)
            keycode = 8
            while keycode <= 137:
                state = states[index]
                ptr = GetLookupString(xdisplay, c_int(keycode), state)
                output = cast(ptr, c_char_p).value.decode('utf-8')
                self.keymappreview.write(output)
                if keycode <= 137:
                    self.keymappreview.write("\n")
                keycode += 1
            index += 1
            if index <= sectcount - 1:
                self.keymappreview.write("\n")
        xlib.XCloseDisplay(xdisplay)
        self.keymapbrowser.appendPlainText(self.keymappreview.getvalue())

    def saveKeymapFile(self):
        fname = QtGui.QFileDialog.getSaveFileName(self, "Save keymap file as...", self.keymapname, "Ini files (*.ini)")
        if fname[0] != "":
            with open(fname[0], 'w') as keymapfile:
                keymapfile.writelines(self.keymappreview.getvalue())
            keymapfile.close()

    def xrdpIniPreview(self):
        preview_window = PreviewWindow()
        preview_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        if self.editingXrdpIni:
            config = self.ConfigFileGenerator("xrdp.ini")
            self.xrdp_ini_file.write(config, space_around_delimiters=False)
        else:
            config = self.ConfigFileGenerator("sesman.ini")
            self.sesman_ini_file.write(config, space_around_delimiters=False)
        preview_window.previewBrowser.appendPlainText(config.getvalue())
        preview_window.previewBrowser.moveCursor(QtGui.QTextCursor.Start)
        preview_window.exec_()
        config.close()

    def showAbout(self):
        self.about_window.exec()

    # GLOBALS --- Click/change event handlers...

    def listeningaddresschanged(self):
        if self.listeningAddressEntryBox.isModified():
            if not self.xrdp_ini_file.has_option('globals', 'address'):
                self.xrdp_ini_file.set('globals', 'address', '0.0.0.0')
            self.xrdp_ini_file.set('globals', 'address', self.listeningAddressEntryBox.text())
            self.xrdp_changed()
            self.listeningAddressEntryBox.setStyleSheet(self.line_edit_changed_stylesheet)

    def listeningportchanged(self):
        if self.listeningPortEntryBox.isModified():
            if not self.xrdp_ini_file.has_option('globals', 'port'):
                self.xrdp_ini_file.set('globals', 'port', '3389')
            self.xrdp_ini_file.set('globals', 'port', self.listeningPortEntryBox.text())
            self.xrdp_changed()
            self.listeningPortEntryBox.setStyleSheet(self.line_edit_changed_stylesheet)

    # noinspection PyUnusedLocal
    def maxBppChanged(self, arg):
        if not self.xrdp_ini_file.has_option('globals', 'max_bpp'):
            self.xrdp_ini_file.set('globals', 'max_bpp', '24')
        self.xrdp_ini_file.set('globals', 'max_bpp', self.maxBppComboBox.currentText())
        self.xrdp_changed()
        self.maxBppComboBox.setStyleSheet(self.combobox_changed_stylesheet)

    # noinspection PyUnusedLocal
    def cryptLevelChanged(self, arg):
        if not self.xrdp_ini_file.has_option('globals', 'crypt_level'):
            self.xrdp_ini_file.set('globals', 'crypt_level', 'low')
        self.xrdp_ini_file.set('globals', 'crypt_level', self.cryptLevelComboBox.currentText())
        self.xrdp_changed()
        self.cryptLevelComboBox.setStyleSheet(self.combobox_changed_stylesheet)

    def autorunSessionChanged(self, index):
        if index == 0:
            self.xrdp_ini_file.remove_option('globals', 'autorun')
        if index > 0:
            if not self.xrdp_ini_file.has_option('globals', 'autorun'):
                self.xrdp_ini_file.set('globals', 'autorun', '')
            self.xrdp_ini_file.set('globals', 'autorun', self.autoRunComboBox.currentText())
        self.xrdp_changed()
        self.autoRunComboBox.setStyleSheet(self.combobox_changed_stylesheet)

    def useBitMapCacheChanged(self):
        if not self.xrdp_ini_file.has_option('globals', 'bitmap_cache'):
            self.xrdp_ini_file.set('globals', 'bitmap_cache', 'no')
        if self.useBitMapCacheCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('globals', 'bitmap_cache', "no")
        else:
            self.xrdp_ini_file.set('globals', 'bitmap_cache', "yes")
        self.xrdp_changed()
        self.useBitMapCacheCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def useBitMapCompChanged(self):
        if not self.xrdp_ini_file.has_option('globals', 'bitmap_compression'):
            self.xrdp_ini_file.set('globals', 'bitmap_compression', 'no')
        if self.useBitMapCompCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('globals', 'bitmap_compression', "no")
        else:
            self.xrdp_ini_file.set('globals', 'bitmap_compression', "yes")
        self.xrdp_changed()
        self.useBitMapCompCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def useBulkCompChanged(self):
        if not self.xrdp_ini_file.has_option('globals', 'bulk_compression'):
            self.xrdp_ini_file.set('globals', 'bulk_compression', 'no')
        if self.useBulkCompCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('globals', 'bulk_compression', "no")
        else:
            self.xrdp_ini_file.set('globals', 'bulk_compression', "yes")
        self.xrdp_changed()
        self.useBulkCompCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def enableChannelsChanged(self):
        if not self.xrdp_ini_file.has_option('globals', 'channel_code'):
            self.xrdp_ini_file.set('globals', 'channel_code', 'no')
        if self.enableChannelsCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('globals', 'channel_code', "0")
        else:
            self.xrdp_ini_file.set('globals', 'channel_code', "1")
        self.xrdp_changed()
        self.enableChannelsCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def forkSessionsChanged(self):
        if not self.xrdp_ini_file.has_option('globals', 'fork'):
            self.xrdp_ini_file.set('globals', 'fork', 'no')
        if self.forkSessionsCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('globals', 'fork', "no")
        else:
            self.xrdp_ini_file.set('globals', 'fork', "yes")
        self.xrdp_changed()
        self.forkSessionsCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def hideLogWindowChanged(self):
        if not self.xrdp_ini_file.has_option('globals', 'hidelogwindow'):
            self.xrdp_ini_file.set('globals', 'hidelogwindow', 'no')
        if self.hideLogWindowCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('globals', 'hidelogwindow', "no")
        else:
            self.xrdp_ini_file.set('globals', 'hidelogwindow', "yes")
        self.xrdp_changed()
        self.hideLogWindowCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def tcpNodelayChanged(self):
        if not self.xrdp_ini_file.has_option('globals', 'tcp_nodelay'):
            self.xrdp_ini_file.set('globals', 'tcp_nodelay', 'no')
        if self.tcpNoDelayCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('globals', 'tcp_nodelay', "no")
        else:
            self.xrdp_ini_file.set('globals', 'tcp_nodelay', "yes")
        self.xrdp_changed()
        self.tcpNoDelayCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def tcpKeepaliveChanged(self):
        if not self.xrdp_ini_file.has_option('globals', 'tcp_keepalive'):
            self.xrdp_ini_file.set('globals', 'tcp_keepalive', 'no')
        if self.tcpKeepAliveCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('globals', 'tcp_keepalive', "no")
        else:
            self.xrdp_ini_file.set('globals', 'tcp_keepalive', "yes")
        self.xrdp_changed()
        self.tcpKeepAliveCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def requireCredentialsChanged(self):
        if self.requireCredentialsCheckbox.checkState() == 2:
            if not self.xrdp_ini_file.has_option('globals', 'require_credentials'):
                self.xrdp_ini_file.set('globals', 'require_credentials', 'yes')
        else:
            if self.xrdp_ini_file.has_option('globals', 'require_credentials'):
                self.xrdp_ini_file.remove_option('globals', 'require_credentials')
        self.xrdp_changed()
        self.requireCredentialsCheckbox.setStyleSheet(self.checkbox_changed_stylesheet)

    def allowMultimonChanged(self):
        if self.allowMultimonCheckBox.checkState() == 2:
            if not self.xrdp_ini_file.has_option('globals', 'allow_multimon'):
                self.xrdp_ini_file.set('globals', 'allow_multimon', 'true')
        else:
            if self.xrdp_ini_file.has_option('globals', 'allow_multimon'):
                self.xrdp_ini_file.remove_option('globals', 'allow_multimon')
        self.xrdp_changed()
        self.allowMultimonCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def pamErrorTextHandler(self):
        if self.additionalPamErrorTextCheckbox.checkState() == 2:
            self.pamErrorText.setEnabled(True)
            if self.pamErrorText.isModified():
                self.xrdp_ini_file.set('globals', 'pamerrortxt', self.pamErrorText.text())
                self.pamErrorText.setStyleSheet(self.line_edit_changed_stylesheet)
                self.xrdp_changed()
                self.pamErrorText.setModified(0)
        if self.additionalPamErrorTextCheckbox.checkState() == 0:
            self.pamErrorText.setEnabled(False)
            if self.xrdp_ini_file.has_option('globals', 'pamerrortxt'):
                self.xrdp_ini_file.remove_option('globals', 'pamerrortxt')
        self.xrdp_changed()
        self.additionalPamErrorTextCheckbox.setStyleSheet(self.checkbox_changed_stylesheet)

    def disableNewCursorsChanged(self):
        if self.disableNewCursorsCheckBox.checkState() == 2:
            self.xrdp_ini_file.set('globals', 'new_cursors', 'no')
        else:
            self.xrdp_ini_file.set('globals', 'new_cursors', 'yes')
        self.xrdp_changed()
        self.disableNewCursorsCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    # Set or unset the xrdp1 session for debugging XRDP if the debug checkbox is enabled by the user...
    def debugClicked(self):
        self.debugHandler(0, "xrdp1")

    def debugHandler(self, index, secname):
        # This function decides what to do when the Debug option on [xrdp1] is clicked (or not).
        # It has to handle the re-ordering of tabs - hence the re-ordering of the xrdp.ini file,
        # and 'hand the torch over' to whatever new tab/xrdpX section will become the [xrdp1] session.
        # @param index: the number/id/index of the tab in question
        # @param secname: the section name
        global original_port_setting
        sessionport_widget = self.sessionsTab.widget(index).findChild(QtGui.QLineEdit, "sessionPortEntryBox")
        chansrvport_widget = self.sessionsTab.widget(index).findChild(QtGui.QLineEdit, "chansrvPortEntryBox")
        sessionport_label_widget = self.sessionsTab.widget(index).findChild(QtGui.QLabel, "sessionport_label")
        chansrvport_label_widget = self.sessionsTab.widget(index).findChild(QtGui.QLabel, "chansrvport_label")
        checkbox = self.sessionsTab.widget(index).findChild(QtGui.QCheckBox, "debugXRDPCheckbox")
        if checkbox.checkState() == 0:
            if self.xrdp_ini_file.has_option(secname, 'chansrvport'):
                self.xrdp_ini_file.remove_option(secname, 'chansrvport')
            if 'original_port_setting' not in globals():
                #self.original_port_setting = sessionport_widget.text()
                original_port_setting = '-1'
            self.xrdp_ini_file.set(secname, 'port', original_port_setting)
            sessionport_widget.setText(original_port_setting)
            chansrvport_widget.setVisible(False)
            chansrvport_label_widget.setVisible(False)
            sessionport_label_widget.setEnabled(True)
            sessionport_widget.setEnabled(True)
        else:
            original_port_setting = self.xrdp_ini_file.get(secname, 'port')
            self.xrdp_ini_file.set(secname, 'port', '/tmp/.xrdp/xrdp_display_10')
            sessionport_widget.setText('/tmp/.xrdp/xrdp_display_10')
            chansrvport_widget.setVisible(True)
            chansrvport_label_widget.setVisible(True)
            self.xrdp_ini_file.set(secname, 'chansrvport', '/tmp/.xrdp/xrdp_chansrv_socket_7210')
            chansrvport_widget.setText('/tmp/.xrdp/xrdp_chansrv_socket_7210')
            sessionport_label_widget.setEnabled(False)
            sessionport_widget.setEnabled(False)
        self.xrdp_changed()
        checkbox.setStyleSheet(self.checkbox_changed_stylesheet)

    # LOGGING --- Click/change event handlers...
    def logFileNameChanged(self):
        if self.logFileNameEntryBox.isModified():
            if not self.xrdp_ini_file.has_option('Logging', 'LogFile'):
                self.xrdp_ini_file.set('Logging', 'LogFile', 'xrdp.log')
            self.xrdp_ini_file.set('Logging', 'LogFile', self.logFileNameEntryBox.text())
            self.xrdp_changed()
            self.logFileNameEntryBox.setModified(0)
            self.logFileNameEntryBox.setStyleSheet(self.line_edit_changed_stylesheet)

    # noinspection PyUnusedLocal
    def logLevelChanged(self, arg):
        if not self.xrdp_ini_file.has_option('Logging', 'LogLevel'):
            self.xrdp_ini_file.set('Logging', 'LogLevel', 'DEBUG')
        self.xrdp_ini_file.set('Logging', 'LogLevel', self.logLevelComboBox.currentText())
        self.xrdp_changed()
        self.logLevelComboBox.setStyleSheet(self.combobox_changed_stylesheet)
        self.xrdpSyslogLevelChanged(1)

    def enableSyslogChanged(self):
        if not self.xrdp_ini_file.has_option('Logging', 'EnableSyslog'):
            self.xrdp_ini_file.set('Logging', 'EnableSyslog', 'no')
        if self.enableSyslogCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('Logging', 'EnableSyslog', "no")
            self.label_12.setEnabled(False)
            self.sysLogLevelComboBox.setEnabled(False)
            if self.xrdp_ini_file.has_option('Logging', 'SyslogLevel'):
                self.xrdp_ini_file.remove_option('Logging', 'SyslogLevel')
        else:
            self.xrdp_ini_file.set('Logging', 'EnableSyslog', "yes")
            self.label_12.setEnabled(True)
            self.sysLogLevelComboBox.setEnabled(True)
            self.xrdp_ini_file.set('Logging', 'Sysloglevel', self.sysLogLevelComboBox.currentText())
            self.xrdpSyslogLevelChanged(1)
        self.xrdp_changed()
        self.sysLogLevelComboBox.setStyleSheet(self.combobox_changed_stylesheet)
        self.enableSyslogCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    # noinspection PyUnusedLocal
    def xrdpSyslogLevelChanged(self, arg):
        if self.xrdp_ini_file.has_option('Logging', 'SyslogLevel'):
            if self.sysLogLevelComboBox.currentIndex() > self.logLevelComboBox.currentIndex():
                self.xrdp_ini_file.set('Logging', 'SyslogLevel', self.xrdp_ini_file.get('Logging', 'SyslogLevel'))
                self.sysLogLevelComboBox.setCurrentIndex(self.logLevelComboBox.currentIndex())
            else:
                self.xrdp_ini_file.set('Logging', 'SyslogLevel', self.sysLogLevelComboBox.currentText())
        self.xrdp_changed()
        self.sysLogLevelComboBox.setStyleSheet(self.combobox_changed_stylesheet)

    # CHANNELS - Click/change event handlers...

    def useRdpDrChanged(self):
        if not self.xrdp_ini_file.has_option('channels', 'rdpdr'):
            self.xrdp_ini_file.set('channels', 'rdpdr', '0')
        if self.useRdpDrCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('channels', 'rdpdr', "0")
        else:
            self.xrdp_ini_file.set('channels', 'rdpdr', "true")
        self.xrdp_changed()
        self.useRdpDrCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def useRdpSndChanged(self):
        if not self.xrdp_ini_file.has_option('channels', 'rdpsnd'):
            self.xrdp_ini_file.set('channels', 'rdpsnd', '0')
        if self.useRdpSndCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('channels', 'rdpsnd', "0")
        else:
            self.xrdp_ini_file.set('channels', 'rdpsnd', "true")
        self.xrdp_changed()
        self.useRdpSndCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def useDrDynVcChanged(self):
        if not self.xrdp_ini_file.has_option('channels', 'drdynvc'):
            self.xrdp_ini_file.set('channels', 'drdynvc', '0')
        if self.useDrDynVcCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('channels', 'drdynvc', "0")
        else:
            self.xrdp_ini_file.set('channels', 'drdynvc', "true")
        self.xrdp_changed()
        self.useDrDynVcCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def useClipRdrChanged(self):
        if not self.xrdp_ini_file.has_option('channels', 'cliprdr'):
            self.xrdp_ini_file.set('channels', 'cliprdr', '0')
        if self.useClipRdrCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('channels', 'cliprdr', "0")
        else:
            self.xrdp_ini_file.set('channels', 'cliprdr', "true")
        self.xrdp_changed()
        self.useClipRdrCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def useRAILChanged(self):
        if not self.xrdp_ini_file.has_option('channels', 'rail'):
            self.xrdp_ini_file.set('channels', 'rail', '0')
        if self.useRAILCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('channels', 'rail', "0")
        else:
            self.xrdp_ini_file.set('channels', 'rail', "true")
        self.xrdp_changed()
        self.useRAILCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def useXrdpVrChanged(self):
        if not self.xrdp_ini_file.has_option('channels', 'xrdpvr'):
            self.xrdp_ini_file.set('channels', 'xrdpvr', '0')
        if self.useXrdpVrCheckBox.checkState() == 0:
            self.xrdp_ini_file.set('channels', 'xrdpvr', "0")
        else:
            self.xrdp_ini_file.set('channels', 'xrdpvr', "true")
        self.xrdp_changed()
        self.useXrdpVrCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    # Add new Session...
    def newsession(self):
        if self.newsesswindow.newSessionName.isModified():
            tab_index = self.sessionsTab.count()
            new_sesssion_name = self.newsesswindow.newSessionName.displayText()
            self.createsessionstab(new_sesssion_name)
            self.addSessionName(tab_index, new_sesssion_name)
            self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox, 'enableOverridesCheckBox').clicked.connect(self.sessionOverridesEventHandler)
            self.sessionsTab.widget(tab_index).findChild(QtGui.QComboBox, 'serverbppcombobox').currentIndexChanged.connect(self.sessionbppcomboboxchanged)
            section_name = "xrdp" + str(tab_index + 1)
            self.sessionsTab.widget(tab_index).findChild(QtGui.QLabel, 'sessionSectionName').setText("[" + section_name + "]")
            # set default values for new session according to connection type...
            index = self.newsesswindow.connectionTypeComboBox.currentIndex()

            # X11rdp libxup.so
            if index == 0:
                self.addSessionLib(tab_index, "libxup.so")
                self.addSessionIP(tab_index, "127.0.0.1")
                self.addSessionPort(tab_index, "-1")
                self.addSessionUsername(tab_index, "ask")
                self.addSessionPassword(tab_index, "ask")
                # Also add new session to xrdp.ini ConfigParser object...
                self.xrdp_ini_file.add_section(section_name)
                self.xrdp_ini_file.set(section_name, "name", new_sesssion_name)
                self.xrdp_ini_file.set(section_name, "lib", "libxup.so")
                self.xrdp_ini_file.set(section_name, "ip", "127.0.0.1")
                self.xrdp_ini_file.set(section_name, "port", "-1")
                self.xrdp_ini_file.set(section_name, "username", "ask")
                self.xrdp_ini_file.set(section_name, "password", "ask")

            # sesman-Xvnc libvnc.so
            if index == 1:
                self.addSessionLib(tab_index, "libvnc.so")
                self.addSessionIP(tab_index, "127.0.0.1")
                self.addSessionPort(tab_index, "-1")
                self.addSessionUsername(tab_index, "ask")
                self.addSessionPassword(tab_index, "ask")
                # Also add new session to xrdp.ini ConfigParser object...
                self.xrdp_ini_file.add_section(section_name)
                self.xrdp_ini_file.set(section_name, "name", new_sesssion_name)
                self.xrdp_ini_file.set(section_name, "lib", "libvnc.so")
                self.xrdp_ini_file.set(section_name, "ip", "127.0.0.1")
                self.xrdp_ini_file.set(section_name, "port", "-1")
                self.xrdp_ini_file.set(section_name, "username", "ask")
                self.xrdp_ini_file.set(section_name, "password", "ask")

            # console libvnc.so
            if index == 2:
                self.addSessionLib(tab_index, "libvnc.so")
                self.addSessionIP(tab_index, "127.0.0.1")
                self.addSessionPort(tab_index, "5900")
                self.addSessionUsername(tab_index, "na")
                self.addSessionPassword(tab_index, "ask")
                # Also add new session to xrdp.ini ConfigParser object...
                self.xrdp_ini_file.add_section(section_name)
                self.xrdp_ini_file.set(section_name, "name", new_sesssion_name)
                self.xrdp_ini_file.set(section_name, "lib", "libvnc.so")
                self.xrdp_ini_file.set(section_name, "ip", "127.0.0.1")
                self.xrdp_ini_file.set(section_name, "port", "5900")
                self.xrdp_ini_file.set(section_name, "username", "na")
                self.xrdp_ini_file.set(section_name, "password", "ask")

            # vnc-any libvnc.so
            if index == 3:
                self.addSessionLib(tab_index, "libvnc.so")
                self.addSessionIP(tab_index, "ask")
                self.addSessionPort(tab_index, "ask5900")
                self.addSessionUsername(tab_index, "na")
                self.addSessionPassword(tab_index, "ask")
                # Also add new session to xrdp.ini ConfigParser object...
                self.xrdp_ini_file.add_section(section_name)
                self.xrdp_ini_file.set(section_name, "name", new_sesssion_name)
                self.xrdp_ini_file.set(section_name, "lib", "libvnc.so")
                self.xrdp_ini_file.set(section_name, "ip", "ask")
                self.xrdp_ini_file.set(section_name, "port", "ask5900")
                self.xrdp_ini_file.set(section_name, "username", "na")
                self.xrdp_ini_file.set(section_name, "password", "ask")

            # sesman-any libvnc.so
            if index == 4:
                self.addSessionLib(tab_index, "libvnc.so")
                self.addSessionIP(tab_index, "ask")
                self.addSessionPort(tab_index, "-1")
                self.addSessionUsername(tab_index, "ask")
                self.addSessionPassword(tab_index, "ask")
                # Also add new session to xrdp.ini ConfigParser object...
                self.xrdp_ini_file.add_section(section_name)
                self.xrdp_ini_file.set(section_name, "name", new_sesssion_name)
                self.xrdp_ini_file.set(section_name, "lib", "libvnc.so")
                self.xrdp_ini_file.set(section_name, "ip", "ask")
                self.xrdp_ini_file.set(section_name, "port", "-1")
                self.xrdp_ini_file.set(section_name, "username", "ask")
                self.xrdp_ini_file.set(section_name, "password", "ask")

            # rdp-any librdp.so
            if index == 5:
                self.addSessionLib(tab_index, "librdp.so")
                self.addSessionIP(tab_index, "ask")
                self.addSessionPort(tab_index, "ask3389")
                # Also add new session to xrdp.ini ConfigParser object...
                self.xrdp_ini_file.add_section(section_name)
                self.xrdp_ini_file.set(section_name, "name", new_sesssion_name)
                self.xrdp_ini_file.set(section_name, "lib", "librdp.so")
                self.xrdp_ini_file.set(section_name, "ip", "ask")
                self.xrdp_ini_file.set(section_name, "port", "ask3389")

            # freerdp libxrdpfreerdp1.so
            if index == 6:
                self.addSessionLib(tab_index, "libxrdpfreerdp1.so")
                self.addSessionIP(tab_index, "ask")
                self.addSessionPort(tab_index, "ask3389")
                self.addSessionUsername(tab_index, "ask")
                self.addSessionPassword(tab_index, "ask")
                # Also add new session to xrdp.ini ConfigParser object...
                self.xrdp_ini_file.add_section(section_name)
                self.xrdp_ini_file.set(section_name, "name", new_sesssion_name)
                self.xrdp_ini_file.set(section_name, "lib", "libxrdpfreerdp1.so")
                self.xrdp_ini_file.set(section_name, "ip", "ask")
                self.xrdp_ini_file.set(section_name, "port", "ask3389")
                self.xrdp_ini_file.set(section_name, "username", "ask")
                self.xrdp_ini_file.set(section_name, "password", "ask")

            # neutrinolabs libxrdpneutrinordp.so
            if index == 7:
                self.addSessionLib(tab_index, "libxrdpneutrinordp.so")
                self.addSessionIP(tab_index, "ask")
                self.addSessionPort(tab_index, "ask3389")
                self.addSessionUsername(tab_index, "ask")
                self.addSessionPassword(tab_index, "ask")
                # Also add new session to xrdp.ini ConfigParser object...
                self.xrdp_ini_file.add_section(section_name)
                self.xrdp_ini_file.set(section_name, "name", new_sesssion_name)
                self.xrdp_ini_file.set(section_name, "lib", "libxrdpneutrinordp.so")
                self.xrdp_ini_file.set(section_name, "ip", "ask")
                self.xrdp_ini_file.set(section_name, "port", "ask3389")
                self.xrdp_ini_file.set(section_name, "username", "ask")
                self.xrdp_ini_file.set(section_name, "password", "ask")
                # Lastly, update No. Of configured sessions counter..
            self.configuredSessionsLabel.setText(str(tab_index + 1))
            self.sessionsTab.setCurrentIndex(tab_index)

            self.newsesswindow.newSessionName.setText("")
            self.newsesswindow.newSessionName.setModified(False)
            self.newsesswindow.close()

            self.sessionsOverrideAddToArray(tab_index)

            self.sessionsOverrideUpdateActiveList(tab_index, "add")

            self.xrdp_changed()

    def reordersessiontabs(self, idx_from, *idx_to):
        if idx_to == ():
            return
        debugcheckbox = self.sessionsTab.widget(1).findChild(QtGui.QCheckBox, "debugXRDPCheckbox")
        tab_count = self.sessionsTab.count()
        if tab_count < 1:
            return
        xrdp_from = "xrdp" + str(idx_from + 1)
        xrdp_to = "xrdp" + str(idx_to[0] + 1)

        # step 1 - make a copy of xrdp_from
        xrdp_from_items = self.xrdp_ini_file.items(xrdp_from)
        xrdp_from_overrides = self.overridearray[idx_from]
        xrdp_from_override_enabled = self.sessions_channel_override_active_list[idx_from]

        # step 2 - make a copy of xrdp_to
        xrdp_to_items = self.xrdp_ini_file.items(xrdp_to)
        xrdp_to_overrides = self.overridearray[idx_to[0]]
        xrdp_to_override_enabled = self.sessions_channel_override_active_list[idx_to[0]]

        # step 3 - remove xrdp_from and to sections...
        self.xrdp_ini_file.remove_section(xrdp_from)
        self.xrdp_ini_file.remove_section(xrdp_to)

        # step 4 - create new xrdp_from section with contents of xrdp_to
        self.xrdp_ini_file.add_section(xrdp_from)
        for item in xrdp_to_items:
            self.xrdp_ini_file.set(xrdp_from, item[0], item[1])

        # step 5 - create new xrdp_to section with contents of xrdp_from
        self.xrdp_ini_file.add_section(xrdp_to)
        for item in xrdp_from_items:
            self.xrdp_ini_file.set(xrdp_to, item[0], item[1])

        # step 6 - update sessionsTab with new section names...
        self.sessionsTab.widget(idx_from).findChild(QtGui.QLabel, "sessionSectionName").setText("[" + xrdp_from + "]")
        self.sessionsTab.widget(idx_to[0]).findChild(QtGui.QLabel, "sessionSectionName").setText("[" + xrdp_to + "]")

        # step 7 - handle the debug checkbox stuff...

        # Debug was DISABLED and need to move the checkbox over...
        if (self.xrdp_debug_checkbox.checkState() != QtCore.Qt.CheckState.Checked) and (idx_from in (0, 1)) and (idx_to[0] in (0, 1)):
            self.xrdp_debug_checkbox.clicked.disconnect(self.debugClicked)
            debugcheckbox.setStyleSheet("")
            debugcheckbox.setVisible(False)
            self.xrdp_debug_checkbox = self.sessionsTab.widget(0).findChild(QtGui.QCheckBox, "debugXRDPCheckbox")
            self.xrdp_debug_checkbox.clicked.connect(self.debugClicked)
            self.xrdp_debug_checkbox.setVisible(True)

        # Debug was ENABLED and need to move the settings over...   
        if (self.xrdp_debug_checkbox.checkState() == QtCore.Qt.CheckState.Checked) and (idx_from in (0, 1)) and (idx_to[0] in (0, 1)):
            self.xrdp_debug_checkbox.clicked.disconnect(self.debugClicked)
            debugcheckbox.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.debugHandler(1, "xrdp2")
            debugcheckbox.setStyleSheet("")
            debugcheckbox.setVisible(False)
            self.xrdp_debug_checkbox = self.sessionsTab.widget(0).findChild(QtGui.QCheckBox, "debugXRDPCheckbox")
            self.xrdp_debug_checkbox.clicked.connect(self.debugClicked)
            self.xrdp_debug_checkbox.setVisible(True)
            self.xrdp_debug_checkbox.setCheckState(QtCore.Qt.CheckState.Checked)
            self.debugHandler(0, "xrdp1")

        # step 8 - swap the overridearray values over for the two sessions...
        self.overridearray[idx_to[0]] = xrdp_from_overrides
        self.overridearray[idx_from] = xrdp_to_overrides
        self.sessions_channel_override_active_list[idx_to[0]] = xrdp_from_override_enabled
        self.sessions_channel_override_active_list[idx_from] = xrdp_to_override_enabled

        # step 9 - resequence the [xrdp] sections in the INI file to keep it tidy.
        # Update the Autorun and modulebox (login sim) comboboxes as well...

        self.resequenceINI()

        # Also set AutoRun combobox index if autorun has been selected...
        if self.xrdp_ini_file.has_option('globals', 'autorun'):
            autorun_text = self.xrdp_ini_file.get('globals', 'autorun')
            for index in range(0, self.autoRunComboBox.count()):
                self.autoRunComboBox.setCurrentIndex(index)
                if autorun_text in self.autoRunComboBox.currentText():
                    break
        self.something_xrdp_changed = 1
        self.settitleforxrdp()

    def resequenceINI(self):
        tab_count = self.sessionsTab.count()
        self.resetAutorunComboBox()
        self.resetModuleBox()
        xrdpN_sections = []
        for index in range(0, tab_count):
            xrdpN_sections.append([])
            secname = "xrdp" + str((index + 1))
            items = self.xrdp_ini_file.items(secname)
            xrdpN_sections[index].append(items)
            self.xrdp_ini_file.remove_section(secname)
        for index in range(0, tab_count):
            secname = "xrdp" + str((index + 1))
            self.xrdp_ini_file.add_section(secname)
            items = xrdpN_sections[index]
            for item in items[0]:
                self.xrdp_ini_file.set(secname, item[0], item[1])
                if item[0] in "name":
                    self.autoRunComboBox.addItem(item[1])
                    self.simmodulebox.addItem(item[1])

    def deleteSession(self):
        tab_count = self.sessionsTab.count()
        if tab_count == 0:
            return
        index = self.sessionsTab.currentIndex()
        session_name = "xrdp" + str(index + 1)
        self.sessionsTab.removeTab(index)
        self.xrdp_ini_file.remove_section(session_name)
        self.autoRunComboBox.removeItem(index + 1)
        self.simmodulebox.removeItem(index)
        del self.overridearray[index]
        self.sessionsOverrideUpdateActiveList(index, "delete")
        if index < tab_count - 1:
            for sesnum in range(index, tab_count - 1):
                old_sesname = "xrdp" + str(sesnum + 2)
                new_sesname = "xrdp" + str(sesnum + 1)
                items = self.xrdp_ini_file.items(old_sesname)
                self.xrdp_ini_file.add_section(new_sesname)
                for item in items:
                    self.xrdp_ini_file.set(new_sesname, item[0], item[1])
                self.xrdp_ini_file.remove_section(old_sesname)
                self.sessionsTab.widget(sesnum).findChild(QtGui.QLabel, 'sessionSectionName').setText(
                    "[" + new_sesname + "]")
            if index == 0:
                self.setXrdpCheckboxVisibility()
        self.configuredSessionsLabel.setText(str(self.sessionsTab.count()))
        self.xrdp_changed()
        if self.sessionsTab.count() == 0:
            self.deleteSessionButton.setEnabled(False)

    def addNewSession(self):
        self.newsesswindow.buttonBox.rejected.connect(self.newsesswindow.close)
        self.newsesswindow.buttonBox.accepted.connect(self.newsession)
        self.newsesswindow.exec_()
        self.xrdp_changed()

    # End of event Handlers ^^^^^

    def showXrdpIniPage(self):
        if self.xrdp_ini_file_opened == 1:
            self.filenameFrame.setVisible(True)
            self.label_4.setVisible(True)
            self.configuredSessionsLabel.setVisible(True)
            self.nameOfOpenFile.setText(self.xrdpfilename)
            self.stackedWidget.setVisible(True)
            self.stackedWidget.setCurrentIndex(1)
            self.actionPreview.setEnabled(True)
            self.actionSave.setEnabled(True)
            self.actionSave_as.setEnabled(True)
            self.actionPreview.setEnabled(True)
            self.editingSesman = False
            self.editingXrdpIni = True
            self.menuPage.setEnabled(True)
            self.actionXrdp_ini.setEnabled(True)
            self.actionLogin_Window.setEnabled(True)
            if self.sesman_ini_file_opened == 0:
                self.actionSesman_ini.setEnabled(False)
            self.settitleforxrdp()

    def showLoginWindowSim(self):
        if self.xrdp_ini_file_opened:
            if self.editingSesman:
                self.showXrdpIniPage()
            self.winSim.show()
            self.winSim.raise_()

    def settitleforxrdp(self):
        title = "XRDPConfigurator : editing an xrdp.ini file."
        if self.something_xrdp_changed != 1:
            self.setWindowTitle(title)
        else:
            self.setWindowTitle("*" + title)

    def showSesmanIniPage(self):
        if self.sesman_ini_file_opened == 1:
            self.filenameFrame.setVisible(True)
            self.label_4.setVisible(False)
            self.nameOfOpenFile.setText(self.sesmanfilename)
            self.configuredSessionsLabel.setVisible(False)
            self.stackedWidget.setVisible(True)
            self.stackedWidget.setCurrentIndex(0)
            self.stackedWidget.setCurrentIndex(2)
            self.actionPreview.setEnabled(True)
            self.actionSave.setEnabled(True)
            self.actionSave_as.setEnabled(True)
            self.actionPreview.setEnabled(True)
            self.editingSesman = True
            self.editingXrdpIni = False
            self.actionSesman_ini.setEnabled(True)
            if self.xrdp_ini_file_opened == 0:
                self.actionXrdp_ini.setEnabled(False)
            self.settitleforsesman()

    def settitleforsesman(self):
        title = "XRDPConfigurator : editing a sesman.ini file."
        if self.something_sesman_changed != 1:
            self.setWindowTitle(title)
        else:
            self.setWindowTitle("*" + title)

    def fileSave(self):
        if self.editingSesman:
            self.fileSaveSesmanIni()
        elif self.editingXrdpIni:
            self.fileSaveXrdpIni()

    def fileSaveAs(self):
        if self.editingSesman:
            self.fileSaveSesmanIniAs()
        elif self.editingXrdpIni:
            self.fileSaveXrdpIniAs()

    # This function generates the header for the configfile to be saved...
    def ConfigFileGenerator(self, filetype):
        config = StringIO()
        config.write("# " + filetype + " configuration file.\n")
        config.write("# Generated by XRDPConfigurator v" + self.Version + "\n")
        config.write("#\n")
        config.write("# File creation date : " + strftime("%Y-%m-%d %H:%M:%S") + "\n")
        config.write("#\n")
        return config

    def fileSaveXrdpIni(self):
        config = self.ConfigFileGenerator("xrdp.ini")
        self.xrdp_ini_file.write(config, space_around_delimiters=False)
        try:
            with open(self.xrdp_ini_filename, 'w') as configfile:
                configfile.writelines(config.getvalue())
            configfile.close()
            self.something_xrdp_changed = 0
            self.settitleforxrdp()
        except PermissionError:
            message_window = InfoWindow(
                "<html><head/><body><p>You do not have permission to save the INI file.</p><p>Try saving to a different location.</p></body></html>")
            message_window.exec_()

    def fileSaveXrdpIniAs(self):
        fname = QtGui.QFileDialog.getSaveFileName(self, "Save file as...", "xrdp.ini", "Ini files (*.ini)")
        if fname[0] != "":
            config = self.ConfigFileGenerator("xrdp.ini")
            self.xrdp_ini_file.write(config, space_around_delimiters=False)
            try:
                with open(fname[0], 'w') as configfile:
                    configfile.writelines(config.getvalue())
                    configfile.close()
                    self.nameOfOpenFile.setText(fname[0])
                    self.xrdp_ini_filename = fname[0]
                    self.something_xrdp_changed = 0
                    self.settitleforxrdp()
            except PermissionError:
                message_window = InfoWindow("<html><head/><body><p>You do not have permission</p><p>to overwrite the INI file.</p></body></html>")
                message_window.exec_()

    def fileSaveSesmanIniAs(self):
        fname = QtGui.QFileDialog.getSaveFileName(self, "Save file as...", "sesman.ini", "Ini files (*.ini)")
        if fname[0] != "":
            config = self.ConfigFileGenerator("sesman.ini")
            self.sesman_ini_file.write(config, space_around_delimiters=False)
            try:
                with open(fname[0], 'w') as configfile:
                    configfile.writelines(config.getvalue())
                configfile.close()
                self.nameOfOpenFile.setText(fname[0])
                self.sesman_ini_filename = fname[0]
                self.something_sesman_changed = 0
                self.settitleforsesman()
            except PermissionError:
                message_window = InfoWindow(
                    "<html><head/><body><p>You do not have permission</p><p>to overwrite the INI file.</p></body></html>")
                message_window.exec_()

    def fileSaveSesmanIni(self):
        config = self.ConfigFileGenerator("sesman.ini")
        self.sesman_ini_file.write(config, space_around_delimiters=False)
        try:
            with open(self.sesman_ini_filename, 'w') as configfile:
                configfile.writelines(config.getvalue())
            configfile.close()
            self.something_sesman_changed = 0
            self.settitleforsesman()
        except PermissionError:
            message_window = InfoWindow(
                "<html><head/><body><p>You do not have permission to save the INI file.</p><p>Try saving to a different location.</p></body></html>")
            message_window.exec_()

    # User wants to quit...
    def fileQuit(self):
        if (self.something_xrdp_changed == 1) or (self.something_sesman_changed == 1):
            quit_window = AreYouSure(
                "<html><head/><body><p>You have unsaved changes.</p><p>Are you sure you want to quit?</p></body></html>")
            result = quit_window.exec_()
            if result == 1:
                QtGui.qApp.quit()
        else:
            QtGui.qApp.quit()

    # User wants to open xrdp.ini
    def fileOpenXrdpIni(self):
        if self.something_xrdp_changed:
            question = AreYouSure(
                "<html><head/><body><p>You have unsaved changes to the xrdp.ini file."
                "</p><p>Are you sure you want to open another file?</p></body></html>")
            result = question.exec_()
        else:
            result = 1
        if result == 1:
            filename = QtGui.QFileDialog.getOpenFileName(self, "Open xrdp.ini file...", "xrdp.ini", "Ini files (*.ini)")
            if filename[0] != "" and verifyXrdpIni(filename) is True:
                self.new_version_flag = 0
                self.xrdp_ini_filename = filename[0]
                self.parseXrdpIni(str(self.xrdp_ini_filename))
                self.something_xrdp_changed = 0
                self.settitleforxrdp()

    def xrdp_changed(self):
        #print("calling function : ", inspect.stack()[1][3])
        if self.something_xrdp_changed != 1:
            self.something_xrdp_changed = 1
            title = self.windowTitle()
            self.setWindowTitle("*" + title)

    def sesman_changed(self):
        if self.something_sesman_changed != 1:
            self.something_sesman_changed = 1
            title = self.windowTitle()
            self.setWindowTitle("*" + title)

    def fileOpenSesmanIni(self):
        if self.something_sesman_changed == 1:
            question = AreYouSure(
                "<html><head/><body><p>You have unsaved changes to the sesman.ini file."
                "</p><p>Are you sure you want to open another file?</p></body></html>")
            result = question.exec_()
        else:
            result = 1
        if result == 1:
            filename = QtGui.QFileDialog.getOpenFileName(self, "Open sesman.ini file...", "sesman.ini",
                                                         "Ini files (*.ini)")
            if filename[0] != "":
                if verifySesmanIni(filename[0]):
                    self.sesman_ini_filename = filename[0]
                    self.parseSesmanIni(str(self.sesman_ini_filename))
                    self.something_sesman_changed = 0
                    self.settitleforsesman()

    def updateMaxBppCombo(self, bpp):
        self.maxBppComboBox.blockSignals(True)
        if bpp == "8":
            self.maxBppComboBox.setCurrentIndex(0)
        if bpp == "15":
            self.maxBppComboBox.setCurrentIndex(1)
        if bpp == "16":
            self.maxBppComboBox.setCurrentIndex(2)
        if bpp == "24":
            self.maxBppComboBox.setCurrentIndex(3)
        self.maxBppComboBox.blockSignals(False)

    def updateCryptLevelCombo(self, cryptlevel):
        self.cryptLevelComboBox.blockSignals(True)
        if cryptlevel in ["low", "Low"]:
            self.cryptLevelComboBox.setCurrentIndex(0)
        if cryptlevel in ["medium", "Medium"]:
            self.cryptLevelComboBox.setCurrentIndex(1)
        if cryptlevel in ["high", "High"]:
            self.cryptLevelComboBox.setCurrentIndex(2)
        self.cryptLevelComboBox.blockSignals(False)

    # Event Handlers for Session Tabs Updates start here...

    def tabUserPasswordToggle(self, tabID, makeVisible):
        section_name = "xrdp" + str(tabID + 1)
        lib_widget = self.sessionsTab.widget(tabID).findChild(QtGui.QComboBox, "libraryComboBox")
        if not lib_widget:
            return
        username_widget = self.sessionsTab.widget(tabID).findChild(QtGui.QLabel, "label_4")
        username_entrybox = self.sessionsTab.widget(tabID).findChild(QtGui.QLineEdit, "sessionUserNameEntryBox")
        password_label = self.sessionsTab.widget(tabID).findChild(QtGui.QLabel, "label_8")
        password_entrybox = self.sessionsTab.widget(tabID).findChild(QtGui.QLineEdit, "sessionPasswordEntryBox")
        if makeVisible == 0:
            username_widget.setVisible(False)
            username_entrybox.setVisible(False)
            password_label.setVisible(False)
            password_entrybox.setVisible(False)
            if self.xrdp_ini_file.has_option(section_name, "username"):
                self.xrdp_ini_file.remove_option(section_name, "username")
            if self.xrdp_ini_file.has_option(section_name, "password"):
                self.xrdp_ini_file.remove_option(section_name, "password")
        if makeVisible == 1:
            username_widget.setVisible(True)
            username_entrybox.setVisible(True)
            password_label.setVisible(True)
            password_entrybox.setVisible(True)
            self.xrdp_ini_file.set(section_name, "username", "ask")
            self.xrdp_ini_file.set(section_name, "password", "ask")

    def setCodeTen(self, section, set_to):  # Adds or removes "code=10" depending on library used.
        if set_to == 0:  # Remove "code=10"
            if self.xrdp_ini_file.has_option(section, 'code'):
                self.xrdp_ini_file.remove_option(section, 'code')
        if set_to == 1:  # Add "code=10"
            if not self.xrdp_ini_file.has_option(section, 'code'):
                self.xrdp_ini_file.set(section, 'code', '10')

    # noinspection PyUnusedLocal
    def tabLibraryComboBoxChanged(self, arg):
        tabID = self.sessionsTab.currentIndex()
        lib_widget = self.sessionsTab.widget(tabID).findChild(QtGui.QComboBox, "libraryComboBox")
        library = ""
        section = "xrdp" + str(tabID + 1)
        index = lib_widget.currentIndex()
        if index == 0:
            library = "libxup.so"
            self.setCodeTen(section, 1)
        if index == 1:
            library = "libvnc.so"
            self.setCodeTen(section, 0)
        if index == 2:
            library = "librdp.so"
            self.setCodeTen(section, 0)
        if index == 3:
            library = "libxrdpfreerdp1.so"
            self.setCodeTen(section, 0)
        if index == 4:
            library = "libxrdpneutrinordp.so"
            self.setCodeTen(section, 0)
        if "librdp.so" in library:
            self.tabUserPasswordToggle(tabID, 0)
        else:
            self.tabUserPasswordToggle(tabID, 1)
        self.xrdp_ini_file.set(section, "lib", library)
        self.xrdp_changed()
        lib_widget.setStyleSheet(self.combobox_changed_stylesheet)

    # noinspection PyUnusedLocal
    def sessionbppcomboboxchanged(self, arg):
        tabID = self.sessionsTab.currentIndex()
        widget = self.sessionsTab.widget(tabID).findChild(QtGui.QComboBox, 'serverbppcombobox')
        section = "xrdp" + str(tabID + 1)
        index = widget.currentIndex()
        if index != 0:
            self.xrdp_ini_file.set(section, 'xserverbpp', widget.currentText())
        else:
            self.xrdp_ini_file.remove_option(section, 'xserverbpp')
        widget.setStyleSheet(self.combobox_changed_stylesheet)
        self.xrdp_changed()
        widget.setStyleSheet(self.combobox_changed_stylesheet)

    def sessionNameBoxChanged(self):
        tabID = self.sessionsTab.currentIndex()
        sessname_widget = self.sessionsTab.widget(tabID).findChild(QtGui.QLineEdit, "sessionNameBox")
        if not sessname_widget:
            return
        if sessname_widget.isModified():
            section = "xrdp" + str(tabID + 1)
            name = sessname_widget.text()
            self.sessionsTab.setTabText(tabID, name)
            self.autoRunComboBox.setItemText((tabID + 1), name)
            self.simmodulebox.setItemText(tabID, name)  # Login sim list
            self.xrdp_ini_file.set(section, "name", name)
            if self.xrdp_ini_file.has_option('globals', 'autorun'):
                if self.xrdp_ini_file.get('globals', 'autorun') != name:
                    self.xrdp_ini_file.set('globals', 'autorun', name)
            sessname_widget.setStyleSheet(self.line_edit_changed_stylesheet)
            self.xrdp_changed()
            sessname_widget.setModified(0)

    def sessionIPAddressChanged(self):
        tabID = self.sessionsTab.currentIndex()
        sess_ip_widget = self.sessionsTab.widget(tabID).findChild(QtGui.QLineEdit, "sessionIPAddress")
        if not sess_ip_widget:
            return
        if sess_ip_widget.isModified():
            section = "xrdp" + str(tabID + 1)
            address = sess_ip_widget.text()
            self.xrdp_ini_file.set(section, "ip", address)
            sess_ip_widget.setStyleSheet(self.line_edit_changed_stylesheet)
            self.xrdp_changed()
            sess_ip_widget.setModified(0)

    def sessionPortBoxChanged(self):
        tabID = self.sessionsTab.currentIndex()
        sess_port_widget = self.sessionsTab.widget(tabID).findChild(QtGui.QLineEdit, "sessionPortEntryBox")
        if sess_port_widget is None:
            return
        if sess_port_widget.isModified():
            section = "xrdp" + str(tabID + 1)
            port = sess_port_widget.text()
            self.xrdp_ini_file.set(section, "port", port)
            sess_port_widget.setStyleSheet(self.line_edit_changed_stylesheet)
            self.xrdp_changed()
            sess_port_widget.setModified(0)

    def sessionUsernameBoxChanged(self):
        tabID = self.sessionsTab.currentIndex()
        sess_username_widget = self.sessionsTab.widget(tabID).findChild(QtGui.QLineEdit, "sessionUserNameEntryBox")
        if sess_username_widget is None:
            return
        if sess_username_widget.isModified():
            section = "xrdp" + str(tabID + 1)
            username = sess_username_widget.text()
            self.xrdp_ini_file.set(section, "username", username)
            sess_username_widget.setStyleSheet(self.line_edit_changed_stylesheet)
            self.xrdp_changed()
            sess_username_widget.setModified(0)

    def sessionPasswordBoxChanged(self):
        tabID = self.sessionsTab.currentIndex()
        sess_password_widget = self.sessionsTab.widget(tabID).findChild(QtGui.QLineEdit, "sessionPasswordEntryBox")
        if sess_password_widget is None:
            return
        if sess_password_widget.isModified():
            section = "xrdp" + str(tabID + 1)
            password = sess_password_widget.text()
            self.xrdp_ini_file.set(section, "password", password)
            sess_password_widget.setStyleSheet(self.line_edit_changed_stylesheet)
            self.xrdp_changed()
            sess_password_widget.setModified(0)

    # Channel overrides event handler...
    def sessionOverridesEventHandler(self):
        #listIndex = 0
        tabID = self.sessionsTab.currentIndex()
        section = "xrdp" + str(tabID + 1)
        enable_overrides = self.sessionsTab.widget(tabID).findChild(QtGui.QCheckBox, 'enableOverridesCheckBox')
        channelsFrame = self.sessionsTab.widget(tabID).findChild(QtGui.QFrame, 'channelsFrame')
        # If we can't find the Enable Overrides checkbox then give up...
        if enable_overrides is None:
            return
        # If a session's Enable Channel Overrides checkbox is ticked...
        if enable_overrides.checkState() == 2:
            # If channelsFrame isn't already enabled,
            # Then enable the overrides frame for that session, making the tickboxes clickable...
            if not channelsFrame.isEnabled():
                channelsFrame.setEnabled(True)
            self.sessionOverridesTicked(section, tabID)
        else:  # IF ENABLE_OVERRIDES IS UNCHECKED...
            self.sessionOverridesUnticked(section, tabID)
            channelsFrame.setEnabled(False)
        self.sessionsOverrideUpdateActiveList(tabID, "update")
        self.xrdp_changed()
        enable_overrides.setStyleSheet(self.checkbox_changed_stylesheet)

    # User has ticked the session's Enable Channel Override tick box...
    def sessionOverridesTicked(self, section, tabID):
        #print("Session Overrides were already enabled for tabID", tabID, ",section",section)
        listIndex = 0
        # For each of the globals channel names, session channel names, and the Qt checkbox name
        # in the SESSIONOVERRIDESLIST array...
        for globals_channel_name, session_channel_name, checkbox_name in self.SESSIONOVERRIDESLIST:
            # If the channel override doesn't exist in INI file, then add that option
            # then set the tick state of each tick box, then update the override array to suit...
            if not self.xrdp_ini_file.has_option(section, session_channel_name):
                # Get the enabled/disabled state of each of the global channel settings...
                global_channel_state = self.xrdp_ini_file.get('channels', globals_channel_name)
                # set the INI file's corresponding  session override to be the same...
                self.xrdp_ini_file.set(section, session_channel_name, global_channel_state)
                # set the overridearray list to reflect that...
                self.sessionOverrideChannelState(section, tabID, session_channel_name, checkbox_name)
                session_channel_tickbox_state = self.sessionsTab.widget(tabID).findChild(QtGui.QCheckBox, checkbox_name).checkState()
                if session_channel_tickbox_state == 2:
                    self.overridearray[tabID][listIndex] = 2
                elif session_channel_tickbox_state == 0:
                    self.overridearray[tabID][listIndex] = 0
            else:
                # If the channel override option is already in the INI file, then look at the option, and
                # tick or untick the relevent checkbox...
                session_channel_tickbox = self.sessionsTab.widget(tabID).findChild(QtGui.QCheckBox, checkbox_name)
                session_channel_tickbox_state = int(session_channel_tickbox.checkState())
                override_array_state = self.overridearray[tabID][listIndex]
                if session_channel_tickbox_state == 2:
                    self.xrdp_ini_file.set(section, session_channel_name, 'true')
                else:
                    self.xrdp_ini_file.set(section, session_channel_name, '0')
                if override_array_state != session_channel_tickbox_state:
                    # If the Session's old state was unchecked, don't update the stylesheet
                    # because we're merely enabling the overrides and setting or unsetting the
                    # relevent checkbox according to the corresponding Global channels settings...
                    if self.sessions_channel_override_active_list[tabID] == 1:
                        session_channel_tickbox.setStyleSheet(self.checkbox_changed_stylesheet)
                    if session_channel_tickbox_state == 2:
                        self.overridearray[tabID][listIndex] = 2
                    elif session_channel_tickbox_state == 0:
                        self.overridearray[tabID][listIndex] = 0

                self.sessionOverrideChannelState(section, tabID, session_channel_name, checkbox_name)
            listIndex += 1

    # User has un-ticked the session's Enable Channel Overrides box...
    def sessionOverridesUnticked(self, section, tabID):
        listIndex = 0
        for globals_channel_name, session_channel_name, checkbox_name in self.SESSIONOVERRIDESLIST:
            if self.xrdp_ini_file.has_option(section, session_channel_name):
                # Remove the channel override option from the section...
                self.xrdp_ini_file.remove_option(section, session_channel_name)
                # Untick the corresponding tickbox...
                self.sessionsTab.widget(tabID).findChild(QtGui.QCheckBox, checkbox_name).setCheckState(QtCore.Qt.CheckState(0))
                # Set the corresponding tickboxe's stylesheet back to its default...
                self.sessionsTab.widget(tabID).findChild(QtGui.QCheckBox, checkbox_name).setStyleSheet("")
                # set the value of the channel overrides array to the checked/unchecked value...
                self.overridearray[tabID][listIndex] = 0
                self.sessions_channel_override_active_list[tabID] = 0
                listIndex += 1

    def sessionOverrideChannelState(self, section, tabID, channel, checkbox):
        if self.xrdp_ini_file.get(section, channel) == '0':
            self.sessionsTab.widget(tabID).findChild(QtGui.QCheckBox, checkbox).setCheckState(QtCore.Qt.CheckState(0))
        if self.xrdp_ini_file.get(section, channel) == 'true':
            self.sessionsTab.widget(tabID).findChild(QtGui.QCheckBox, checkbox).setCheckState(QtCore.Qt.CheckState(2))

    # We keep tabs (heh cwutididthar!) on which session has Enable Channel Overrides ticked or unticked.
    # @param tab_index: The index/id of the session's tab being updated
    # @param option: whether to /add/ to the array, /update/ an existing entry, or /remove/ one
    def sessionsOverrideUpdateActiveList(self, tab_index, option):
        if option == "add":
            self.sessions_channel_override_active_list.append([])
            # Update the list of sessions with channel overrides - to be used when checking old value if user clicks checkbox...
            if self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                            "enableOverridesCheckBox").checkState() == 2:
                self.sessions_channel_override_active_list[tab_index] = 1
            else:
                self.sessions_channel_override_active_list[tab_index] = 0
            self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox, 'enableOverridesCheckBox').clicked.connect(
                self.sessionOverridesEventHandler)
        if option == "update":
            overridescheckbox = self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox, 'enableOverridesCheckBox')
            if overridescheckbox.checkState() == 2:
                self.sessions_channel_override_active_list[tab_index] = 1
            else:
                self.sessions_channel_override_active_list[tab_index] = 0
        if option == "delete":
            del self.sessions_channel_override_active_list[tab_index]

    # This function gets called whenever a new session is added either by reading in an INI file, or by the user.
    # It appends a new set of override states (0=disabled, 2=enabled) to the array self.overridearray.
    def sessionsOverrideAddToArray(self, tab_index):
        # NEW IMPROVED ARRAY[tm] ...
        self.overridearray.append([])
        # For each channel in the CHANNEL_LIST array...
        for override_channel_name in self.CHANNEL_LIST:
            # Find the widget with that channel name...
            widget = self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox, override_channel_name)
            if widget.checkState() == 2:
                self.overridearray[tab_index].append(2)
            else:
                self.overridearray[tab_index].append(0)
            self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox, override_channel_name).clicked.connect(
                self.sessionOverridesEventHandler)

    # ###END OF SESSIONS EVENT HANDLERS###

    # CUSTOMIZATION Page Starts Here (a.k.a. Login Simulator Page....

    # This function gets called any time the mouse enters one of the desired
    # Login Simulator Buttons...
    #def eventFilter(self, obj, event):
    #    txt = obj.text()
    #    if event.type() == QtCore.QEvent.Enter:
    #        if txt == "Background" and self.hilight_background_running == 0:
    #            with futures.ThreadPoolExecutor(max_workers=1) as executor:
    #                self.hl_bground = executor.submit(self.hilightBackground())
    #        if txt == "Text" and self.highlight_text_running == 0:
    #            with futures.ThreadPoolExecutor(max_workers=1) as executor:
    #                executor.submit(self.hilightText())
    #        return True
    #    else:
    #        return False

    @staticmethod
    def createBoxShadeLines(parent_widget, boxlength=210, xpos=200, ypos=200):
        # Adds Shadelines to the various boxes

        pen_width = 1

        pen = QtGui.QPen(QtGui.QColor(128, 128, 128))
        pen.setWidth(pen_width)
        topline = QtGui.QGraphicsLineItem(parent=parent_widget)
        topline.setPen(pen)
        topline.setLine(xpos, ypos, xpos + boxlength, ypos)

        pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        pen.setWidth(1)
        topline2 = QtGui.QGraphicsLineItem(parent=parent_widget)
        topline2.setPen(pen)
        topline2.setLine(xpos + 1, ypos + 1, xpos + boxlength - 1, ypos + 1)

        pen = QtGui.QPen(QtGui.QColor(128, 128, 128))
        pen.setWidth(1)
        leftline = QtGui.QGraphicsLineItem(parent=parent_widget)
        leftline.setPen(pen)
        leftline.setLine(xpos, ypos, xpos, ypos + 17)

        pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        pen.setWidth(1)
        leftline2 = QtGui.QGraphicsLineItem(parent=parent_widget)
        leftline2.setPen(pen)
        leftline2.setLine(xpos + 1, ypos + 1, xpos + 1, ypos + 1 + 17)

        bottomline = QtGui.QGraphicsLineItem(parent=parent_widget)
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255))
        bottomline.setPen(pen)
        bottomline.setLine(xpos, ypos + 18, xpos + boxlength, ypos + 18)

        rightline = QtGui.QGraphicsLineItem(parent=parent_widget)
        rightline.setPen(pen)
        rightline.setLine(xpos + boxlength, ypos, xpos + boxlength, ypos + 18)

        return topline, topline2, leftline, leftline2, rightline, bottomline

    @staticmethod
    def hideWinSim():
        winSim.hide()

    def setupWinSimButtonConnections(self):
        self.winSim = winSim
        #        winSim.CloseBtn.clicked.connect(self.hideWinSim)
        winSim.background_Pushbutton.clicked.connect(self.loginSimulatorSelectBackground)
        winSim.resetBackgroundButton.clicked.connect(self.resetToDefaultBackground)
        winSim.grey_Pushbutton.clicked.connect(self.loginSimulatorSelectGrey)
        winSim.resetWindowButton.clicked.connect(self.resetGrey)
        winSim.blue_Pushbutton.clicked.connect(self.loginSimulatorSelectBlue)
        winSim.resetTitleBgndButton.clicked.connect(self.resetBlue)
        winSim.black_Pushbutton.clicked.connect(self.loginSimulatorSelectBlack)
        winSim.resetTextButton.clicked.connect(self.resetBlack)
        winSim.dark_blue_Pushbutton.clicked.connect(self.loginSimulatorSelectDarkBlue)
        winSim.resetSessionBoxHilightBtn.clicked.connect(self.resetDarkBlue)
        winSim.white_Pushbutton.clicked.connect(self.loginSimulatorSelectWhite)
        winSim.resetTopLeftTitleBoxesBtn.clicked.connect(self.resetWhite)
        winSim.dark_grey_Pushbutton.clicked.connect(self.loginSimulatorSelectDarkGrey)
        winSim.resetBottomRightBtn.clicked.connect(self.resetDarkGrey)
        winSim.resizeDialogBtn.clicked.connect(self.windowDialogResizeClicked)
        winSim.boxesLocationBtn.clicked.connect(self.windowDialogBoxesBtnClicked)
        winSim.logoPositionBtn.clicked.connect(self.windowLogoPositionClicked)
        winSim.buttonsLocationBtn.clicked.connect(self.windowDialogButtonsCustBtnClicked)
        winSim.closeWinSimBtn.clicked.connect(self.hideWinSim)
        winSim.previewINIBtn.clicked.connect(self.xrdpIniPreview)

    def setupWinSim(self):
        self.x_pos = 0
        self.y_pos = 0
        self.okbtn_width = 60
        self.okbtn_height = 23
        self.cancelbtn_width = 60
        self.cancelbtn_height = 23
        self.helpbtn_width = 60
        self.helpbtn_height = 23
        self.dialog_width = 400
        self.dialog_height = 200

        # Set the location and dimensions of the Module, username, password labels and boxes
        self.mod_text_xpos = self.x_pos + 150
        self.mod_text_ypos = self.y_pos + 30
        self.mod_box_xpos = self.mod_text_xpos + 80
        self.mod_box_ypos = self.mod_text_ypos + 7

        self.user_text_xpos = self.x_pos + 150
        self.user_text_ypos = self.y_pos + 56
        self.user_box_xpos = self.user_text_xpos + 80
        self.user_box_ypos = self.user_text_ypos + 7

        self.pass_text_xpos = self.x_pos + 150
        self.pass_text_ypos = self.y_pos + 82
        self.pass_box_xpos = self.pass_text_xpos + 80
        self.pass_box_ypos = self.pass_text_ypos + 7

        self.boxlength = 140

        # Set the location and dimensions of the Ok, Cancel, and Help buttons...
        self.okbtn_xpos = self.x_pos + 180
        self.okbtn_ypos = self.y_pos + 163

        self.cancelbtn_xpos = self.x_pos + 250
        self.cancelbtn_ypos = self.y_pos + 163

        self.helpbtn_xpos = self.x_pos + 320
        self.helpbtn_ypos = self.y_pos + 163

        # Font to be used is Sans 10, no antialiasing, to match the real login window...
        font = QtGui.QFont()
        font.setFamily("Sans")
        font.setPointSize(10)
        font.setStyleStrategy(QtGui.QFont.NoAntialias)

        pen_width = 1

        modtext = "Module"

        dialog_colour = QtGui.QColor(195, 195, 195)

        if self.new_version_flag:
            modtext = "Session"
            self.winSim.DialogGroupBox.setVisible(True)

            if self.xrdp_ini_file.has_option('globals', 'ls_input_width'):
                self.boxlength = int(self.xrdp_ini_file.get('globals', 'ls_input_width'))
            if self.xrdp_ini_file.has_option('globals', 'ls_width'):
                self.dialog_width = int(self.xrdp_ini_file.get('globals', 'ls_width'))
            if self.xrdp_ini_file.has_option('globals', 'ls_height'):
                self.dialog_height = int(self.xrdp_ini_file.get('globals', 'ls_height'))
            if self.xrdp_ini_file.has_option('globals', 'ls_label_x_pos'):
                self.mod_text_xpos = int(self.xrdp_ini_file.get('globals', 'ls_label_x_pos'))
                self.mod_text_ypos = int(self.xrdp_ini_file.get('globals', 'ls_input_y_pos'))
                self.updateDialogCalculateLabelBoxesPositions()
            if self.xrdp_ini_file.has_option('globals', 'ls_btn_ok_x_pos'):
                self.okbtn_xpos = int(self.xrdp_ini_file.get('globals', 'ls_btn_ok_x_pos'))
                self.okbtn_ypos = int(self.xrdp_ini_file.get('globals', 'ls_btn_ok_y_pos'))
                self.okbtn_width = int(self.xrdp_ini_file.get('globals', 'ls_btn_ok_width'))
                self.okbtn_height = int(self.xrdp_ini_file.get('globals', 'ls_btn_ok_height'))
                self.cancelbtn_xpos = int(self.xrdp_ini_file.get('globals', 'ls_btn_cancel_x_pos'))
                self.cancelbtn_ypos = int(self.xrdp_ini_file.get('globals', 'ls_btn_cancel_y_pos'))
                self.cancelbtn_width = int(self.xrdp_ini_file.get('globals', 'ls_btn_cancel_width'))
                self.cancelbtn_height = int(self.xrdp_ini_file.get('globals', 'ls_btn_cancel_height'))
            if self.xrdp_ini_file.has_option('globals', 'ls_logo_x_pos'):
                self.logo_xpos = int(self.xrdp_ini_file.get('globals', 'ls_logo_x_pos'))
                self.logo_ypos = int(self.xrdp_ini_file.get('globals', 'ls_logo_y_pos'))
                self.logo_filename = self.xrdp_ini_file.get('globals', 'ls_logo_filename')
        else:
            self.winSim.DialogGroupBox.setVisible(False)

        # WINSIM Set up the view and scene for the login window area...
        self.simscene = QtGui.QGraphicsScene()
        self.simscene.setSceneRect(QtCore.QRectF(self.winSim.xrdp_window.viewport().rect()))
        self.winSim.resized.connect(self.winSimResized)
        self.winSim.xrdp_window.setScene(self.simscene)
        self.winSim.xrdp_window.setRenderHints(QtGui.QPainter.CompositionMode_Destination)
        self.winSim.xrdp_window.scale(1, 1)

        # these views are for the various colour "swatches"...
        self.simbackgroundscene = QtGui.QGraphicsScene()
        self.simbackgroundscene.setSceneRect(QtCore.QRectF(self.winSim.backgroundView.viewport().rect()))
        self.winSim.backgroundView.setScene(self.simbackgroundscene)

        self.simwindowscene = QtGui.QGraphicsScene()
        self.simwindowscene.setSceneRect(QtCore.QRectF(self.winSim.windowView.viewport().rect()))
        self.winSim.windowView.setScene(self.simwindowscene)

        self.simtitleBgndscene = QtGui.QGraphicsScene()
        self.simtitleBgndscene.setSceneRect(QtCore.QRectF(self.winSim.titleBgndView.viewport().rect()))
        self.winSim.titleBgndView.setScene(self.simtitleBgndscene)

        self.simtextscene = QtGui.QGraphicsScene()
        self.simtextscene.setSceneRect(QtCore.QRectF(self.winSim.textView.viewport().rect()))
        self.winSim.textView.setScene(self.simtextscene)

        self.simboxesscene = QtGui.QGraphicsScene()
        self.simboxesscene.setSceneRect(QtCore.QRectF(self.winSim.boxesView.viewport().rect()))
        self.winSim.boxesView.setScene(self.simboxesscene)

        self.simbotRightscene = QtGui.QGraphicsScene()
        self.simbotRightscene.setSceneRect(QtCore.QRectF(self.winSim.botRightView.viewport().rect()))
        self.winSim.botRightView.setScene(self.simbotRightscene)

        self.simdarkBluescene = QtGui.QGraphicsScene()
        self.simdarkBluescene.setSceneRect(QtCore.QRectF(self.winSim.darkBlueView.viewport().rect()))
        self.winSim.darkBlueView.setScene(self.simdarkBluescene)

        self.dark_blue = QtGui.QColor(0, 0, 127)
        self.winSim.darkBlueView.setBackgroundBrush(QtGui.QBrush(self.dark_blue))

        # Create items group
        self.simlogin_window_group = LoginWindowGroup(self.winSim.xrdp_window.sceneRect())

        # Set up the default background...
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.winSim.xrdp_window.setBackgroundBrush(brush)
        self.winSim.backgroundView.setBackgroundBrush(brush)
        self.simloginwindow = LoginWindow()
        self.simnewloginrect = self.simloginwindow.createDialog(self.x_pos, self.y_pos, self.dialog_width,
                                                                self.dialog_height, dialog_colour, 1, self.new_version_flag)
        self.simscene.addItem(self.simloginwindow.loginrect)
        self.simarrow = self.simscene.addWidget(self.simloginwindow.resizearrow)
        self.simloginwindow.resizeInvisible()

        dialog_brush = QtGui.QBrush(dialog_colour)
        self.winSim.windowView.setBackgroundBrush(dialog_brush)

        pen = QtGui.QPen(QtGui.QColor(255, 255, 255))
        pen.setWidth(pen_width)
        self.winSim.boxesView.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255)))

        pen = QtGui.QPen(QtGui.QColor(128, 128, 128))
        pen.setWidth(pen_width)
        self.winSim.botRightView.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(128, 128, 128)))

        # Create the Module/Session text
        self.simmoduletext = QtGui.QGraphicsTextItem(parent=self.simnewloginrect)
        self.simmoduletext.setFont(font)
        self.simmoduletext.setDefaultTextColor(QtGui.QColor(0, 0, 0))
        self.simmoduletext.setPlainText(modtext)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        self.winSim.textView.setBackgroundBrush(brush)

        # Create the "username" text
        self.simusernametext = QtGui.QGraphicsTextItem(parent=self.simnewloginrect)
        self.simusernametext.setFont(font)
        self.simusernametext.setDefaultTextColor(QtGui.QColor(0, 0, 0))
        self.simusernametext.setPlainText("username")

        # Create the "password" text
        self.simpasswordtext = QtGui.QGraphicsTextItem(parent=self.simnewloginrect)
        self.simpasswordtext.setFont(font)
        self.simpasswordtext.setDefaultTextColor(QtGui.QColor(0, 0, 0))
        self.simpasswordtext.setPlainText("password")

        # Draw them
        #self.windowDialogSetLabelsPosition()
        self.simmoduletext.setPos(self.mod_text_xpos, self.mod_text_ypos)
        self.simusernametext.setPos(self.user_text_xpos, self.user_text_ypos)
        self.simpasswordtext.setPos(self.pass_text_xpos, self.pass_text_ypos)

        # Add a text entry box for "username"...
        textcolour = QtGui.QColor(self.simmoduletext.defaultTextColor()).name()
        boxes = QtGui.QColor(self.simloginwindow.topline.pen().color()).name()
        stylesheet = 'QLineEdit { ' \
                    'color: ' + textcolour + '; ' \
                    'background: ' + boxes + '; ' \
                    'padding: 0px; ' \
                    '} '
        self.simusernamebox = QtGui.QLineEdit()
        self.simusernamebox.setFrame(False)
        self.simusernamebox.setFont(font)
        self.simusernamebox.setStyleSheet(stylesheet)
        self.simusernamebox.setGeometry(
            QtCore.QRect(self.user_box_xpos + 2, self.user_box_ypos + 2, self.boxlength - 1, 13))

        # Add Shading to username entrybox...
        self.simuserShading = BoxShades(self.simloginwindow.loginrect, self.boxlength + 1, self.user_box_xpos,
                                        self.user_box_ypos)
        self.simlogin_window_group.addToGroup(self.simuserShading)

        # Add a text entry box for "password"...
        self.simpassbox = QtGui.QLineEdit()
        self.simpassbox.setGeometry(
            QtCore.QRect(self.pass_box_xpos + 2, self.pass_box_ypos + 2, self.boxlength - 1, 13))
        self.simpassbox.setFrame(False)
        self.simpassbox.setFont(font)
        self.simpassbox.setEchoMode(QtGui.QLineEdit.Password)
        stylesheet = 'QLineEdit { ' \
                     'lineedit-password-character: 42;' \
                     'color: ' + textcolour + '; ' \
                     'background: ' + boxes + '; ' \
                     'padding: 0px; ' \
                     'margin: 0px;' \
                     'border: 0px;' \
                     '}'
        self.simpassbox.setStyleSheet(stylesheet)

        # Add Shading to password entrybox...
        self.simpassShading = BoxShades(self.simloginwindow.loginrect, self.boxlength + 1, self.pass_box_xpos,
                                        self.pass_box_ypos)
        self.simlogin_window_group.addToGroup(self.simpassShading)

        # Add an OK button...
        self.simokbtn = QtGui.QPushButton()
        self.simokbtn.setStyle(QtGui.QStyleFactory.create("windows"))
        self.simokbtn.setGeometry(self.okbtn_xpos, self.okbtn_ypos, self.okbtn_width, self.okbtn_height)
        self.simokbtn.setFont(font)
        self.simokbtn.setText("OK")
        self.simokbtn.setAutoFillBackground(True)

        #        self.okbottomline = QtGui.QGraphicsLineItem()
        #        self.okbottomline.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        #        self.okbottomline.setLine(self.x_pos + 279, self.y_pos + 210 + self.button_height, self.x_pos + 279 + self.button_length, self.y_pos + 210 + self.button_height)
        #        self.login_window_group.addToGroup(self.okbottomline)
        #        self.okrightline = QtGui.QGraphicsLineItem()
        #        self.okrightline.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        #        self.okrightline.setLine(self.x_pos + 279 + self.button_length, self.y_pos + 210 + self.button_height, self.x_pos + 279 + self.button_length, self.y_pos + 210)
        #        self.login_window_group.addToGroup(self.okrightline)

        # Add a Cancel button...
        self.simcancelbtn = QtGui.QPushButton()
        self.simcancelbtn.setStyle(QtGui.QStyleFactory.create("windows"))
        self.simcancelbtn.setGeometry(self.cancelbtn_xpos, self.cancelbtn_ypos, self.cancelbtn_width,
                                      self.cancelbtn_height)
        self.simcancelbtn.setFont(font)
        self.simcancelbtn.setText("Cancel")
        self.simcancelbtn.setAutoFillBackground(True)

        #        self.cancelbottomline = QtGui.QGraphicsLineItem()
        #        self.cancelbottomline.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        #        self.cancelbottomline.setLine(self.x_pos + 348, self.y_pos + 210 + self.button_height, self.x_pos + 348 + self.button_length, self.y_pos + 210 + self.button_height)
        #        self.login_window_group.addToGroup(self.cancelbottomline)
        #        self.cancelrightline = QtGui.QGraphicsLineItem()
        #        self.cancelrightline.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        #        self.cancelrightline.setLine(self.x_pos + 348 + self.button_length, self.y_pos + 210 + self.button_height, self.x_pos + 348 + self.button_length, self.y_pos + 210)
        #        self.login_window_group.addToGroup(self.cancelrightline)

        # Add a Help button...
        if not self.new_version_flag:
            self.simhelpbtn = QtGui.QPushButton()
            self.simhelpbtn.setStyle(QtGui.QStyleFactory.create("windows"))
            self.simhelpbtn.setGeometry(self.helpbtn_xpos, self.okbtn_ypos, self.okbtn_width, self.okbtn_height)
            self.simhelpbtn.setFont(font)
            self.simhelpbtn.setText("Help")
            self.simhelpbtn.setAutoFillBackground(True)

        #        self.helpbottomline = QtGui.QGraphicsLineItem()
        #        self.helpbottomline.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        #        self.helpbottomline.setLine(self.x_pos + 418, self.y_pos + 210 + self.button_height, self.x_pos + 418 + self.button_length, self.y_pos + 210 + self.button_height)
        #        self.login_window_group.addToGroup(self.helpbottomline)
        #        self.helprightline = QtGui.QGraphicsLineItem()
        #        self.helprightline.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        #        self.helprightline.setLine(self.x_pos + 418 + self.button_length, self.y_pos + 210 + self.button_height, self.x_pos + 418 + self.button_length, self.y_pos + 210)
        #        self.login_window_group.addToGroup(self.helprightline)

        # Add a combobox to represent the menu...
        self.simmodulebox = QtGui.QComboBox()
        self.simmodulebox.setStyle(QtGui.QStyleFactory.create("windows"))
        self.simmodulebox.setGeometry(
            QtCore.QRect(self.mod_box_xpos + 2, self.mod_box_ypos + 2, self.boxlength - 4, 16))
        self.simmodulebox.setFixedWidth(self.boxlength)
        self.simmodulebox.setFont(font)

        self.simuserproxy = self.simscene.addWidget(self.simusernamebox)
        self.simpassproxy = self.simscene.addWidget(self.simpassbox)
        self.simokproxy = self.simscene.addWidget(self.simokbtn)
        self.simcnclproxy = self.simscene.addWidget(self.simcancelbtn)

        if not self.new_version_flag:
            self.simhelpproxy = self.simscene.addWidget(self.simhelpbtn)

        self.simmodproxy = self.simscene.addWidget(self.simmodulebox)

        # Add the Window logo...
        self.simwinlogo_pixmap, self.simwinlogo, self.simlogo_filename = self.windowLogoLoadToDialog()
        self.simwinlogoproxy = self.simscene.addWidget(self.simwinlogo)
        self.windowLogoUpdate(self.simwinlogo_pixmap, self.simwinlogo, self.simlogo_filename, self.x_pos, self.y_pos)
        self.simwinlogo.clicked.connect(self.windowLogoClicked)
        self.simgroupitems = (self.simloginwindow.loginrect,
                              self.simloginwindow.leftline,
                              self.simloginwindow.topline,
                              self.simloginwindow.rightline,
                              self.simloginwindow.bottomline,
                              self.simloginwindow.loginbanner,
                              self.simloginwindow.bannertext,
                              self.simarrow,
                              self.simuserproxy,
                              self.simpassproxy,
                              self.simokproxy,
                              self.simcnclproxy)
        if not self.new_version_flag:
            self.simgroupitems = self.simgroupitems + (self.simhelpproxy,)
        self.simgroupitems = self.simgroupitems + (self.simmodproxy, self.simwinlogoproxy)
        self.loginGroupAddItems(self.simlogin_window_group, self.simgroupitems)
        #self.winlogoproxy.setToolTip("<html><head/><body><p>Click this logo to customize...</p></body></html>")

        # Draw shade-lines around module combobox...
        self.simmoduShading = BoxShades(self.simloginwindow.loginrect, self.boxlength + 1, self.mod_box_xpos,
                                        self.mod_box_ypos)

        self.updateModuleStylesheet()
        self.updateButtonStyles()

        # load the "main" xrdp bitmap if old INI version...
        if not self.new_version_flag:
            self.simlogo, scene_width, scene_height, l_width, l_height = self.loadMainLogo(self.simscene)
            self.simlogodisplayer = QtGui.QGraphicsPixmapItem(self.simlogo)
            self.simlogodisplayer.setPos(scene_width - l_width, scene_height - l_height)
            self.simscene.addItem(self.simlogodisplayer)

        # Finally add the login group to the scene...
        self.simscene.addItem(self.simlogin_window_group)

        # Lower the gridLayout of the colour dialog because the loginwindowgroup
        # won't be movable within that region...
        #self.winSim.gridLayoutWidget.lower()

    @staticmethod
    def loginGroupAddItems(login_window_group, items):
        for item in items:
            login_window_group.addToGroup(item)

    @staticmethod
    def loginGroupRemoveItems(login_window_group, items):
        for item in items:
            login_window_group.removeFromGroup(item)

    def windowDialogResizeClicked(self):
        self.simwinlogo.blockSignals(True)
        self.orig_dialog_width = self.dialog_width
        self.orig_dialog_height = self.dialog_height
        self.rubberBand = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, parent=None)
        self.rubberBand.setGeometry(int(self.simlogin_window_group.x()), int(self.simlogin_window_group.y()),
                                    self.dialog_width, self.dialog_height)
        self.simscene.addWidget(self.rubberBand)
        self.rubberBand.show()
        self.resizeDialog = DialogSizeWidget()
        self.resizeDialog.move(self.winSim.width() - self.resizeDialog.width() - 25, 0)
        self.resizeDialog.widthSpinBox.setValue(self.dialog_width)
        self.resizeDialog.heightSpinBox.setValue(self.dialog_height)
        self.resizeDialog.closeBtn.clicked.connect(self.windowDialogResizeAccepted)
        self.resizeDialog.cancelBtn.clicked.connect(self.windowDialogResizeRejected)
        self.simloginwindow.resizearrow.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.simloginwindow.resizearrow.clicked.connect(self.windowDialogResizeArrowClickedInitial)
        self.simloginwindow.resizearrow.moved.connect(self.windowDialogResizeArrowMoving)
        self.simloginwindow.resizearrow.released.connect(self.windowDialogResizeArrowReleased)
        self.resizeDialog.widthSpinBox.valueChanged.connect(self.windowDialogResizeUpdate)
        self.resizeDialog.heightSpinBox.valueChanged.connect(self.windowDialogResizeUpdate)
        self.winSim.DialogGroupBox.setEnabled(False)
        self.winSim.ColoursGroupBox.setEnabled(False)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, False)
        self.winSim.resizeDialogBtn.setStyleSheet(self.colourbutton_stylesheet)
        self.simloginwindow.resizeVisible()
        self.simscene.addWidget(self.resizeDialog)

    def windowDialogResizeArrowClickedInitial(self, event):
        self.initialoffset_x = event.globalX()
        self.initialoffset_y = event.globalY()

    def windowDialogResizeArrowMoving(self, event):
        offset_x = event.globalX() - self.initialoffset_x
        if (self.dialog_width + offset_x) < 320:
            self.newwidth = 320
        else:
            self.newwidth = self.dialog_width + offset_x
        offset_y = event.globalY() - self.initialoffset_y
        if (self.dialog_height + offset_y) < 200:
            self.newheight = 200
        else:
            self.newheight = self.dialog_height + offset_y
        self.resizeDialog.widthSpinBox.blockSignals(True)
        self.resizeDialog.heightSpinBox.blockSignals(True)
        self.simlogin_window_group.prepareGeometryChange()
        self.rubberBand.setGeometry(QtCore.QRect(int(self.simlogin_window_group.x()),
                                                 int(self.simlogin_window_group.y()),
                                                 int(self.newwidth),
                                                 int(self.newheight)).normalized())
        self.simloginwindow.resizearrow.moved.disconnect(self.windowDialogResizeArrowMoving)
        self.simloginwindow.adjustDialogSize(self.rubberBand.x() - self.simlogin_window_group.x(),
                                             self.rubberBand.y() - self.simlogin_window_group.y(),
                                             self.newwidth, self.newheight)
        self.resizeDialog.widthSpinBox.setValue(self.rubberBand.width())
        self.resizeDialog.heightSpinBox.setValue(self.rubberBand.height())
        self.simloginwindow.resizearrow.moved.connect(self.windowDialogResizeArrowMoving)

        self.resizeDialog.widthSpinBox.blockSignals(False)
        self.resizeDialog.heightSpinBox.blockSignals(False)

    # noinspection PyUnusedLocal
    def windowDialogResizeArrowReleased(self, arg):
        self.dialog_width = self.newwidth
        self.dialog_height = self.newheight

    # noinspection PyUnusedLocal
    def windowDialogResizeUpdate(self, val):
        self.start_x = self.simloginwindow.resizearrow.x()
        self.start_y = self.simloginwindow.resizearrow.y()
        self.simloginwindow.adjustDialogSize(self.rubberBand.x() - self.simlogin_window_group.x(),
                                             self.rubberBand.y() - self.simlogin_window_group.y(),
                                             int(self.resizeDialog.widthSpinBox.value()),
                                             int(self.resizeDialog.heightSpinBox.value()))
        self.rubberBand.setGeometry(QtCore.QRect(int(self.simlogin_window_group.x()),
                                                 int(self.simlogin_window_group.y()),
                                                 int(self.resizeDialog.widthSpinBox.value()),
                                                 int(self.resizeDialog.heightSpinBox.value())))
        self.dialog_width = int(self.resizeDialog.widthSpinBox.value())
        self.dialog_height = int(self.resizeDialog.heightSpinBox.value())

    def windowDialogResizeRejected(self):
        self.rubberBand.hide()
        self.simloginwindow.adjustDialogSize(self.simloginwindow.loginrect.x(),
                                             self.simloginwindow.loginrect.y(),
                                             self.orig_dialog_width, self.orig_dialog_height)
        self.dialog_width = self.orig_dialog_width
        self.dialog_height = self.orig_dialog_height
        self.xrdp_ini_file.set('globals', 'ls_width', str(self.dialog_width))
        self.xrdp_ini_file.set('globals', 'ls_height', str(self.dialog_height))
        self.loginGroupRemoveItems(self.simlogin_window_group, self.simgroupitems)
        self.loginGroupAddItems(self.simlogin_window_group, self.simgroupitems)
        self.simloginwindow.resizeInvisible()
        self.resizeDialog.deleteLater()
        self.winSim.DialogGroupBox.setEnabled(True)
        self.winSim.ColoursGroupBox.setEnabled(True)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, True)
        self.winSim.resizeDialogBtn.setStyleSheet("")
        self.simwinlogo.blockSignals(False)

    def windowDialogResizeAccepted(self):
        self.rubberBand.hide()
        self.simloginwindow.adjustDialogSize(self.rubberBand.x() - self.simlogin_window_group.x(),
                                             self.rubberBand.y() - self.simlogin_window_group.y(),
                                             self.rubberBand.width(), self.rubberBand.height())
        self.dialog_width = self.resizeDialog.widthSpinBox.value()
        self.dialog_height = self.resizeDialog.heightSpinBox.value()
        self.xrdp_ini_file.set('globals', 'ls_width', str(self.dialog_width))
        self.xrdp_ini_file.set('globals', 'ls_height', str(self.dialog_height))
        self.loginGroupRemoveItems(self.simlogin_window_group, self.simgroupitems)
        self.loginGroupAddItems(self.simlogin_window_group, self.simgroupitems)
        self.simloginwindow.resizeInvisible()
        self.resizeDialog.deleteLater()
        self.winSim.DialogGroupBox.setEnabled(True)
        self.winSim.ColoursGroupBox.setEnabled(True)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, True)
        self.winSim.resizeDialogBtn.setStyleSheet("")
        self.simwinlogo.blockSignals(False)
        self.xrdp_changed()

    #This loads the login window logo...
    def windowLogoLoadToDialog(self):
        winlogo_pixmap = QtGui.QPixmap()
        winlogo = ClickableQLabel(winlogo_pixmap)
        winlogo.setAutoFillBackground(False)
        if self.new_version_flag:
            if self.logo_filename != "":
                if os.path.isfile(self.logo_filename):
                    filename = self.logo_filename
                else:
                    filename = "/usr/share/xrdp/xrdp_logo.bmp"
            else:
                filename = "/usr/share/xrdp/xrdp_logo.bmp"
        else:
            filename = "/usr/share/xrdp/ad24b.bmp"

        return winlogo_pixmap, winlogo, filename

    def windowLogoUpdate(self, winlogo_pixmap, winlogo, filename, x, y):
        if os.path.isfile(filename):
            winlogo_pixmap.load(filename)
        else:
            winlogo_pixmap.load(":/Logo/xrdptmp.png")

        if self.new_version_flag:
            winlogo.setGeometry(self.logo_xpos, self.logo_ypos, winlogo_pixmap.width(), winlogo_pixmap.height())
            self.xrdp_ini_file.set('globals', 'ls_logo_filename', filename)
        else:
            winlogo.setGeometry(x + 10, y + 30, winlogo_pixmap.width(), winlogo_pixmap.height())

        winlogo.setStyleSheet("background-image: url(" + filename + ");"
                            "background-repeat: no-repeat;"
                            "background-position: center center;"
                            "border: 0px; margin: 0px; padding: 0px")

    def windowLogoPositionClicked(self):
        self.logoStartGeometry = self.simwinlogo.geometry()
        self.simwinlogo.clicked.disconnect(self.windowLogoClicked)
        self.logoPosDialog = LogoPositionWidget()
        #self.logoPosDialog.move(1000,20)
        self.logoPosDialog.move(self.winSim.width() - self.logoPosDialog.width() - 25, 0)
        self.simscene.addWidget(self.logoPosDialog)
        self.logoPosDialog.xSpinBox.setValue(self.simwinlogo.x())
        self.logoPosDialog.ySpinBox.setValue(self.simwinlogo.y())
        self.logoPosDialog.okBtn.clicked.connect(self.windowlogoPositionAccepted)
        self.logoPosDialog.cancelBtn.clicked.connect(self.windowlogoPositionRejected)
        self.logoPosDialog.xSpinBox.valueChanged.connect(self.windowlogoXYSpinboxValueChanged)
        self.logoPosDialog.ySpinBox.valueChanged.connect(self.windowlogoXYSpinboxValueChanged)
        self.simwinlogo.clicked.connect(self.windowLogoPositionInitialClick)
        self.simwinlogo.moved.connect(self.windowlogoPositionMove)
        self.winSim.DialogGroupBox.setEnabled(False)
        self.winSim.ColoursGroupBox.setEnabled(False)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, False)
        self.winSim.logoPositionBtn.setStyleSheet(self.colourbutton_stylesheet)

    def windowLogoPositionInitialClick(self, event):
        self.start_x = self.simwinlogo.x()
        self.start_y = self.simwinlogo.y()
        self.mouse_offset_x = event.globalX()
        self.mouse_offset_y = event.globalY()

    def windowlogoPositionMove(self, event):
        self.logoPosDialog.xSpinBox.blockSignals(True)
        xpos = self.start_x - self.mouse_offset_x + event.globalX()
        if xpos < 5:
            xpos = 5
        ypos = self.start_y - self.mouse_offset_y + event.globalY()
        if ypos < 25:
            ypos = 25
        self.simwinlogo.move(xpos, ypos)
        self.logoPosDialog.xSpinBox.setValue(self.simwinlogo.x())
        self.logoPosDialog.ySpinBox.setValue(self.simwinlogo.y())
        self.logoPosDialog.xSpinBox.blockSignals(False)

    def windowlogoPositionAccepted(self):
        self.xrdp_ini_file.set('globals', 'ls_logo_x_pos', str(self.simwinlogo.x()))
        self.xrdp_ini_file.set('globals', 'ls_logo_y_pos', str(self.simwinlogo.y()))
        self.logoPosDialog.deleteLater()
        self.simwinlogo.clicked.connect(self.windowLogoClicked)
        self.winSim.DialogGroupBox.setEnabled(True)
        self.winSim.ColoursGroupBox.setEnabled(True)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, True)
        self.winSim.logoPositionBtn.setStyleSheet("")
        self.xrdp_changed()

    def windowlogoPositionRejected(self):
        self.simwinlogo.setGeometry(self.logoStartGeometry)
        self.simwinlogo.clicked.connect(self.windowLogoClicked)
        self.logoPosDialog.deleteLater()
        self.winSim.DialogGroupBox.setEnabled(True)
        self.winSim.ColoursGroupBox.setEnabled(True)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, True)
        self.winSim.logoPositionBtn.setStyleSheet("")

    # noinspection PyUnusedLocal
    def windowlogoXYSpinboxValueChanged(self, arg):
        new_pos_logo_x = self.logoPosDialog.xSpinBox.value()
        if new_pos_logo_x < 5:
            new_pos_logo_x = 5
        self.simwinlogo.move(new_pos_logo_x, int(self.simwinlogo.y()))
        new_pos_logo_y = self.logoPosDialog.ySpinBox.value()
        if new_pos_logo_y < 25:
            new_pos_logo_y = 25
        self.simwinlogo.move(int(self.simwinlogo.x()), new_pos_logo_y)

    # Loads the XRDP bitmap...
    @staticmethod
    def loadMainLogo(scene):
        logo = QtGui.QPixmap()
        logofile = "/usr/share/xrdp/xrdp24b.bmp"
        if os.path.isfile(logofile):
            logo.load(logofile)
        else:
            logo.load(":/Logo/xrdp24b.png")
        l_width = logo.width()
        l_height = logo.height()
        scene_width = scene.width()
        scene_height = scene.height()
        return logo, scene_width, scene_height, l_width, l_height

    # Display the Logo Customization Window
    # noinspection PyUnusedLocal
    def windowLogoClicked(self, arg):
        self.simwinlogo.blockSignals(True)
        self.customizeLogoForm = LogoCustomizationWidget()
        self.customizeLogoForm.logoFilePath.setText(self.logo_filename)
        self.windowLogoDisplayScaled()
    #        self.winlogodisplayer.setGeometry(5,75, self.winlogo_pixmap.width(), self.winlogo_pixmap.height())
        self.customizeLogoForm.closeButton.clicked.connect(self.windowLogoCustomizeClose)
        self.customizeLogoForm.changeLogoBtn.clicked.connect(self.windowLogoSelectFromFile)
        self.customizeLogoForm.importAnImageBtn.clicked.connect(self.windowLogoDisplayImportLogoWindow)
        self.customizeLogoForm.show()

    def windowLogoDisplayScaled(self):
        scaledLogo = self.simwinlogo_pixmap.scaled(self.customizeLogoForm.currentLogoLabel.size(),
                                                   QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.customizeLogoForm.currentLogoLabel.setPixmap(scaledLogo)
        self.customizeLogoForm.currentLogoWidthLabel.setText(str(self.simwinlogo_pixmap.width()))
        self.customizeLogoForm.currentLogoHeightLabel.setText(str(self.simwinlogo_pixmap.height()))
        self.customizeLogoForm.currentLogoLabel.setToolTip('<html><img src=' + str(self.logo_filename) + '/></html>')
        status = self.windowLogoCheckBitmap(self.simwinlogo_pixmap)
        if status == 0:
            self.customizeLogoForm.imageStatusStackedWidget.setCurrentIndex(1)
        if status == 1:
            self.customizeLogoForm.imageStatusStackedWidget.setCurrentIndex(2)

    def windowLogoDisplayImportLogoWindow(self):
        self.importImageForm = ImageImport()
        self.importImageForm.importLogoBtn.clicked.connect(self.windowLogoImport)
        self.importImageForm.switchToImportedLogoBtn.clicked.connect(self.windowLogoSwitchToImported)
        self.importImageForm.switchToImportedLogoBtn.setVisible(False)
        self.increaseBtn = self.importImageForm.imageStatusStackedWidget.findChild(QtGui.QPushButton, 'increaseImageBtn')
        self.decreaseBtn = self.importImageForm.imageStatusStackedWidget.findChild(QtGui.QPushButton, 'decreaseImageBtn')
        self.increaseBtn.clicked.connect(self.windowLogoUpscaleImage)
        self.decreaseBtn.clicked.connect(self.windowLogoDownscaleImage)
        self.importImageForm.saveImportedImageBtn.clicked.connect(self.windowLogoSaveImportedImage)
        self.importImageForm.closeImportWindowBtn.clicked.connect(self.windowLogoCloseImportWindow)
        self.importImageForm.show()

    def windowLogoCustomizeClose(self):
        self.customizeLogoForm.deleteLater()
        del self.customizeLogoForm
        self.simwinlogo.blockSignals(False)
        self.simlogin_window_group.setVisible(True)

    def windowLogoCloseImportWindow(self):
        self.importImageForm.deleteLater()
        del self.importImageForm

    def windowLogoSelectFromFile(self):
        filename = QtGui.QFileDialog.getOpenFileName(self.customizeLogoForm, "Select logo image file...",
                                                     os.path.dirname(self.logo_filename) + "/*.BMP",
                                                     "BMP files (*.BMP)")
        if filename[0] != "":
            self.logo_filename = filename[0]
            self.customizeLogoForm.logoFilePath.setText(self.logo_filename)
            self.simwinlogo_pixmap.load(self.logo_filename)
            self.windowLogoCheckBitmap(self.simwinlogo_pixmap)
            self.windowLogoDisplayScaled()
            self.windowLogoUpdate(self.simwinlogo_pixmap, self.simwinlogo, self.logo_filename, self.x_pos, self.y_pos)

    @staticmethod
    def windowLogoCheckBitmap(bitmap):
        status = 0
        if 0 != bitmap.width() % 4:
            status = 1
        return status

    def windowLogoImport(self):
        wdgt = self.customizeLogoForm.findChild(QtGui.QLabel, 'importedDisplayer')
        if wdgt is not None:
            wdgt.setParent(None)
            del wdgt
        importedDisplayer = QtGui.QLabel(self.importImageForm)
        importedDisplayer.setObjectName('importedDisplayer')
        importedDisplayer.setStyleSheet('QLabel {'
                                        'border: 3px; '
                                        'border-color: black; '
                                        '}')
        import_image = QtGui.QImage()
        importedDisplayer.setVisible(False)
        filename = QtGui.QFileDialog.getOpenFileName(self.importImageForm, "Select an image file to import...", "", "Image Files (*.bmp *.png *.jpg)")[0]
        if filename != "":
            import_image.load(filename)
            if import_image.hasAlphaChannel():
                intermediate_image = QtGui.QImage(import_image.size(), QtGui.QImage.Format_RGB32)
                intermediate_image.fill(QtGui.QColor(255, 255, 255).rgb())
                painter = QtGui.QPainter()
                painter.begin(intermediate_image)
                painter.drawImage(0, 0, import_image)
                painter.end()
                newformat_image = intermediate_image.convertToFormat(QtGui.QImage.Format_RGB32)
            else:
                newformat_image = import_image.convertToFormat(QtGui.QImage.Format_RGB32)
            self.importImageForm.importedFilePath.setText(filename)
            self.windowLogoSetImportPixmap(newformat_image)

    def windowLogoSetImportPixmap(self, newformat_image):
        self.import_pixmap = QtGui.QPixmap.fromImage(newformat_image)
        scaledImportedLogo = self.import_pixmap.scaled(self.importImageForm.importedLogoLabel.size(),
                                                       QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.importImageForm.importedLogoLabel.setPixmap(scaledImportedLogo)
        self.importImageForm.importedLogoWidthLabel.setText(str(newformat_image.width()))
        self.importImageForm.importedLogoHeightLabel.setText(str(newformat_image.height()))
        self.windowLogoCheckImportedImageWidth(int(newformat_image.width()))

    def windowLogoCheckImportedImageWidth(self, width):
        status = self.windowLogoCheckBitmap(self.import_pixmap)
        if status == 0:
            self.importImageForm.imageStatusStackedWidget.setCurrentIndex(1)
        if status == 1:
            self.importImageForm.imageStatusStackedWidget.setCurrentIndex(2)
            self.windowLogoCheckRescaleSteps(width)

    # Check factors to scale image up or down, depending on No. of pixels up or down...
    def windowLogoCheckRescaleSteps(self, width):
        self.increasing_width_by = 0
        self.decreasing_width_by = 0
        while 0 != (width + self.increasing_width_by) % 4:
            self.increasing_width_by += 1
        while 0 != (width - self.decreasing_width_by) % 4:
            self.decreasing_width_by += 1
        if self.increasing_width_by == 1:
            self.increaseBtn.setText("Increase image width by " + str(self.increasing_width_by) + " pixel")
        if self.increasing_width_by > 1:
            self.increaseBtn.setText("Increase image width by " + str(self.increasing_width_by) + " pixels")
        if self.decreasing_width_by == 1:
            self.decreaseBtn.setText("Decrease image width by " + str(self.decreasing_width_by) + " pixel")
        if self.decreasing_width_by > 1:
            self.decreaseBtn.setText("Decrease image width by " + str(self.decreasing_width_by) + " pixels")

    def windowLogoUpscaleImage(self):
        scaled_image = self.import_pixmap.scaledToWidth(self.import_pixmap.width() + self.increasing_width_by, mode=QtCore.Qt.SmoothTransformation)
        newformat_image = scaled_image.toImage()
        self.windowLogoSetImportPixmap(newformat_image)

    def windowLogoDownscaleImage(self):
        scaled_image = self.import_pixmap.scaledToWidth(self.import_pixmap.width() - self.decreasing_width_by,
                                                        mode=QtCore.Qt.SmoothTransformation)
        newformat_image = scaled_image.toImage()
        self.windowLogoSetImportPixmap(newformat_image)

    def windowLogoSaveImportedImage(self):
        fname = QtGui.QFileDialog.getSaveFileName(self.importImageForm, "Save imported file as...", "", "BMP files (*.BMP)")
        if fname[0] != "":
            try:
                self.import_pixmap.save(fname[0], 'BMP')
                self.importImageForm.exportedFilePath.setText(fname[0])
                self.importImageForm.importedLogoLabel.setToolTip('<html><img src=' + str(fname[0]) + '/></html>')
                self.importImageForm.switchToImportedLogoBtn.setVisible(True)
                #newformat_image.save('TESTSAVE.bmp', 'BMP')
            except PermissionError:
                message_window = InfoWindow(
                "<html><head/><body><p>You do not have permission to save the BMP file.</p><p>Try saving to a different location.</p></body></html>")
                message_window.exec_()

    def windowLogoSwitchToImported(self):
        self.logo_filename = self.importImageForm.exportedFilePath.text()
        self.customizeLogoForm.logoFilePath.setText(self.logo_filename)
        self.simwinlogo_pixmap.load(self.logo_filename)
        self.windowLogoUpdate(self.simwinlogo_pixmap, self.simwinlogo, self.logo_filename, self.x_pos, self.y_pos)
        self.windowLogoDisplayScaled()
        self.windowLogoCloseImportWindow()

    def windowDialogButtonsCustBtnClicked(self):
        # Stop the Dialog Window from being moved
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, False)

        # Save a copy of the button's Position and Size
        self.orig_ok_btn_position = self.simokbtn.pos()
        self.orig_ok_btn_dimensions = self.simokbtn.geometry()
        self.orig_cancel_btn_position = self.simcancelbtn.pos()
        self.orig_cancel_btn_dimensions = self.simcancelbtn.geometry()

        # Create a dialog for the button customization
        self.btnDialog = DialogButtonsCustomizationWidget()
        # Widget Ok and Cancel connections...
        self.btnDialog.cancelBtn.clicked.connect(self.windowDialogButtonsCancelClicked)
        self.btnDialog.closeBtn.clicked.connect(self.windowDialogButtonsOKClicked)
        self.btnDialog.move(self.winSim.width() - self.btnDialog.width() - 25, 0)
        self.simscene.addWidget(self.btnDialog)

        # Update the spinboxes with the current values
        self.btnDialog.ok_x_spinBox.setValue(int(self.okbtn_xpos))
        self.btnDialog.ok_y_spinBox.setValue(int(self.okbtn_ypos))
        self.btnDialog.ok_width_spinBox.setValue(int(self.okbtn_width))
        self.btnDialog.ok_height_spinBox.setValue(int(self.okbtn_height))

        self.btnDialog.cancel_x_spinBox.setValue(int(self.cancelbtn_xpos))
        self.btnDialog.cancel_y_spinBox.setValue(int(self.cancelbtn_ypos))
        self.btnDialog.cancel_width_spinBox.setValue(int(self.cancelbtn_width))
        self.btnDialog.cancel_height_spinBox.setValue(int(self.cancelbtn_height))

        # Create an arrow for the OK button positioning
        self.okBtnPosArrow = ClickableQLabel(QtGui.QPixmap(":/dragpoint/images/dragpoints/Arrow_topleft.png"))
        self.okBtnPosArrow.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.okBtnPosArrow.setToolTip("Drag to position OK button")

        # Move the arrow to current location of OK button
        xpos = int(self.simokbtn.x()) + int(self.simlogin_window_group.x())
        ypos = int(self.simokbtn.y()) + int(self.simlogin_window_group.y())
        self.okBtnPosArrow.move(xpos, ypos)

        # Connect the arrow's signals to the handler functions
        self.okBtnPosArrow.clicked.connect(self.windowDialogButtonsOKPosArrowInitialClick)
        self.okBtnPosArrow.moved.connect(self.windowDialogButtonsOKPosArrowMoving)

        # Create an arrow for OK button width and height
        self.OkBtnSizeArrow = ClickableQLabel(QtGui.QPixmap(":/dragpoint/images/dragpoints/Arrow_bottomright.png"))
        self.OkBtnSizeArrow.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.OkBtnSizeArrow.setToolTip("Drag to change OK button size")
        # Move the arrow to current bottom-right corner of OK Button
        self.windowDialogButtonsPositionBtnResizeArrow(self.OkBtnSizeArrow,
                                                       xpos,
                                                       ypos,
                                                       int(self.okbtn_width),
                                                       int(self.okbtn_height))
        # Connect the size arrow's signals to the handler functions
        self.OkBtnSizeArrow.clicked.connect(self.windowDialogButtonsOKResizeArrowInitialClick)
        self.OkBtnSizeArrow.moved.connect(self.windowDialogButtonsOKSizeArrowMoving)
        self.OkBtnSizeArrow.released.connect(self.windowDialogButtonsOKSizeArrowReleased)

        # Create an arrow for the Cancel button positioning
        self.cancelBtnPosArrow = ClickableQLabel(QtGui.QPixmap(":/dragpoint/images/dragpoints/Arrow_topleft.png"))
        self.cancelBtnPosArrow.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.cancelBtnPosArrow.setToolTip("Drag to position Cancel button")

        # Connect the cancel pos arrow's signals to the handler functions
        self.cancelBtnPosArrow.clicked.connect(self.windowDialogButtonsCancelPosArrowInitialClick)
        self.cancelBtnPosArrow.moved.connect(self.windowDialogButtonsCancelPosArrowMoving)

        # Move the arrow to current location of OK button
        xpos = int(self.simcancelbtn.x()) + int(self.simlogin_window_group.x())
        ypos = int(self.simcancelbtn.y()) + int(self.simlogin_window_group.y())
        self.cancelBtnPosArrow.move(xpos, ypos)

        # Create an arrow for Cancel button width and height
        self.cancelBtnSizeArrow = ClickableQLabel(QtGui.QPixmap(":/dragpoint/images/dragpoints/Arrow_bottomright.png"))
        self.cancelBtnSizeArrow.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.cancelBtnSizeArrow.setToolTip("Drag to change Cancel button size")
        # Move the arrow to current bottom-right corner of OK Button
        self.windowDialogButtonsPositionBtnResizeArrow(self.cancelBtnSizeArrow,
                                                       xpos,
                                                       ypos,
                                                       int(self.cancelbtn_width),
                                                       int(self.cancelbtn_height))
        # Connect the size arrow's signals to the handler functions
        self.cancelBtnSizeArrow.clicked.connect(self.windowDialogButtonsCancelResizeArrowInitialClick)
        self.cancelBtnSizeArrow.moved.connect(self.windowDialogButtonsCancelSizeArrowMoving)
        self.cancelBtnSizeArrow.released.connect(self.windowDialogButtonsCancelSizeArrowReleased)

        # Display them arrows
        self.simscene.addWidget(self.okBtnPosArrow)
        self.simscene.addWidget(self.OkBtnSizeArrow)
        self.simscene.addWidget(self.cancelBtnPosArrow)
        self.simscene.addWidget(self.cancelBtnSizeArrow)

        self.winSim.DialogGroupBox.setEnabled(False)
        self.winSim.ColoursGroupBox.setEnabled(False)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, False)
        self.winSim.buttonsLocationBtn.setStyleSheet(self.colourbutton_stylesheet)

        # Connect spinbox value changed signals
        self.btnDialog.ok_x_spinBox.valueChanged.connect(self.windowDialogButtonsOK_XY_SpinboxValueChanged)
        self.btnDialog.ok_y_spinBox.valueChanged.connect(self.windowDialogButtonsOK_XY_SpinboxValueChanged)
        self.btnDialog.cancel_x_spinBox.valueChanged.connect(self.windowDialogButtonsCancel_XY_SpinboxValueChanged)
        self.btnDialog.cancel_y_spinBox.valueChanged.connect(self.windowDialogButtonsCancel_XY_SpinboxValueChanged)
        self.btnDialog.ok_width_spinBox.valueChanged.connect(
            self.windowDialogButtonsOK_width_height_SpinboxValueChanged)
        self.btnDialog.ok_height_spinBox.valueChanged.connect(
            self.windowDialogButtonsOK_width_height_SpinboxValueChanged)
        self.btnDialog.cancel_width_spinBox.valueChanged.connect(
            self.windowDialogButtonsCancel_width_height_SpinboxValueChanged)
        self.btnDialog.cancel_height_spinBox.valueChanged.connect(
            self.windowDialogButtonsCancel_width_height_SpinboxValueChanged)

    @staticmethod
    def windowDialogButtonsPositionBtnResizeArrow(arrow, xpos, ypos, button_width, button_height):
        btnbottomright_x = xpos + button_width
        btnbottomright_y = ypos + button_height
        x = btnbottomright_x - arrow.pixmap().width()
        y = btnbottomright_y - arrow.pixmap().height()
        arrow.move(x, y)

    def windowDialogButtonsCancelClicked(self):
        self.btnDialog.deleteLater()
        self.okBtnPosArrow.deleteLater()
        self.OkBtnSizeArrow.deleteLater()
        self.cancelBtnPosArrow.deleteLater()
        self.cancelBtnSizeArrow.deleteLater()
        self.simokbtn.move(self.orig_ok_btn_position)
        self.simokbtn.setGeometry(self.orig_ok_btn_dimensions)
        self.okbtn_width = self.simokbtn.width()
        self.okbtn_height = self.simokbtn.height()
        self.simokbtn.setMaximumWidth(self.okbtn_width)
        self.simokbtn.setMaximumHeight(self.okbtn_height)
        self.simcancelbtn.move(self.orig_cancel_btn_position)
        self.simcancelbtn.setGeometry(self.orig_cancel_btn_dimensions)
        self.cancelbtn_width = self.simcancelbtn.width()
        self.cancelbtn_height = self.simcancelbtn.height()
        self.simcancelbtn.setMaximumWidth(self.cancelbtn_width)
        self.simcancelbtn.setMaximumHeight(self.cancelbtn_height)
        self.winSim.DialogGroupBox.setEnabled(True)
        self.winSim.ColoursGroupBox.setEnabled(True)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, True)
        self.winSim.buttonsLocationBtn.setStyleSheet("")

    def windowDialogButtonsOKClicked(self):
        self.okbtn_xpos = self.btnDialog.ok_x_spinBox.value()
        self.okbtn_ypos = self.btnDialog.ok_y_spinBox.value()
        self.cancelbtn_xpos = self.btnDialog.cancel_x_spinBox.value()
        self.cancelbtn_ypos = self.btnDialog.cancel_y_spinBox.value()
        self.xrdp_ini_file.set('globals', 'ls_btn_ok_x_pos', str(self.okbtn_xpos))
        self.xrdp_ini_file.set('globals', 'ls_btn_ok_y_pos', str(self.okbtn_ypos))
        self.xrdp_ini_file.set('globals', 'ls_btn_ok_width', str(self.okbtn_width))
        self.xrdp_ini_file.set('globals', 'ls_btn_ok_height', str(self.okbtn_height))
        self.xrdp_ini_file.set('globals', 'ls_btn_cancel_x_pos', str(self.cancelbtn_xpos))
        self.xrdp_ini_file.set('globals', 'ls_btn_cancel_y_pos', str(self.cancelbtn_ypos))
        self.xrdp_ini_file.set('globals', 'ls_btn_cancel_width', str(self.cancelbtn_width))
        self.xrdp_ini_file.set('globals', 'ls_btn_cancel_height', str(self.cancelbtn_height))
        self.btnDialog.deleteLater()
        self.okBtnPosArrow.deleteLater()
        self.OkBtnSizeArrow.deleteLater()
        self.cancelBtnPosArrow.deleteLater()
        self.cancelBtnSizeArrow.deleteLater()
        self.winSim.DialogGroupBox.setEnabled(True)
        self.winSim.ColoursGroupBox.setEnabled(True)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, True)
        self.winSim.buttonsLocationBtn.setStyleSheet("")
        self.xrdp_changed()

    def windowDialogButtonsOKPosArrowInitialClick(self, event):
        # Save the current global mouse position so we can calculate the offset
        self.initial_mouse_x = int(event.globalX())
        self.initial_mouse_y = int(event.globalY())
        # Save the initial Size Arrow coords
        self.initial_size_arrow_x = int(self.OkBtnSizeArrow.x())
        self.initial_size_arrow_y = int(self.OkBtnSizeArrow.y())
        # save the Initial OK button X position
        self.initial_okbtn_x = int(self.simokbtn.x())
        self.initial_okbtn_y = int(self.simokbtn.y())
        # Save the initial position arrow x & y coords
        self.initial_pos_arrow_x = int(self.okBtnPosArrow.x())
        self.initial_pos_arrow_y = int(self.okBtnPosArrow.y())
        # Calculate the offset between current mouse location and
        # The ORIGIN OF THE Size ARROW...
        # This gives us a way of moving the arrow without things jumping all
        # over the place!
        self.mouse_offset_x = int(event.globalX()) - self.initial_pos_arrow_x
        self.mouse_offset_y = int(event.globalY()) - self.initial_pos_arrow_y

    def windowDialogButtonsOKPosArrowMoving(self, event):
        self.btnDialog.ok_x_spinBox.blockSignals(True)
        self.btnDialog.ok_y_spinBox.blockSignals(True)
        # Calculate the offset between original mouse location and mouse current location
        offset_x = int(event.globalX()) - self.initial_pos_arrow_x
        offset_y = int(event.globalY()) - self.initial_pos_arrow_y
        # Calculate the ok button's x,y coords based on that offset
        new_ok_x_position = self.initial_okbtn_x + offset_x - self.mouse_offset_x
        new_ok_y_position = self.initial_okbtn_y + offset_y - self.mouse_offset_y
        if new_ok_x_position >= 5 and new_ok_y_position >= 25:
            # Move the arrow and ok button
            self.okBtnPosArrow.move(new_ok_x_position + int(self.simlogin_window_group.x()),
                                    new_ok_y_position + int(self.simlogin_window_group.y()))
            self.simokbtn.move(new_ok_x_position, new_ok_y_position)
            # Move the Size arrow...
            self.OkBtnSizeArrow.move(self.initial_size_arrow_x + offset_x - self.mouse_offset_x,
                                     self.initial_size_arrow_y + offset_y - self.mouse_offset_y)
            # Update the OK button x, y spinboxes
            self.btnDialog.ok_x_spinBox.setValue(new_ok_x_position - int(self.simloginwindow.x()))
            self.btnDialog.ok_y_spinBox.setValue(new_ok_y_position - int(self.simloginwindow.y()))

        self.btnDialog.ok_x_spinBox.blockSignals(False)
        self.btnDialog.ok_y_spinBox.blockSignals(False)

    def windowDialogButtonsOK_XY_SpinboxValueChanged(self):
        # Calculate new X position of OK button position arrow
        new_pos_arrow_x = self.btnDialog.ok_x_spinBox.value() + int(self.simlogin_window_group.x())
        self.okBtnPosArrow.move(new_pos_arrow_x, self.okBtnPosArrow.y())
        new_pos_arrow_y = self.btnDialog.ok_y_spinBox.value() + int(self.simlogin_window_group.y())
        self.okBtnPosArrow.move(self.okBtnPosArrow.x(), new_pos_arrow_y)
        self.simokbtn.move(self.btnDialog.ok_x_spinBox.value(), self.btnDialog.ok_y_spinBox.value())
        self.okbtn_xpos = self.btnDialog.ok_x_spinBox.value()
        self.okbtn_ypos = self.btnDialog.ok_y_spinBox.value()
        new_size_arrow_x = self.simlogin_window_group.x() + self.simokbtn.x() + self.simokbtn.width() - self.OkBtnSizeArrow.width()
        self.OkBtnSizeArrow.move(new_size_arrow_x, self.OkBtnSizeArrow.y())
        new_size_arrow_y = self.simlogin_window_group.y() + self.simokbtn.y() + self.simokbtn.height() - self.OkBtnSizeArrow.height()
        self.OkBtnSizeArrow.move(self.OkBtnSizeArrow.x(), new_size_arrow_y)

    def windowDialogButtonsCancel_XY_SpinboxValueChanged(self):
        # Calculate new XY position of Cancel button position arrow
        new_pos_arrow_x = self.btnDialog.cancel_x_spinBox.value() + int(self.simlogin_window_group.x())
        self.cancelBtnPosArrow.move(new_pos_arrow_x, self.cancelBtnPosArrow.y())
        new_pos_arrow_y = self.btnDialog.cancel_y_spinBox.value() + int(self.simlogin_window_group.y())
        self.cancelBtnPosArrow.move(self.cancelBtnPosArrow.x(), new_pos_arrow_y)
        self.simcancelbtn.move(self.btnDialog.cancel_x_spinBox.value(), self.btnDialog.cancel_y_spinBox.value())
        self.cancelbtn_xpos = self.btnDialog.cancel_x_spinBox.value()
        self.cancelbtn_ypos = self.btnDialog.cancel_y_spinBox.value()
        new_size_arrow_x = self.simlogin_window_group.x() + self.simcancelbtn.x() + self.simcancelbtn.width() - self.cancelBtnSizeArrow.width()
        self.cancelBtnSizeArrow.move(new_size_arrow_x, self.cancelBtnSizeArrow.y())
        new_size_arrow_y = self.simlogin_window_group.y() + self.simcancelbtn.y() + self.simcancelbtn.height() - self.cancelBtnSizeArrow.height()
        self.cancelBtnSizeArrow.move(self.cancelBtnSizeArrow.x(), new_size_arrow_y)

    def windowDialogButtonsOK_width_height_SpinboxValueChanged(self):
        self.OkBtnSizeArrow.blockSignals(True)
        self.okbtn_width = self.btnDialog.ok_width_spinBox.value()
        self.okbtn_height = self.btnDialog.ok_height_spinBox.value()
        self.simokbtn.setGeometry(self.simokbtn.x(), self.simokbtn.y(), self.okbtn_width, self.okbtn_height)
        self.updateButtonStyles()
        new_size_arrow_x = self.simlogin_window_group.x() + self.simokbtn.x() + self.simokbtn.width() - self.OkBtnSizeArrow.width()
        new_size_arrow_y = self.simlogin_window_group.y() + self.simokbtn.y() + self.simokbtn.height() - self.OkBtnSizeArrow.height()
        self.OkBtnSizeArrow.move(new_size_arrow_x, new_size_arrow_y)
        self.OkBtnSizeArrow.blockSignals(False)

    def windowDialogButtonsCancel_width_height_SpinboxValueChanged(self):
        self.cancelBtnSizeArrow.blockSignals(True)
        self.cancelbtn_width = self.btnDialog.cancel_width_spinBox.value()
        self.cancelbtn_height = self.btnDialog.cancel_height_spinBox.value()
        self.simcancelbtn.setGeometry(self.simcancelbtn.x(), self.simcancelbtn.y(), self.cancelbtn_width,
                                      self.cancelbtn_height)
        self.updateButtonStyles()
        new_size_arrow_x = self.simlogin_window_group.x() + self.simcancelbtn.x() + self.simcancelbtn.width() - self.cancelBtnSizeArrow.width()
        new_size_arrow_y = self.simlogin_window_group.y() + self.simcancelbtn.y() + self.simcancelbtn.height() - self.cancelBtnSizeArrow.height()
        self.cancelBtnSizeArrow.move(new_size_arrow_x, new_size_arrow_y)
        self.cancelBtnSizeArrow.blockSignals(False)

    def windowDialogButtonsCancelPosArrowInitialClick(self, event):
        # Save the current global mouse position so we can calculate the offset
        self.initial_mouse_x = int(event.globalX())
        self.initial_mouse_y = int(event.globalY())
        # Save the initial Size Arrow coords
        self.initial_size_arrow_x = int(self.cancelBtnSizeArrow.x())
        self.initial_size_arrow_y = int(self.cancelBtnSizeArrow.y())
        # save the Initial OK button X position
        self.initial_cancel_btn_x = int(self.simcancelbtn.x())
        self.initial_cancel_btn_y = int(self.simcancelbtn.y())
        # Save the initial position arrow x & y coords
        self.initial_pos_arrow_x = int(self.cancelBtnPosArrow.x())
        self.initial_pos_arrow_y = int(self.cancelBtnPosArrow.y())
        # Calculate the offset between current mouse location and
        # The ORIGIN OF THE Size ARROW...
        # This gives us a way of moving the arrow without things jumping all
        # over the place!
        self.mouse_offset_x = int(event.globalX()) - self.initial_pos_arrow_x
        self.mouse_offset_y = int(event.globalY()) - self.initial_pos_arrow_y

    def windowDialogButtonsCancelPosArrowMoving(self, event):
        self.btnDialog.cancel_x_spinBox.blockSignals(True)
        self.btnDialog.cancel_y_spinBox.blockSignals(True)

        # Calculate the offset between original mouse location and mouse current location
        offset_x = int(event.globalX()) - self.initial_pos_arrow_x
        offset_y = int(event.globalY()) - self.initial_pos_arrow_y
        # Calculate the Cancel button's x,y coords based on that offset
        new_cancel_x_position = self.initial_cancel_btn_x + offset_x - self.mouse_offset_x
        new_cancel_y_position = self.initial_cancel_btn_y + offset_y - self.mouse_offset_y
        if new_cancel_x_position >= 5 and new_cancel_y_position >= 25:
            # Move the arrow and Cancel button
            self.cancelBtnPosArrow.move(new_cancel_x_position + int(self.simlogin_window_group.x()),
                                        new_cancel_y_position + int(self.simlogin_window_group.y()))
            self.simcancelbtn.move(new_cancel_x_position, new_cancel_y_position)
            # Move the Size arrow...
            self.cancelBtnSizeArrow.move(self.initial_size_arrow_x + offset_x - self.mouse_offset_x,
                                         self.initial_size_arrow_y + offset_y - self.mouse_offset_y)
            # Update the Cancel button x, y spinboxes
            self.btnDialog.cancel_x_spinBox.setValue(new_cancel_x_position - int(self.simloginwindow.x()))
            self.btnDialog.cancel_y_spinBox.setValue(new_cancel_y_position - int(self.simloginwindow.y()))

        self.btnDialog.cancel_x_spinBox.blockSignals(False)
        self.btnDialog.cancel_y_spinBox.blockSignals(False)

    def windowDialogButtonsOKResizeArrowInitialClick(self, event):
        self.btnDialog.ok_width_spinBox.blockSignals(True)
        self.btnDialog.ok_height_spinBox.blockSignals(True)
        # Save the current global mouse position so we can calculate the offset
        self.initial_mouse_x = int(event.globalX())
        self.initial_mouse_y = int(event.globalY())
        # Move the arrow to current location of OK button
        xpos = int(self.simokbtn.x()) + int(self.simlogin_window_group.x())
        ypos = int(self.simokbtn.y()) + int(self.simlogin_window_group.y())
        self.okBtnPosArrow.move(xpos, ypos)
        # Save the initial position arrow x & y coords
        self.initial_pos_arrow_x = int(self.okBtnPosArrow.x())
        self.initial_pos_arrow_y = int(self.okBtnPosArrow.y())
        # Save the initial Size Arrow coords
        self.initial_size_arrow_x = int(self.OkBtnSizeArrow.x())
        self.initial_size_arrow_y = int(self.OkBtnSizeArrow.y())
        # save the Initial OK button X position
        self.initial_okbtn_x = int(self.simokbtn.x())
        self.initial_okbtn_y = int(self.simokbtn.y())
        # Calculate the offset between current mouse location and
        # The ORIGIN OF THE position ARROW...
        # This gives us a way of moving the arrow without things jumping all
        # over the place!
        self.mouse_offset_x = int(event.globalX()) - self.initial_size_arrow_x
        self.mouse_offset_y = int(event.globalY()) - self.initial_size_arrow_y

    # noinspection PyUnusedLocal
    def windowDialogButtonsOKSizeArrowReleased(self, arg):
        self.okbtn_width = self.simokbtn.width()
        self.okbtn_height = self.simokbtn.height()
        self.okbtn_xpos = self.simokbtn.x()
        self.okbtn_ypos = self.simokbtn.y()
        self.btnDialog.ok_width_spinBox.blockSignals(False)
        self.btnDialog.ok_height_spinBox.blockSignals(False)

    def windowDialogButtonsOKSizeArrowMoving(self, event):
        # Calculate the offset between original mouse location and mouse current location
        offset_x = int(event.globalX()) - self.initial_size_arrow_x
        offset_y = int(event.globalY()) - self.initial_size_arrow_y
        # Calculate the size arrow's new x,y coords based on that offset
        new_x = self.initial_size_arrow_x + offset_x - self.mouse_offset_x
        new_y = self.initial_size_arrow_y + offset_y - self.mouse_offset_y
        # Move the resize arrow
        self.OkBtnSizeArrow.move(new_x, new_y)
        # Resize dat OK button
        new_width = self.okbtn_width + offset_x - self.mouse_offset_x
        new_height = self.okbtn_height + offset_y - self.mouse_offset_y
        #print(new_width, new_height)
        ok_x = int(self.simokbtn.x())
        ok_y = int(self.simokbtn.y())
        self.simokbtn.setMaximumWidth(new_width)
        self.simokbtn.setMaximumHeight(new_height)
        self.simokbtn.setGeometry(ok_x, ok_y, new_width, new_height)
        # Update OK Button width & Height Spinboxen
        self.btnDialog.ok_width_spinBox.setValue(new_width)
        self.btnDialog.ok_height_spinBox.setValue(new_height)

    def windowDialogButtonsCancelResizeArrowInitialClick(self, event):
        self.btnDialog.cancel_width_spinBox.blockSignals(True)
        self.btnDialog.cancel_height_spinBox.blockSignals(True)
        # Save the current global mouse position so we can calculate the offset
        self.initial_mouse_x = int(event.globalX())
        self.initial_mouse_y = int(event.globalY())
        # Move the arrow to current location of OK button
        xpos = int(self.simcancelbtn.x()) + int(self.simlogin_window_group.x())
        ypos = int(self.simcancelbtn.y()) + int(self.simlogin_window_group.y())
        self.cancelBtnPosArrow.move(xpos, ypos)
        # Save the initial position arrow x & y coords
        self.initial_pos_arrow_x = int(self.cancelBtnPosArrow.x())
        self.initial_pos_arrow_y = int(self.cancelBtnPosArrow.y())
        # Save the initial Size Arrow coords
        self.initial_size_arrow_x = int(self.cancelBtnSizeArrow.x())
        self.initial_size_arrow_y = int(self.cancelBtnSizeArrow.y())
        # save the Initial OK button X position
        self.initial_cancel_btn_x = int(self.simcancelbtn.x())
        self.initial_cancel_btn_y = int(self.simcancelbtn.y())
        # Calculate the offset between current mouse location and
        # The ORIGIN OF THE position ARROW...
        # This gives us a way of moving the arrow without things jumping all
        # over the place!
        self.mouse_offset_x = int(event.globalX()) - self.initial_size_arrow_x
        self.mouse_offset_y = int(event.globalY()) - self.initial_size_arrow_y

    def windowDialogButtonsCancelSizeArrowMoving(self, event):
        # Calculate the offset between original mouse location and mouse current location
        offset_x = int(event.globalX()) - self.initial_size_arrow_x
        offset_y = int(event.globalY()) - self.initial_size_arrow_y
        # Calculate the size arrow's new x,y coords based on that offset
        new_x = self.initial_size_arrow_x + offset_x - self.mouse_offset_x
        new_y = self.initial_size_arrow_y + offset_y - self.mouse_offset_y
        # Move the resize arrow
        self.cancelBtnSizeArrow.move(new_x, new_y)
        # Resize dat OK button
        new_width = self.cancelbtn_width + offset_x - self.mouse_offset_x
        new_height = self.cancelbtn_height + offset_y - self.mouse_offset_y
        #print(new_width, new_height)
        x = int(self.simcancelbtn.x())
        y = int(self.simcancelbtn.y())
        self.simcancelbtn.setMaximumWidth(new_width)
        self.simcancelbtn.setMaximumHeight(new_height)
        self.simcancelbtn.setGeometry(x, y, new_width, new_height)
        # Update OK Button width & Height Spinboxen
        self.btnDialog.cancel_width_spinBox.setValue(new_width)
        self.btnDialog.cancel_height_spinBox.setValue(new_height)

    # noinspection PyUnusedLocal
    def windowDialogButtonsCancelSizeArrowReleased(self, arg):
        self.cancelbtn_width = self.simcancelbtn.width()
        self.cancelbtn_height = self.simcancelbtn.height()
        self.cancelbtn_xpos = self.simcancelbtn.x()
        self.cancelbtn_ypos = self.simcancelbtn.y()
        self.btnDialog.cancel_width_spinBox.blockSignals(False)
        self.btnDialog.cancel_height_spinBox.blockSignals(False)

    def windowDialogBoxesBtnClicked(self):
        # Stop the Dialog Window from being moved
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, False)
        # save a copy of the original modulebox text & box positions
        self.orig_mod_text_xpos = self.mod_text_xpos
        self.orig_mod_box_xpos = self.mod_box_xpos
        self.orig_mod_box_ypos = self.mod_box_ypos

        # Create a dialog for the box/labels positioning
        self.boxesDialog = LabelsAndBoxesWidget()
        self.boxesDialog.okBtn.clicked.connect(self.windowDialogBoxesAccepted)
        self.boxesDialog.cancelBtn.clicked.connect(self.windowDialogBoxesRejected)

        self.boxesDialog.move(self.winSim.width() - self.boxesDialog.width() - 25, 0)
        self.simscene.addWidget(self.boxesDialog)
        # Update the positioning dialog with the current values
        self.boxesDialog.labels_x_spinbox.setValue(self.pass_text_xpos)
        self.boxesDialog.boxes_x_spinbox.setValue(self.mod_box_xpos)
        self.boxesDialog.boxes_y_spinbox.setValue(self.mod_box_ypos)
        self.boxesDialog.boxes_w_spinbox.setValue(self.boxlength)
        # Store "old" values of spinboxes, for later use...
        self.old_boxes_X_spinbox_value = self.mod_box_xpos
        self.old_boxes_Y_spinbox_value = self.mod_box_ypos
        # Connect spinbox value changed signals to valuechanged handler...
        # self.boxesDialog.labels_x_spinbox.valueChanged.connect(self.windowDialogLabelsSpinBoxValueChanged)
        # Create a positioning arrow for the labels positioning
        self.labelsArrow = ClickableQLabel(QtGui.QPixmap(":/dragpoint/images/dragpoints/Arrow_topleft.png"))
        self.labelsArrow.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.labelsArrow.setToolTip("Drag to set Labels X coordinate")
        # Move the arrow to the current location of the labels
        # NOTE : moduletext coordinates are LOCAL to their parent widget (loginrect)!!!
        # So first - calculate the global x and y pos of the moduletext...
        xpos = self.simlogin_window_group.x() + self.simmoduletext.x()
        ypos = self.simlogin_window_group.y() + self.simmoduletext.y()
        self.labelsArrow.move(xpos, ypos + 4)

        # Connect the LabelsArrow's signals to the handler functions
        self.labelsArrow.clicked.connect(self.windowDialogBoxesLabelsInitialClick)
        self.labelsArrow.moved.connect(self.windowDialogBoxesLabelsMoving)
        # Display the dialogue
        self.simscene.addWidget(self.labelsArrow)
        # Save the initial arrow x & y coords
        self.initial_labelsarrow_x = int(self.labelsArrow.x())
        self.initial_labelsarrow_y = int(self.labelsArrow.y())

        # Create a positioning arrow for the Boxes X/Y axes
        self.boxes_XY_Arrow = ClickableQLabel(QtGui.QPixmap(":/dragpoint/images/dragpoints/Arrow_topleft.png"))
        self.boxes_XY_Arrow.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.boxes_XY_Arrow.setToolTip("Drag to set Boxes/Labels Y, and Boxes X Coordinate")

        # Move the Boxes XY Arrow to the current location of the modulebox
        xpos = self.simlogin_window_group.x() + self.simmodulebox.x() - 2
        ypos = self.simlogin_window_group.y() + self.simmodulebox.y() - 2
        self.boxes_XY_Arrow.move(xpos, ypos)
        # Save the initial Boxes XY Arrow coords
        self.initial_bx_xyArrow_x = int(self.boxes_XY_Arrow.x())
        self.initial_bx_xyArrow_y = int(self.boxes_XY_Arrow.y())

        self.boxes_XY_Arrow.clicked.connect(self.windowDialogBoxesXYInitialClick)
        self.boxes_XY_Arrow.moved.connect(self.windowDialogBoxesXYmoving)
        #self.boxes_XY_Arrow.released.connect(self.windowDialogBoxesXYReleased)
        self.simscene.addWidget(self.boxes_XY_Arrow)

        # Connect boxes X & Y SPinbox value changed signal to windowDialogBoxesXYSpinboxValueChanged()
        # self.boxesDialog.boxes_x_spinbox.valueChanged.connect(self.windowDialogBoxesXYSpinboxValueChanged)
        # self.boxesDialog.boxes_y_spinbox.valueChanged.connect(self.windowDialogBoxesXYSpinboxValueChanged)

        # Disable the buttons at the top of the LWS (prevent user activating other functions)
        self.winSim.DialogGroupBox.setEnabled(False)
        self.winSim.ColoursGroupBox.setEnabled(False)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, False)
        self.winSim.boxesLocationBtn.setStyleSheet(self.colourbutton_stylesheet)

    # This is for when the LABELS are being moved.
    def windowDialogBoxesLabelsInitialClick(self, event):
        # Save the current global mouse position so we can calculate the offset
        self.initial_mouse_x = int(event.globalX())
        self.initial_mouse_y = int(event.globalY())
        # Save the initial Labels arrow x & y coords
        self.initial_labelsarrow_x = int(self.labelsArrow.x())
        self.initial_labelsarrow_y = int(self.labelsArrow.y())
        # save the Initial text label X position
        self.initial_text_x = int(self.simmoduletext.x())
        self.initial_text_y = int(self.simmoduletext.y())
        # Calculate the offset between current mouse location and
        # The ORIGIN OF THE Boxes XY ARROW...
        # This gives us a way of moving the arrow without things jumping all
        # over the place!
        self.mouse_offset_x = int(event.globalX()) - self.initial_labelsarrow_x
        self.mouse_offset_y = int(event.globalY()) - self.initial_labelsarrow_y

    # This is for when the BOXES are being moved
    # noinspection PyAttributeOutsideInit
    def windowDialogBoxesXYInitialClick(self, event):
        # Save the current global mouse position so we can calculate the offset
        self.initial_mouse_x = int(event.globalX())
        self.initial_mouse_y = int(event.globalY())

        # save the Boxes XY Arrow values
        self.initial_bx_xyArrow_x = int(self.boxes_XY_Arrow.x())
        self.initial_bx_xyArrow_y = int(self.boxes_XY_Arrow.y())

        # Save the initial Labels arrow x & y coords
        self.initial_labelsarrow_x = int(self.labelsArrow.x())
        self.initial_labelsarrow_y = int(self.labelsArrow.y())

        # save the Initial text label X position
        self.initial_text_x = int(self.simmoduletext.x())
        self.initial_text_y = int(self.simmoduletext.y())
        # Calculate the offset between current mouse location and
        # The ORIGIN OF THE Boxes XY ARROW...
        # This gives us a way of moving the arrow without things jumping all
        # over the place!
        self.mouse_offset_x = int(event.globalX()) - self.initial_bx_xyArrow_x
        self.mouse_offset_y = int(event.globalY()) - self.initial_bx_xyArrow_y
        self.windowDialogBoxesSnapshotCoords()

    # noinspection PyAttributeOutsideInit
    def windowDialogBoxesSnapshotCoords(self):
        # Snapshot the X & Y coords of the Shadebox
        self.shade_x = int(self.simmoduShading.topline.x())
        self.shade_y = int(self.simmoduShading.topline.y())

        #Snapshot the coords of the module combobox
        self.initial_mod_x = int(self.simmodproxy.x())
        self.initial_mod_y = int(self.simmodproxy.y())

        # Snapshot the coords of the username entrybox
        self.initial_user_x = int(self.simuserproxy.x())
        self.initial_user_y = int(self.simuserproxy.y())

        # Snapshot coords of pasword entrybox
        self.initial_pass_x = int(self.simpassproxy.x())
        self.initial_pass_y = int(self.simpassproxy.y())

    def windowDialogBoxesLabelsMoving(self, event):
        # Calculate the offset between original mouse location and mouse current location
        offset_x = int(event.globalX()) - self.initial_labelsarrow_x
        # Calculate the label x-axis based on that offset
        new_label_x_position = self.initial_text_x + offset_x - self.mouse_offset_x
        # Prevent text from going too far to the left of the current dialog window
        if new_label_x_position < 5:
            new_label_x_position = 5
        # Calculate xpos of arrow based on offset of where mouse was clicked on arrow
        # new_arrow_x = self.initial_labelsarrow_x + offset_x - self.mouse_offset_x
        xpos = self.initial_labelsarrow_x + offset_x - self.mouse_offset_x
        # Only move the arrow if it's not going beyond the left of the dialog box
        if xpos >= int(self.simlogin_window_group.x()) + 5:
            # Move the arrow with the cursor, along the x-axis
            self.labelsArrow.move(xpos, self.initial_labelsarrow_y)
        # Update the moduletext position with the new x value
        self.mod_text_xpos = new_label_x_position
        # Calculate the positions of the other text labels
        self.updateDialogCalculateLabelBoxesPositions()
        # Update the positions on-screen
        self.windowDialogSetLabelsPosition()
        # Update the spinbox
        self.boxesDialog.labels_x_spinbox.blockSignals(True)
        self.boxesDialog.labels_x_spinbox.setValue(new_label_x_position)
        self.boxesDialog.labels_x_spinbox.blockSignals(False)

    def windowDialogBoxesXYmoving(self, event):
        # Calculate the offset between original mouse location and mouse current location
        offset_x = int(event.globalX()) - self.initial_bx_xyArrow_x
        offset_y = int(event.globalY()) - self.initial_bx_xyArrow_y

        # Calculate the label y-axis based on that offset
        new_label_y_position = self.initial_text_y + offset_y - self.mouse_offset_y

        # Calculate the labels Arrow position
        new_labelsArrow_y = self.initial_labelsarrow_y + offset_y - self.mouse_offset_y

        # Calculate the new Input Boxes X & Y position
        new_input_x_pos = self.initial_mod_x + offset_x - self.mouse_offset_x
        new_input_y_pos = self.initial_mod_y + offset_y - self.mouse_offset_y

        # Calculate the new XY-Arrow x & y points based on the offsets
        # between original location and the currently dragging mouse's Global position
        new_arrow_x = self.initial_bx_xyArrow_x + offset_x - self.mouse_offset_x
        new_arrow_y = self.initial_bx_xyArrow_y + offset_y - self.mouse_offset_y

        if new_input_y_pos >= 25:
            # Move the Labels arrow according to the new Y point...
            self.labelsArrow.move(self.initial_labelsarrow_x, new_labelsArrow_y)
            # Update and recalculate the Labels positions...
            self.mod_text_ypos = new_label_y_position
            self.updateDialogCalculateLabelsPositions()
            self.windowDialogSetLabelsPosition()
            self.boxes_XY_Arrow.move(new_arrow_x, new_arrow_y)
            # Calculate the shadeboxes x + y points...
            shade_x = self.shade_x + offset_x - self.mouse_offset_x
            shade_y = self.shade_y + offset_y - self.mouse_offset_y

            # Move the Module combobox, and Username and Password entryfields...
            self.simmodproxy.setPos(self.initial_mod_x + offset_x - self.mouse_offset_x,
                                    self.initial_mod_y + offset_y - self.mouse_offset_y)
            self.simuserproxy.setPos(self.initial_user_x + offset_x - self.mouse_offset_x,
                                     self.initial_user_y + offset_y - self.mouse_offset_y)
            self.simpassproxy.setPos(self.initial_pass_x + offset_x - self.mouse_offset_x,
                                     self.initial_pass_y + offset_y - self.mouse_offset_y)
            # Move the Shadeboxes as well...
            self.simmoduShading.move(shade_x, shade_y)
            self.simuserShading.move(shade_x, shade_y)
            self.simpassShading.move(shade_x, shade_y)

            # Update the boxes X & Y SpinBoxes with the new values...
            self.boxesDialog.boxes_x_spinbox.blockSignals(True)
            self.boxesDialog.boxes_y_spinbox.blockSignals(True)
            self.boxesDialog.boxes_x_spinbox.setValue(new_input_x_pos)
            self.boxesDialog.boxes_y_spinbox.setValue(new_input_y_pos)
            self.boxesDialog.boxes_x_spinbox.blockSignals(False)
            self.boxesDialog.boxes_y_spinbox.blockSignals(False)

            self.mod_box_xpos = new_input_x_pos
            self.mod_box_ypos = new_input_y_pos

            # Store values of spinboxes
            self.old_boxes_X_spinbox_value = new_input_x_pos
            self.old_boxes_Y_spinbox_value = new_input_y_pos

#    def windowDialogBoxesXYSpinboxValueChanged(self):
#        # Get current positions of the boxes...
#        self.windowDialogBoxesSnapshotCoords()
#
#        # Get Values of the spinboxes...
#        spinbox_X = self.boxesDialog.boxes_x_spinbox.value()
#        spinbox_Y = self.boxesDialog.boxes_y_spinbox.value()
#
#        #if spinbox_X != self.old_boxes_X_spinbox_value or spinbox_Y != self.old_boxes_Y_spinbox_value:
#        self.windowDialogBoxesXYSpinboxMoveBoxes(spinbox_X, spinbox_Y)

#    def windowDialogBoxesXYSpinboxMoveBoxes(self, spinbox_X, spinbox_Y):
        # Make sure values don't go below 5 for X and 25 for Y...
#        if spinbox_X < 5:
#            spinbox_X = 5
#        if spinbox_Y < 25:
#            spinbox_Y = 25

        # Move the Boxes-XY arrow
#        self.boxes_XY_Arrow.move(spinbox_X + self.simlogin_window_group.x(), spinbox_Y + self.simlogin_window_group.y())

        # Move the Boxes and their Shading
#        self.simmodproxy.setPos(spinbox_X + 2, spinbox_Y + 2)
#        self.simmoduShading.position(spinbox_X, spinbox_Y, self.boxlength)
#        self.simuserproxy.setPos(spinbox_X + 2, spinbox_Y + 2 + 26)
#        self.simuserShading.position(spinbox_X, spinbox_Y + 26, self.boxlength)
#        self.simpassproxy.setPos(spinbox_X + 2, spinbox_Y + 2 + 52)
#        self.simpassShading.position(spinbox_X, spinbox_Y + 52, self.boxlength)

        # Move the labels arrow...
#        self.labelsArrow.move(self.initial_labelsarrow_x, spinbox_Y + self.simlogin_window_group.y())

        # Move the labels...
#        new_label_y_position = spinbox_Y - 5
#        self.mod_text_ypos = new_label_y_position
#        self.updateDialogCalculateLabelsPositions()
#        self.windowDialogSetLabelsPosition()

#    def windowDialogBoxesXYReleased(self):
#        pass

#    def windowDialogLabelsSpinBoxValueChanged(self):
#        self.mod_text_xpos = int(self.boxesDialog.labels_x_spinbox.value())
#        self.updateDialogCalculateLabelsPositions()
#        self.windowDialogSetLabelsPosition()
#        # Calculate xpos of arrow based on offset of where mouse was clicked on arrow
#        xpos = self.simlogin_window_group.x() + self.mod_text_xpos
        #if xpos < 5: xpos = 5
        # Move the arrow with the cursor, along the x-axis
#        self.labelsArrow.move(xpos, self.initial_labelsarrow_y)

    def windowDialogBoxesAccepted(self):
        self.xrdp_ini_file.set('globals', 'ls_label_x_pos', str(self.mod_text_xpos))
        self.xrdp_ini_file.set('globals', 'ls_input_y_pos', str(self.mod_box_ypos))
        self.xrdp_ini_file.set('globals', 'ls_input_x_pos', str(self.mod_box_xpos))
        self.xrdp_ini_file.set('globals', 'ls_input_width', str(self.boxlength))
        self.labelsArrow.deleteLater()
        self.boxes_XY_Arrow.deleteLater()
        self.boxesDialog.deleteLater()
        self.winSim.DialogGroupBox.setEnabled(True)
        self.winSim.ColoursGroupBox.setEnabled(True)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, True)
        self.winSim.boxesLocationBtn.setStyleSheet("")
        self.xrdp_changed()

    def windowDialogBoxesRejected(self):
        self.mod_text_xpos = self.orig_mod_text_xpos
        self.mod_box_xpos = self.orig_mod_box_xpos
        self.mod_box_ypos = self.orig_mod_box_ypos
        self.updateDialogCalculateLabelsPositions()

        self.updateDialogCalculateLabelBoxesPositions()
        self.windowDialogSetLabelsPosition()
        self.labelsArrow.deleteLater()
        self.boxes_XY_Arrow.deleteLater()
        self.boxesDialog.deleteLater()
        self.winSim.DialogGroupBox.setEnabled(True)
        self.winSim.ColoursGroupBox.setEnabled(True)
        self.simlogin_window_group.setFlag(QtGui.QGraphicsItemGroup.ItemIsMovable, True)
        self.winSim.boxesLocationBtn.setStyleSheet("")

    def updateDialogCalculateLabelsPositions(self):
        self.user_text_xpos = self.mod_text_xpos
        self.user_text_ypos = self.mod_text_ypos + 26
        self.pass_text_xpos = self.mod_text_xpos
        self.pass_text_ypos = self.mod_text_ypos + 52

    def updateDialogCalculateLabelBoxesPositions(self):
        self.mod_box_xpos = self.mod_text_xpos + 85
        self.mod_box_ypos = self.mod_text_ypos + 4

        self.user_text_xpos = self.mod_text_xpos
        self.user_text_ypos = self.mod_text_ypos + 26

        self.pass_text_xpos = self.mod_text_xpos
        self.pass_text_ypos = self.mod_text_ypos + 52

        self.user_box_xpos = self.user_text_xpos + 85
        self.pass_box_xpos = self.pass_text_xpos + 85

        self.user_box_ypos = self.user_text_ypos + 4
        self.pass_box_ypos = self.pass_text_ypos + 4

    def windowDialogSetLabelsPosition(self):
        self.simmoduletext.setPos(self.mod_text_xpos, self.mod_text_ypos)
        self.simusernametext.setPos(self.user_text_xpos, self.user_text_ypos)
        self.simpasswordtext.setPos(self.pass_text_xpos, self.pass_text_ypos)

    # This function updates the stylesheet for the username & password boxes...
    def updateUserPassStylesheet(self):
        textcolour = QtGui.QColor(self.simmoduletext.defaultTextColor()).name()
        boxes = QtGui.QColor(self.simloginwindow.topline.pen().color()).name()

        stylesheet = 'QLineEdit { ' \
                    'color: ' + textcolour + '; ' \
                    'background: ' + boxes + '; ' \
                    'lineedit-password-character: 42; ' \
                    'padding: 0 1px; ' \
                    '} '

        self.simusernamebox.setStyleSheet(stylesheet)
        self.simpassbox.setStyleSheet(stylesheet)

    # This function updates the stylesheet for the OK/Cancel/Help buttons...
    def updateButtonStyles(self):
        background = QtGui.QColor(self.simloginwindow.loginrect.brush().color()).name()
        top = QtGui.QColor(self.simloginwindow.topline.pen().color()).name()
        right = QtGui.QColor(self.simloginwindow.rightline.pen().color()).name()
        bottom = QtGui.QColor(self.simmoduShading.topline.pen().color()).name()
        left = QtGui.QColor(self.simloginwindow.leftline.pen().color()).name()
        textcolour = QtGui.QColor(self.simmoduletext.defaultTextColor()).name()

        # set button stylesheet...
        # border-width : TOP , RIGHT , BOTTOM , LEFT
        okbtnstylesheet = 'QPushButton { background-color: ' + background + '; ' \
                        'color: ' + textcolour + '; ' \
                        'border-top-color: ' + top + '; ' \
                        'border-left-color: ' + left + '; ' \
                        'border-bottom-color: ' + bottom + '; ' \
                        'border-right-color: ' + right + '; ' \
                        'border-width: 1px 2px 2px 1px; ' \
                        'border-radius: 0px; ' \
                        'border-style: outset; ' \
                        'padding: 3px;' \
                        ' } ' \
                         'QPushButton:pressed { ' \
                        'color: ' + textcolour + '; ' \
                        'border-top-color: ' + right + '; ' \
                        'border-left-color: ' + right + '; ' \
                        'border-bottom-color: ' + bottom + '; ' \
                        'border-right-color: ' + right + '; ' \
                        'border-width: 2px 2px 2px 2px; ' \
                        'border-radius: 0px; ' \
                        'border-style: outset; ' \
                        'padding: 3px; ' \
                        ' } ' \
                        'QPushButton:focus { ' \
                        'outline: 1px dotted outset #000000;' \
                        ' } '

        cancelbtnstylesheet = 'QPushButton { background-color: ' + background + '; ' \
                        'color: ' + textcolour + '; ' \
                        'border-top-color: ' + top + '; ' \
                        'border-left-color: ' + left + '; ' \
                        'border-bottom-color: ' + bottom + '; ' \
                        'border-right-color: ' + right + '; ' \
                        'border-width: 1px 2px 2px 1px; ' \
                        'border-radius: 0px; ' \
                        'border-style: outset; ' \
                        'padding: 3px;' \
                        ' } ' \
                        'QPushButton:pressed { ' \
                        'color: ' + textcolour + '; ' \
                        'border-top-color: ' + right + '; ' \
                        'border-left-color: ' + right + '; ' \
                        'border-bottom-color: ' + bottom + '; ' \
                        'border-right-color: ' + right + '; ' \
                        'border-width: 2px 2px 2px 2px; ' \
                        'border-radius: 0px; ' \
                        'border-style: outset; ' \
                        'padding: 3px; ' \
                        ' } ' \
                        'QPushButton:focus { ' \
                        'outline: 1px dotted outset #000000;' \
                        ' } '

        helpbtnstylesheet = 'QPushButton { background-color: ' + background + '; ' \
                        'color: ' + textcolour + '; ' \
                        'border-top-color: ' + top + '; ' \
                        'border-left-color: ' + left + '; ' \
                        'border-bottom-color: ' + bottom + '; ' \
                        'border-right-color: ' + right + '; ' \
                        'border-width: 1px 2px 2px 1px; ' \
                        'border-radius: 0px; ' \
                        'border-style: outset; ' \
                        'padding: 3px;' \
                        ' } ' \
                        'QPushButton:pressed { ' \
                        'color: ' + textcolour + '; ' \
                        'border-top-color: ' + right + '; ' \
                        'border-left-color: ' + right + '; ' \
                        'border-bottom-color: ' + bottom + '; ' \
                        'border-right-color: ' + right + '; ' \
                        'border-width: 2px 2px 2px 2px; ' \
                        'border-radius: 0px; ' \
                        'border-style: outset; ' \
                        'padding: 3px; ' \
                        ' } ' \
                        'QPushButton:focus { ' \
                        'outline: 1px dotted outset #000000;' \
                        ' } '

        self.simokbtn.setStyleSheet(okbtnstylesheet)
        self.simcancelbtn.setStyleSheet(cancelbtnstylesheet)
        if not self.new_version_flag:
            self.simhelpbtn.setStyleSheet(helpbtnstylesheet)
            self.simhelpbtn.setMaximumWidth(self.helpbtn_width)
            self.simhelpbtn.setMaximumHeight(self.helpbtn_height)
        self.simokbtn.setMaximumWidth(self.okbtn_width)
        self.simokbtn.setMaximumHeight(self.okbtn_height)
        self.simcancelbtn.setMaximumWidth(self.cancelbtn_width)
        self.simcancelbtn.setMaximumHeight(self.cancelbtn_height)

    # This function updates the stylesheet for the Session ComboBox...
    def updateModuleStylesheet(self):
        background = QtGui.QColor(self.simloginwindow.loginrect.brush().color()).name()
        top = QtGui.QColor(self.simloginwindow.topline.pen().color()).name()
        right = QtGui.QColor(self.simloginwindow.rightline.pen().color()).name()
        bottom = QtGui.QColor(self.simmoduShading.topline.pen().color()).name()
        left = QtGui.QColor(self.simloginwindow.leftline.pen().color()).name()
        boxes = QtGui.QColor(self.simloginwindow.topline.pen().color()).name()
        textcolour = QtGui.QColor(self.simmoduletext.defaultTextColor()).name()
        bannercolour = QtGui.QColor(self.simloginwindow.loginbanner.pen().color()).name()

        module_stylesheet = \
            'QComboBox { ' \
            'border: 0px; ' \
            'margin: 0px; ' \
            'border-style: none; ' \
            'color: ' + textcolour + '; ' \
            'background: ' + boxes + '; } ' \
            'QComboBox:open { ' \
            'background: ' + self.dark_blue.name() + '; ' \
            'color: ' + boxes + ';' \
            ' } ' \
            'QComboBox::focus { ' \
            'background: ' + self.dark_blue.name() + '; ' \
            'color: ' + boxes + ';' \
            ' } ' \
            'QComboBox QAbstractItemView { ' \
            'outline: none; ' \
            'border: 0px; ' \
            'padding: 0px; ' \
            'margin-left: 0px; ' \
            'width: ' + str(self.boxlength) + '; ' \
            'subcontrol-origin: padding; ' \
            'border-radius: 0px; ' \
            'background: ' + boxes + '; ' \
            'selection-background-color: ' + bannercolour + '; ' \
            'selection-color: ' + boxes + '; ' \
            ' } ' \
            'QComboBox::drop-down { ' \
            'subcontrol-origin: margin; ' \
            'margin: 0px; ' \
            'subcontrol-position: right top; ' \
            'border-width: 2px 2px 2px 2px; ' \
            'border-radius: 0px; ' \
            'border-style: outset; ' \
            'background-color: ' + background + '; ' \
            'width: 14px; ' \
            'border-color: ' + top + ' ' + right + ' ' + bottom + ' ' + '; ' \
            ' } ' \
            'QComboBox::down-arrow { ' \
            'image: url(:/modulebox/images/modulebox/down-arrow.png); ' \
            'border-width: 2px 2px 2px 2px; ' \
            'border-color: ' + top + ' ' + right + ' ' + bottom + ' ' + left + '; ' \
            ' } '

        self.simmodulebox.setStyleSheet(module_stylesheet)

    def winSimResized(self):
        # This calculates and repositions the colour dialog, if the LoginSim window was resized.
        self.simscene.setSceneRect(QtCore.QRectF(self.winSim.xrdp_window.viewport().rect()))
        self.simlogin_window_group.restrict_rect = self.winSim.xrdp_window.sceneRect()
        self.colour_chooser.move(self.winSim.width() - 570, self.winSim.xrdp_window.y())

    def setupColourSelector(self):
        # This sets up the colour dialog such that it appears to be within the LoginSim window, instead of a
        # seperate window. It's also made slightly transparent. A nice trick - it means we can prevent the LoginSim
        # window and contents from being dimmed because the colour dialog window is in front of it. This good because
        # then you can show a proper real time update on colour changes without the window dimming in some desktop
        # window managers.
        self.colour_chooser = ColourWidget(winSim)
        self.colour_chooser.setStyleSheet("background-color: rgba(255,255,255, 60%);")
        self.colour_chooser.hide()
        self.colour_chooser.setWindowFlags(QtCore.Qt.Widget)
        self.colour_chooser.setOptions(QtGui.QColorDialog.DontUseNativeDialog)
        self.colour_chooser.setAttribute(QtCore.Qt.WA_DontShowOnScreen, True)

    def hideColourSelector(self, colourUpdater, accepted, rejected, finished):
        self.colour_chooser.blockSignals(True)
        self.colour_chooser.hide()
        self.colour_chooser.currentColorChanged.disconnect(colourUpdater)
        self.colour_chooser.accepted.disconnect(accepted)
        self.colour_chooser.rejected.disconnect(rejected)
        self.colour_chooser.finished.disconnect(finished)
        self.winSim.DialogGroupBox.setEnabled(True)
        self.winSim.ColoursGroupBox.setEnabled(True)

    def showColourSelector(self, original_colour, colourUpdater, accepted, rejected, finished):
        self.colour_chooser.move(self.winSim.width() - 570, self.winSim.xrdp_window.y())
        self.colour_chooser.show()
        self.colour_chooser.setCurrentColor(original_colour)
        self.colour_chooser.blockSignals(True)
        self.colour_chooser.currentColorChanged.connect(colourUpdater)
        self.colour_chooser.accepted.connect(accepted)
        self.colour_chooser.rejected.connect(rejected)
        self.colour_chooser.finished.connect(finished)
        self.colour_chooser.blockSignals(False)
        self.winSim.DialogGroupBox.setEnabled(False)
        self.winSim.ColoursGroupBox.setEnabled(False)

    def disableButtons(self):
        self.winSim.background_Pushbutton.setEnabled(False)
        self.winSim.grey_Pushbutton.setEnabled(False)
        self.winSim.blue_Pushbutton.setEnabled(False)
        self.winSim.black_Pushbutton.setEnabled(False)
        self.winSim.white_Pushbutton.setEnabled(False)
        self.winSim.dark_grey_Pushbutton.setEnabled(False)
        self.winSim.dark_blue_Pushbutton.setEnabled(False)
        self.winSim.resetBackgroundButton.setEnabled(False)
        self.winSim.resetWindowButton.setEnabled(False)
        self.winSim.resetTitleBgndButton.setEnabled(False)
        self.winSim.resetTextButton.setEnabled(False)
        self.winSim.resetTopLeftTitleBoxesBtn.setEnabled(False)
        self.winSim.resetBottomRightBtn.setEnabled(False)
        self.winSim.resetSessionBoxHilightBtn.setEnabled(False)

    def enableButtons(self):
        self.winSim.background_Pushbutton.setEnabled(True)
        self.winSim.grey_Pushbutton.setEnabled(True)
        self.winSim.blue_Pushbutton.setEnabled(True)
        self.winSim.black_Pushbutton.setEnabled(True)
        self.winSim.white_Pushbutton.setEnabled(True)
        self.winSim.dark_grey_Pushbutton.setEnabled(True)
        self.winSim.dark_blue_Pushbutton.setEnabled(True)
        self.winSim.resetBackgroundButton.setEnabled(True)
        self.winSim.resetWindowButton.setEnabled(True)
        self.winSim.resetTitleBgndButton.setEnabled(True)
        self.winSim.resetTextButton.setEnabled(True)
        self.winSim.resetTopLeftTitleBoxesBtn.setEnabled(True)
        self.winSim.resetBottomRightBtn.setEnabled(True)
        self.winSim.resetSessionBoxHilightBtn.setEnabled(True)

    # "background="
    def loginSimulatorSelectBackground(self):
        self.disableButtons()
        self.winSim.show()
        self.winSim.background_Pushbutton.setStyleSheet(self.colourbutton_stylesheet)
        self.original_colour = self.winSim.xrdp_window.backgroundBrush().color()
        self.showColourSelector(self.original_colour, self.selectBackgroundUpdater, self.selectbackgroundaccepted,
                          self.selectbackgroundcancelled, self.selectbackgroundfinished)

    def selectBackgroundUpdater(self, colour):
        self.winSim.xrdp_window.setBackgroundBrush(colour)
        self.winSim.backgroundView.setBackgroundBrush(colour)

    def selectbackgroundaccepted(self):
        self.xrdp_changed()
        self.enableButtons()
        if self.new_version_flag:
            colour = self.colour_chooser.currentColor().name()[1:]
            self.xrdp_ini_file.set('globals', 'ls_top_window_bg_color', colour)
        else:
            self.xrdp_ini_file.set('globals', 'background', str(self.colour_chooser.currentColor().name()[1:]))
        self.hideColourSelector(self.selectBackgroundUpdater, self.selectbackgroundaccepted,
                                self.selectbackgroundcancelled, self.selectbackgroundfinished)

    def selectbackgroundcancelled(self):
        brush = QtGui.QBrush(QtGui.QColor(self.original_colour))
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.winSim.xrdp_window.setBackgroundBrush(brush)
        self.winSim.backgroundView.setBackgroundBrush(self.original_colour)
        self.enableButtons()
        self.hideColourSelector(self.selectBackgroundUpdater, self.selectbackgroundaccepted,
                                self.selectbackgroundcancelled, self.selectbackgroundfinished)

    # noinspection PyUnusedLocal
    def selectbackgroundfinished(self, arg):
        self.winSim.background_Pushbutton.setStyleSheet("")

    def resetToDefaultBackground(self):
        if self.new_version_flag == 1:
            colour = QtGui.QColor(0, 158, 181)
        else:
            colour = QtGui.QColor(0, 0, 0)
        self.winSim.xrdp_window.setBackgroundBrush(colour)
        self.winSim.backgroundView.setBackgroundBrush(colour)
        if self.xrdp_ini_file.has_option('globals', 'background'):
            self.xrdp_ini_file.remove_option('globals', 'background')
        self.xrdp_changed()

    def loginSimulatorSelectBlack(self):
        # "black=" in the ini file is for module/username/password text colour...
        self.disableButtons()
        self.winSim.black_Pushbutton.setStyleSheet(self.colourbutton_stylesheet)
        self.original_colour = self.simmoduletext.defaultTextColor()
        self.original_module_stylesheet = self.simmodulebox.styleSheet()
        self.original_username_stylesheet = self.simusernamebox.styleSheet()
        self.original_passbox_stylesheet = self.simpassbox.styleSheet()
        self.orig_help_btn_stylesheet = self.simokbtn.styleSheet()
        self.orig_cancel_btn_stylesheet = self.simcancelbtn.styleSheet()
        if not self.new_version_flag:
            self.orig_help_btn_stylesheet = self.simhelpbtn.styleSheet()
        self.showColourSelector(self.original_colour, self.selectBlackUpdater, self.blackaccepted, self.blackrejected,
                          self.blackfinished)

    def selectBlackUpdater(self, colour):
        self.simmoduletext.setDefaultTextColor(colour)
        self.simusernametext.setDefaultTextColor(colour)
        self.simpasswordtext.setDefaultTextColor(colour)
        self.updateModuleStylesheet()
        self.updateButtonStyles()
        self.updateUserPassStylesheet()
        self.winSim.textView.setBackgroundBrush(QtGui.QBrush(colour))

    def blackaccepted(self):
        self.xrdp_ini_file.set('globals', 'black', str(self.colour_chooser.currentColor().name()[1:]))
        self.xrdp_changed()
        self.enableButtons()
        self.hideColourSelector(self.selectBlackUpdater, self.blackaccepted, self.blackrejected, self.blackfinished)

    def blackrejected(self):
        self.simmoduletext.setDefaultTextColor(self.original_colour)
        self.simusernametext.setDefaultTextColor(self.original_colour)
        self.simpasswordtext.setDefaultTextColor(self.original_colour)
        self.simmodulebox.setStyleSheet(self.original_module_stylesheet)
        self.simusernamebox.setStyleSheet(self.original_username_stylesheet)
        self.simpassbox.setStyleSheet(self.original_passbox_stylesheet)
        self.simokbtn.setStyleSheet(self.orig_help_btn_stylesheet)
        self.simcancelbtn.setStyleSheet(self.orig_cancel_btn_stylesheet)
        if not self.new_version_flag:
            self.simhelpbtn.setStyleSheet(self.orig_help_btn_stylesheet)
        self.winSim.textView.setBackgroundBrush(QtGui.QBrush(self.original_colour))
        self.enableButtons()
        self.hideColourSelector(self.selectBlackUpdater, self.blackaccepted, self.blackrejected, self.blackfinished)

    # noinspection PyUnusedLocal
    def blackfinished(self, arg):
        self.winSim.black_Pushbutton.setStyleSheet("")

    def resetBlack(self):
        colour = QtGui.QColor(0, 0, 0)
        self.simmoduletext.setDefaultTextColor(colour)
        self.simusernametext.setDefaultTextColor(colour)
        self.simpasswordtext.setDefaultTextColor(colour)
        self.updateModuleStylesheet()
        self.updateButtonStyles()
        self.updateUserPassStylesheet()
        self.winSim.textView.setBackgroundBrush(QtGui.QBrush(colour))
        if self.xrdp_ini_file.has_option('globals', 'black'):
            self.xrdp_ini_file.remove_option('globals', 'black')
        self.xrdp_changed()

    # "grey=" in the ini file is for the login Window fill colour...
    def loginSimulatorSelectGrey(self):
        self.disableButtons()
        self.winSim.grey_Pushbutton.setStyleSheet(self.colourbutton_stylesheet)
        self.original_colour = self.simloginwindow.loginrect.brush().color()
        self.orig_help_btn_stylesheet = self.simokbtn.styleSheet()
        self.orig_cancel_btn_stylesheet = self.simcancelbtn.styleSheet()
        if not self.new_version_flag:
            self.orig_help_btn_stylesheet = self.simhelpbtn.styleSheet()
        self.original_module_stylesheet = self.simmodulebox.styleSheet()
        self.showColourSelector(self.original_colour, self.selectGreyUpdater, self.greyaccepted, self.greyrejected,
                          self.greyfinished)

    def selectGreyUpdater(self, colour):
        self.simloginwindow.loginrect.setBrush(QtGui.QBrush(QtGui.QColor(colour)))
        self.winSim.windowView.setBackgroundBrush(QtGui.QBrush(colour))
        self.updateButtonStyles()
        self.updateModuleStylesheet()

    def greyaccepted(self):
        if self.new_version_flag:
            self.xrdp_ini_file.set('globals', 'ls_bg_color', str(self.colour_chooser.currentColor().name()[1:]))
        self.xrdp_ini_file.set('globals', 'grey', str(self.colour_chooser.currentColor().name()[1:]))
        self.xrdp_changed()
        self.enableButtons()
        self.hideColourSelector(self.selectGreyUpdater, self.greyaccepted, self.greyrejected, self.greyfinished)

    def greyrejected(self):
        self.simloginwindow.loginrect.setBrush(QtGui.QBrush(QtGui.QColor(self.original_colour)))
        self.simokbtn.setStyleSheet(self.orig_help_btn_stylesheet)
        self.simcancelbtn.setStyleSheet(self.orig_cancel_btn_stylesheet)
        if not self.new_version_flag:
            self.simhelpbtn.setStyleSheet(self.orig_help_btn_stylesheet)
        self.simmodulebox.setStyleSheet(self.original_module_stylesheet)
        self.winSim.windowView.setBackgroundBrush(QtGui.QBrush(self.original_colour))
        self.enableButtons()
        self.hideColourSelector(self.selectGreyUpdater, self.greyaccepted, self.greyrejected, self.greyfinished)

    # noinspection PyUnusedLocal
    def greyfinished(self, arg):
        self.winSim.grey_Pushbutton.setStyleSheet("")

    def resetGrey(self):
        if self.new_version_flag == 1:
            colour = QtGui.QColor(222, 223, 222)
        else:
            colour = QtGui.QColor(195, 195, 195)
        self.simloginwindow.loginrect.setBrush(QtGui.QBrush(QtGui.QColor(colour)))
        self.winSim.windowView.setBackgroundBrush(QtGui.QBrush(colour))
        self.updateButtonStyles()
        self.updateModuleStylesheet()
        if self.xrdp_ini_file.has_option('globals', 'grey'):
            self.xrdp_ini_file.remove_option('globals', 'grey')
        self.xrdp_changed()

    # "dark_grey=" is for the Window bottom & right, and "boxes" top & left shade-lines...
    def loginSimulatorSelectDarkGrey(self):
        self.disableButtons()
        self.winSim.dark_grey_Pushbutton.setStyleSheet(self.colourbutton_stylesheet)
        self.original_colour = self.simloginwindow.bottomline.pen().color()
        self.orig_pen = self.simmoduShading.leftline.pen()
        self.orig_help_btn_stylesheet = self.simokbtn.styleSheet()
        self.orig_cancel_btn_stylesheet = self.simcancelbtn.styleSheet()
        if not self.new_version_flag:
            self.orig_help_btn_stylesheet = self.simhelpbtn.styleSheet()
        self.showColourSelector(self.original_colour, self.selectDarkGreyUpdater, self.darkgreyaccepted,
                          self.darkgreyrejected, self.darkgreyfinished)

    def selectDarkGreyUpdater(self, colour):
        pen = self.simloginwindow.bottomline.pen()
        pen.setColor(QtGui.QColor(colour))
        self.simloginwindow.rightline.setPen(pen)
        self.simloginwindow.bottomline.setPen(pen)
        self.simmoduShading.topline.setPen(pen)
        self.simmoduShading.leftline.setPen(pen)
        self.simuserShading.topline.setPen(pen)
        self.simuserShading.leftline.setPen(pen)
        self.simpassShading.topline.setPen(pen)
        self.simpassShading.leftline.setPen(pen)
        self.winSim.botRightView.setBackgroundBrush(QtGui.QBrush(colour))
        self.updateButtonStyles()

    def darkgreyaccepted(self):
        self.xrdp_ini_file.set('globals', 'dark_grey', str(self.colour_chooser.currentColor().name()[1:]))
        self.xrdp_changed()
        self.enableButtons()
        self.hideColourSelector(self.selectDarkGreyUpdater, self.darkgreyaccepted, self.darkgreyrejected,
                                self.darkgreyfinished)

    def darkgreyrejected(self):
        self.simloginwindow.bottomline.setPen(self.orig_pen)
        self.simloginwindow.rightline.setPen(self.orig_pen)
        self.simmoduShading.topline.setPen(self.orig_pen)
        self.simmoduShading.leftline.setPen(self.orig_pen)
        self.simuserShading.topline.setPen(self.orig_pen)
        self.simuserShading.leftline.setPen(self.orig_pen)
        self.simpassShading.topline.setPen(self.orig_pen)
        self.simpassShading.leftline.setPen(self.orig_pen)
        self.simokbtn.setStyleSheet(self.orig_help_btn_stylesheet)
        self.simcancelbtn.setStyleSheet(self.orig_cancel_btn_stylesheet)
        if not self.new_version_flag:
            self.simhelpbtn.setStyleSheet(self.orig_help_btn_stylesheet)
        self.winSim.botRightView.setBackgroundBrush(QtGui.QBrush(self.original_colour))
        self.enableButtons()
        self.hideColourSelector(self.selectDarkGreyUpdater, self.darkgreyaccepted, self.darkgreyrejected,
                                self.darkgreyfinished)

    # noinspection PyUnusedLocal
    def darkgreyfinished(self, arg):
        self.winSim.dark_grey_Pushbutton.setStyleSheet("")

    def resetDarkGrey(self):

        colour = QtGui.QColor(128, 128, 128)
        pen = self.simloginwindow.bottomline.pen()
        pen.setColor(QtGui.QColor(colour))
        self.simloginwindow.rightline.setPen(pen)
        self.simloginwindow.bottomline.setPen(pen)
        self.simmoduShading.topline.setPen(pen)
        self.simmoduShading.leftline.setPen(pen)
        self.simuserShading.topline.setPen(pen)
        self.simuserShading.leftline.setPen(pen)
        self.simpassShading.topline.setPen(pen)
        self.simpassShading.leftline.setPen(pen)
        self.winSim.botRightView.setBackgroundBrush(QtGui.QBrush(colour))
        self.updateButtonStyles()
        if self.xrdp_ini_file.has_option('globals', 'dark_grey'):
            self.xrdp_ini_file.remove_option('globals', 'dark_grey')
        self.xrdp_changed()

    # "blue=" is for the "banner" colour...
    def loginSimulatorSelectBlue(self):
        self.disableButtons()
        self.winSim.blue_Pushbutton.setStyleSheet(self.colourbutton_stylesheet)
        self.simmodulebox.showPopup()
        popup = self.simmodulebox.findChild(QtGui.QFrame, '')
        popup.move(popup.x() - 2, popup.y())
        self.original_colour = self.simloginwindow.loginbanner.pen().color()
        self.original_brush_colour = self.simloginwindow.loginbanner.brush().color()
        self.showColourSelector(self.original_colour, self.selectBlueUpdater, self.blueaccepted, self.bluerejected,
                          self.bluefinished)

    def selectBlueUpdater(self, colour):
        self.simloginwindow.loginbanner.setPen(QtGui.QColor(colour))
        self.simloginwindow.loginbanner.setBrush(QtGui.QColor(colour))
        self.winSim.titleBgndView.setBackgroundBrush(colour)
        self.updateModuleStylesheet()

    def blueaccepted(self):
        self.xrdp_ini_file.set('globals', 'blue', str(self.colour_chooser.currentColor().name()[1:]))
        self.xrdp_changed()
        self.enableButtons()
        self.hideColourSelector(self.selectBlueUpdater, self.blueaccepted, self.bluerejected, self.bluefinished)
        self.simmodulebox.hidePopup()

    def bluerejected(self):
        self.simloginwindow.loginbanner.setPen(self.original_colour)
        self.simloginwindow.loginbanner.setBrush(self.original_brush_colour)
        self.winSim.titleBgndView.setBackgroundBrush(self.original_brush_colour)
        self.enableButtons()
        self.hideColourSelector(self.selectBlueUpdater, self.blueaccepted, self.bluerejected, self.bluefinished)
        self.simmodulebox.hidePopup()

    # noinspection PyUnusedLocal
    def bluefinished(self, arg):
        self.winSim.blue_Pushbutton.setStyleSheet("")

    def resetBlue(self):
        if self.new_version_flag == 1:
            colour = QtGui.QColor(0, 158, 181)
        else:
            colour = QtGui.QColor(0, 0, 255)
        self.simloginwindow.loginbanner.setPen(QtGui.QColor(colour))
        self.simloginwindow.loginbanner.setBrush(QtGui.QColor(colour))
        self.winSim.titleBgndView.setBackgroundBrush(colour)
        self.updateModuleStylesheet()
        if self.xrdp_ini_file.has_option('globals', 'blue'):
            self.xrdp_ini_file.remove_option('globals', 'blue')
        self.xrdp_changed()

    # "dark_blue=" is for the "combobox-focus-background" colour...
    def loginSimulatorSelectDarkBlue(self):
        self.disableButtons()
        self.winSim.dark_blue_Pushbutton.setStyleSheet(self.colourbutton_stylesheet)
        self.simmodulebox.showPopup()
        self.original_colour = self.dark_blue
        self.showColourSelector(self.original_colour, self.selectDarkBlueUpdater, self.darkblueaccepted,
                          self.darkbluerejected, self.darkbluefinished)

    def selectDarkBlueUpdater(self, colour):
        self.dark_blue = colour
        self.updateModuleStylesheet()
        self.winSim.darkBlueView.setBackgroundBrush(QtGui.QBrush(colour))

    def darkblueaccepted(self):
        self.xrdp_ini_file.set('globals', 'dark_blue', str(self.colour_chooser.currentColor().name()[1:]))
        self.xrdp_changed()
        self.enableButtons()
        self.hideColourSelector(self.selectDarkBlueUpdater, self.darkblueaccepted, self.darkbluerejected,
                                self.darkbluefinished)
        self.simmodulebox.hidePopup()

    def darkbluerejected(self):
        self.dark_blue = self.original_colour
        self.updateModuleStylesheet()
        self.winSim.darkBlueView.setBackgroundBrush(QtGui.QBrush(self.original_colour))
        self.enableButtons()
        self.hideColourSelector(self.selectDarkBlueUpdater, self.darkblueaccepted, self.darkbluerejected,
                                self.darkbluefinished)
        self.simmodulebox.hidePopup()

    # noinspection PyUnusedLocal
    def darkbluefinished(self, arg):
        self.winSim.dark_blue_Pushbutton.setStyleSheet("")

    def resetDarkBlue(self):
        colour = QtGui.QColor(0, 0, 127)
        self.dark_blue = colour
        self.updateModuleStylesheet()
        self.winSim.darkBlueView.setBackgroundBrush(QtGui.QBrush(colour))
        if self.xrdp_ini_file.has_option('globals', 'dark_blue'):
            self.xrdp_ini_file.remove_option('globals', 'dark_blue')
        self.xrdp_changed()

    # "white=" is for the top & left shade-lines PLUS Banner Text PLUS Module/name/password blocks...
    def loginSimulatorSelectWhite(self):
        self.disableButtons()
        self.winSim.white_Pushbutton.setStyleSheet(self.colourbutton_stylesheet)
        self.original_colour = self.simloginwindow.topline.pen().color()
        self.orig_pen = self.simloginwindow.topline.pen()
        self.orig_module_stylesheet = self.simmodulebox.styleSheet()
        self.orig_username_stylesheet = self.simusernamebox.styleSheet()
        self.orig_password_stylesheet = self.simpassbox.styleSheet()
        self.orig_help_btn_stylesheet = self.simokbtn.styleSheet()
        self.orig_cancel_btn_stylesheet = self.simcancelbtn.styleSheet()
        if not self.new_version_flag:
            self.orig_help_btn_stylesheet = self.simhelpbtn.styleSheet()
        self.showColourSelector(self.original_colour, self.selectWhiteUpdater, self.whiteaccepted, self.whiterejected,
                          self.whitefinished)

    def selectWhiteUpdater(self, colour):
        pen = self.simloginwindow.topline.pen()
        pen.setColor(QtGui.QColor(colour))
        self.simloginwindow.topline.setPen(pen)
        self.simloginwindow.leftline.setPen(pen)
        self.simloginwindow.bannertext.setDefaultTextColor(QtGui.QColor(colour))
        self.updateModuleStylesheet()
        self.updateButtonStyles()
        self.updateUserPassStylesheet()
        self.updateUserPassStylesheet()
        self.simmoduShading.bottomline.setPen(pen)
        self.simmoduShading.rightline.setPen(pen)
        self.simuserShading.bottomline.setPen(pen)
        self.simuserShading.rightline.setPen(pen)
        self.simpassShading.bottomline.setPen(pen)
        self.simpassShading.rightline.setPen(pen)
        self.winSim.boxesView.setBackgroundBrush(QtGui.QBrush(colour))

    def whiteaccepted(self):
        self.xrdp_ini_file.set('globals', 'white', str(self.colour_chooser.currentColor().name()[1:]))
        self.xrdp_changed()
        self.enableButtons()
        self.hideColourSelector(self.selectWhiteUpdater, self.whiteaccepted, self.whiterejected, self.whitefinished)

    def whiterejected(self):
        self.simloginwindow.topline.setPen(self.orig_pen)
        self.simloginwindow.leftline.setPen(self.orig_pen)
        self.simloginwindow.bannertext.setDefaultTextColor(QtGui.QColor(self.original_colour))
        self.simmodulebox.setStyleSheet(self.orig_module_stylesheet)
        self.simusernamebox.setStyleSheet(self.orig_username_stylesheet)
        self.simpassbox.setStyleSheet(self.orig_password_stylesheet)
        self.simokbtn.setStyleSheet(self.orig_help_btn_stylesheet)
        self.simcancelbtn.setStyleSheet(self.orig_cancel_btn_stylesheet)
        if not self.new_version_flag:
            self.simhelpbtn.setStyleSheet(self.orig_help_btn_stylesheet)
        self.simmoduShading.bottomline.setPen(self.orig_pen)
        self.simmoduShading.rightline.setPen(self.orig_pen)
        self.simuserShading.bottomline.setPen(self.orig_pen)
        self.simuserShading.rightline.setPen(self.orig_pen)
        self.simpassShading.bottomline.setPen(self.orig_pen)
        self.simpassShading.rightline.setPen(self.orig_pen)
        self.winSim.boxesView.setBackgroundBrush(QtGui.QBrush(self.original_colour))
        self.enableButtons()
        self.hideColourSelector(self.selectWhiteUpdater, self.whiteaccepted, self.whiterejected, self.whitefinished)

    # noinspection PyUnusedLocal
    def whitefinished(self, arg):
        self.winSim.white_Pushbutton.setStyleSheet("")

    def resetWhite(self):
        colour = QtGui.QColor(255, 255, 255)
        pen = self.simloginwindow.topline.pen()
        pen.setColor(QtGui.QColor(colour))
        self.simloginwindow.topline.setPen(pen)
        self.simloginwindow.leftline.setPen(pen)
        self.simloginwindow.bannertext.setDefaultTextColor(QtGui.QColor(colour))
        self.updateModuleStylesheet()
        self.updateButtonStyles()
        self.updateUserPassStylesheet()
        self.updateUserPassStylesheet()
        self.simmoduShading.bottomline.setPen(pen)
        self.simmoduShading.rightline.setPen(pen)
        self.simuserShading.bottomline.setPen(pen)
        self.simuserShading.rightline.setPen(pen)
        self.simpassShading.bottomline.setPen(pen)
        self.simpassShading.rightline.setPen(pen)
        self.winSim.boxesView.setBackgroundBrush(QtGui.QBrush(colour))
        if self.xrdp_ini_file.has_option('globals', 'white'):
            self.xrdp_ini_file.remove_option('globals', 'white')
        self.xrdp_changed()

    #
    #    def hilightText(self):
    #        original_colour = self.moduletext.defaultTextColor()
    #        self.highlight_text_running = 1
    #        for colour in range(0, 255, 1):
    #            the_colour = QtGui.QColor.fromRgb(colour, 0, 0)
    #            self.moduletext.setDefaultTextColor(the_colour)
    #            self.usernametext.setDefaultTextColor(the_colour)
    #            self.passwordtext.setDefaultTextColor(the_colour)
    #            QtCore.QCoreApplication.processEvents()
    #        self.moduletext.setDefaultTextColor(original_colour)
    #        self.usernametext.setDefaultTextColor(original_colour)
    #        self.passwordtext.setDefaultTextColor(original_colour)
    #        self.highlight_text_running = 0

    # ### END OF LOGIN SIMULATOR ### 

    # xrdp.ini file section parsers start here.....

    def parseXrdpGlobalsSection(self):
        self.new_version_flag = 0
        self.listeningAddressEntryBox.setText('127.0.0.1')
        #self.versionDisplayLabel.setText("Editing the old format xrdp.ini...")
        for name, value in self.xrdp_ini_file.items("globals"):
            # Detect the INI version...
            if name == "ini_version" and value in "1":
                self.new_version_flag = 1
                #self.versionDisplayLabel.setText("Editing the new format xrdp.ini..")
            elif name == "address":
                self.listeningAddressEntryBox.setText(value)
            elif name == "bitmap_cache" and value in ["1", "yes", "true"]:
                self.useBitMapCacheCheckBox.blockSignals(True)
                self.useBitMapCacheCheckBox.setCheckState(QtCore.Qt.Checked)
                self.useBitMapCacheCheckBox.blockSignals(False)
            elif name == "bitmap_compression" and value in ["1", "yes", "true"]:
                self.useBitMapCompCheckBox.blockSignals(True)
                self.useBitMapCompCheckBox.setCheckState(QtCore.Qt.Checked)
                self.useBitMapCompCheckBox.blockSignals(False)
            elif name == "bulk_compression" and value in ["1", "yes", "true"]:
                self.useBulkCompCheckBox.blockSignals(True)
                self.useBulkCompCheckBox.setCheckState(QtCore.Qt.Checked)
                self.useBulkCompCheckBox.blockSignals(False)
            elif name == "channel_code" and value in ["0", "false", "no"]:
                self.enableChannelCheckBox.blockSignals(True)
                self.enableChannelCheckBox.setCheckState(QtCore.Qt.UnChecked)
                self.enableChannelCheckBox.blockSignals(False)
            elif name == "crypt_level":
                self.updateCryptLevelCombo(value)
            elif name == "fork" and value in ["1", "yes", "true"]:
                self.forkSessionsCheckBox.blockSignals(True)
                self.forkSessionsCheckBox.setCheckState(QtCore.Qt.Checked)
                self.forkSessionsCheckBox.blockSignals(False)
            elif name == "hidelogwindow" and value in ["1", "yes", "true"]:
                self.hideLogWindowCheckBox.blockSignals(True)
                self.hideLogWindowCheckBox.setCheckedState(QtCore.Qt.Checked)
                self.hideLogWindowCheckBox.blockSignals(False)
            elif name == "max_bpp":
                self.updateMaxBppCombo(value)
            elif name == "port":
                self.listeningPortEntryBox.blockSignals(True)
                self.listeningPortEntryBox.setText(value)
                self.listeningPortEntryBox.blockSignals(False)
            elif name == "tcp_keepalive" and value in ["1", "yes", "true"]:
                self.tcpKeepAliveCheckBox.blockSignals(True)
                self.tcpKeepAliveCheckBox.setCheckState(QtCore.Qt.Checked)
                self.tcpKeepAliveCheckBox.blockSignals(False)
            elif name == "tcp_nodelay" and value in ["1", "yes", "true"]:
                self.tcpNoDelayCheckBox.blockSignals(True)
                self.tcpNoDelayCheckBox.setCheckState(QtCore.Qt.Checked)
                self.tcpNoDelayCheckBox.blockSignals(False)
            elif name == "pamerrortxt":
                self.additionalPamErrorTextCheckbox.blockSignals(True)
                self.pamErrorText.blockSignals(True)
                self.additionalPamErrorTextCheckbox.setCheckState(QtCore.Qt.Checked)
                self.pamErrorText.setEnabled(True)
                self.pamErrorText.setText(value)
                self.additionalPamErrorTextCheckbox.blockSignals(False)
                self.pamErrorText.blockSignals(False)
            elif name == "require_credentials" and value in ["1", "yes", "true"]:
                self.requireCredentialsCheckbox.setCheckState(QtCore.Qt.Checked)
            elif name == "new_cursors" and value in ["0", "no", "false"]:
                self.disableNewCursorsCheckBox.blockSignals(True)
                self.disableNewCursorsCheckBox.setCheckState(QtCore.Qt.Checked)
                self.disableNewCursorsCheckBox.blockSignals(False)
            elif name == "blue":
                colour = getColour(value)
                self.simloginwindow.loginbanner.setPen(colour)
                self.simloginwindow.loginbanner.setBrush(colour)
                self.updateButtonStyles()
                self.updateModuleStylesheet()
                self.winSim.titleBgndView.setBackgroundBrush(colour)
            elif name == "dark_blue":
                self.dark_blue = getColour(value)
                self.updateModuleStylesheet()
                self.winSim.darkBlueView.setBackgroundBrush(self.dark_blue)
            elif name == "background":
                colour = getColour(value)
                if self.xrdp_ini_file.has_option('globals', 'ls_top_window_bg_color'):
                    result = self.xrdp_ini_file.get('globals', 'ls_top_window_bg_color')
                    colour = QtGui.QColor('#' + result)
                brush = QtGui.QBrush(colour)
                brush.setStyle(QtCore.Qt.SolidPattern)
                self.winSim.xrdp_window.setBackgroundBrush(brush)
                self.winSim.backgroundView.setBackgroundBrush(colour)
            elif name == "ls_top_window_bg_color":
                colour = QtGui.QColor('#' + value)
                brush = QtGui.QBrush(colour)
                brush.setStyle(QtCore.Qt.SolidPattern)
                self.winSim.xrdp_window.setBackgroundBrush(brush)
                self.winSim.backgroundView.setBackgroundBrush(colour)
            elif name == "ls_bg_color":
                colour = QtGui.QColor('#' + value)
                self.simloginwindow.loginrect.setBrush(QtGui.QBrush(colour))
                self.simloginwindow.loginrect.setPen(QtGui.QPen(colour))
                self.updateButtonStyles()
                self.updateModuleStylesheet()
                self.winSim.windowView.setBackgroundBrush(colour)
            elif name == "grey":
                colour = getColour(value)
                self.simloginwindow.loginrect.setBrush(QtGui.QBrush(colour))
                self.simloginwindow.loginrect.setPen(QtGui.QPen(colour))
                self.updateButtonStyles()
                self.updateModuleStylesheet()
                self.winSim.windowView.setBackgroundBrush(colour)
            elif name == "black":
                colour = getColour(value)
                self.simmoduletext.setDefaultTextColor(colour)
                self.simusernametext.setDefaultTextColor(colour)
                self.simpasswordtext.setDefaultTextColor(colour)
                self.updateButtonStyles()
                self.updateModuleStylesheet()
                self.winSim.textView.setBackgroundBrush(colour)
            elif name == "white":
                colour = getColour(value)
                pen = self.simloginwindow.topline.pen()
                pen.setColor(QtGui.QColor(colour))
                self.simloginwindow.topline.setPen(pen)
                self.simloginwindow.leftline.setPen(pen)
                self.simloginwindow.bannertext.setDefaultTextColor(colour)
                stylecolour = QtGui.QColor(colour)
                self.updateModuleStylesheet()
                stylesheet = 'QLineEdit {background-color: ' + QtGui.QColor(stylecolour).name() + '; } '
                self.simusernamebox.setStyleSheet(stylesheet)
                stylesheet = 'QLineEdit {lineedit-password-character: 42; background-color: ' + QtGui.QColor(
                    stylecolour).name() + '; } '
                self.simpassbox.setStyleSheet(stylesheet)
                self.simmoduShading.bottomline.setPen(pen)
                self.simmoduShading.rightline.setPen(pen)
                self.simuserShading.bottomline.setPen(pen)
                self.simuserShading.rightline.setPen(pen)
                self.simpassShading.bottomline.setPen(pen)
                self.simpassShading.rightline.setPen(pen)
                self.updateButtonStyles()
                self.updateModuleStylesheet()
                self.winSim.boxesView.setBackgroundBrush(colour)
            elif name == "dark_grey":
                colour = getColour(value)
                self.simloginwindow.bottomline.setPen(colour)
                self.simloginwindow.rightline.setPen(colour)
                boxpen = self.simmoduShading.topline.pen()
                boxpen.setColor(QtGui.QColor(colour))
                self.simmoduShading.topline.setPen(boxpen)
                self.simmoduShading.leftline.setPen(boxpen)
                self.simuserShading.topline.setPen(boxpen)
                self.simuserShading.leftline.setPen(boxpen)
                self.simpassShading.topline.setPen(boxpen)
                self.simpassShading.leftline.setPen(boxpen)
                self.updateButtonStyles()
                self.updateModuleStylesheet()
                self.winSim.botRightView.setBackgroundBrush(colour)
            elif name == "allow_multimon":
                self.allowMultimonCheckBox.setCheckState(QtCore.Qt.Checked)

    def parseXrdpLoggingSection(self):
        for name, value in self.xrdp_ini_file.items("Logging"):
            if name == "logfile":
                self.logFileNameEntryBox.setText(value)
            if name == "loglevel":
                self.logLevelComboBox.blockSignals(True)
                if value in ["CORE", "0"]:
                    self.logLevelComboBox.setCurrentIndex(0)
                if value in ["ERROR", "1"]:
                    self.logLevelComboBox.setCurrentIndex(1)
                if value in ["WARNING", "WARN", "2"]:
                    self.logLevelComboBox.setCurrentIndex(2)
                if value in ["INFO", "3"]:
                    self.logLevelComboBox.setCurrentIndex(3)
                if value in ["DEBUG", "4"]:
                    self.logLevelComboBox.setCurrentIndex(4)
                self.logLevelComboBox.blockSignals(False)
            if name == "enablesyslog" and value in ["1", "yes", "true"]:
                self.enableSyslogCheckBox.blockSignals(True)
                self.enableSyslogCheckBox.setCheckState(QtCore.Qt.Checked)
                self.enableSyslogCheckBox.blockSignals(False)
            if name == "sysloglevel":
                self.sysLogLevelComboBox.blockSignals(True)
                if value in ["CORE", "0"]:
                    self.sysLogLevelComboBox.setCurrentIndex(0)
                if value in ["ERROR", "1"]:
                    self.sysLogLevelComboBox.setCurrentIndex(1)
                if value in ["WARNING", "WARN", "2"]:
                    self.sysLogLevelComboBox.setCurrentIndex(2)
                if value in ["INFO", "3"]:
                    self.sysLogLevelComboBox.setCurrentIndex(3)
                if value in ["DEBUG", "4"]:
                    self.sysLogLevelComboBox.setCurrentIndex(4)
                self.sysLogLevelComboBox.blockSignals(False)

    def addDefaultLoggingSection(self):
        self.xrdp_ini_file.add_section("Logging")
        self.xrdp_ini_file.set('Logging', 'logfile', 'xrdp.log')
        self.xrdp_ini_file.set('Logging', 'loglevel', 'DEBUG')
        self.xrdp_ini_file.set('Logging', 'enablesyslog', '1')
        self.xrdp_ini_file.set('Logging', 'sysloglevel', 'DEBUG')

    def parseXrdpChannelsSection(self):
        for name, value in self.xrdp_ini_file.items("channels"):
            if name == "rdpdr" and value in ["1", "true", "yes"]:
                self.useRdpDrCheckBox.blockSignals(True)
                self.useRdpDrCheckBox.setCheckState(QtCore.Qt.Checked)
                self.useRdpDrCheckBox.blockSignals(False)
            if name == "rdpsnd" and value in ["1", "true", "yes"]:
                self.useRdpSndCheckBox.blockSignals(True)
                self.useRdpSndCheckBox.setCheckState(QtCore.Qt.Checked)
                self.useRdpSndCheckBox.blockSignals(False)
            if name == "drdynvc" and value in ["1", "true", "yes"]:
                self.useDrDynVcCheckBox.blockSignals(True)
                self.useDrDynVcCheckBox.setCheckState(QtCore.Qt.Checked)
                self.useDrDynVcCheckBox.blockSignals(False)
            if name == "cliprdr" and value in ["1", "true", "yes"]:
                self.useClipRdrCheckBox.blockSignals(True)
                self.useClipRdrCheckBox.setCheckState(QtCore.Qt.Checked)
                self.useClipRdrCheckBox.blockSignals(False)
            if name == "rail" and value in ["1", "true", "yes"]:
                self.useRAILCheckBox.blockSignals(True)
                self.useRAILCheckBox.setCheckState(QtCore.Qt.Checked)
                self.useRAILCheckBox.blockSignals(False)
            if name == "xrdpvr" and value in ["1", "true", "yes"]:
                self.useXrdpVrCheckBox.blockSignals(True)
                self.useXrdpVrCheckBox.setCheckState(QtCore.Qt.Checked)
                self.useXrdpVrCheckBox.blockSignals(False)

    def addDefaultChannelsSection(self):
        self.xrdp_ini_file.add_section('channels')
        self.xrdp_ini_file.set('channels', 'rdpdr', 'true')
        self.xrdp_ini_file.set('channels', 'rdpsnd', 'true')
        self.xrdp_ini_file.set('channels', 'drdynvc', 'true')
        self.xrdp_ini_file.set('channels', 'cliprdr', 'true')
        self.xrdp_ini_file.set('channels', 'rail', 'true')
        self.xrdp_ini_file.set('channels', 'xrdpvr', 'true')

    # Parse and Create tabs for each of the Sessions...

    # Define functions for each part of a session...

    # This will be called for any session which becomes "[xrdp1]"
    # It enables the "Debug xrdp" checkbox for that particular session
    def setXrdpCheckboxVisibility(self):
        self.xrdp_debug_checkbox = self.sessionsTab.widget(0).findChild(QtGui.QCheckBox, 'debugXRDPCheckbox')
        self.xrdp_debug_checkbox.setVisible(True)
        self.xrdp_debug_checkbox.clicked.connect(self.debugClicked)

    def createsessionstab(self, session_name):
        self.sessionsTab.addTab(sessionConfigForm(), session_name)

    def addSessionName(self, tab_index, value):
        section_name = "xrdp" + str(tab_index + 1)
        self.sessionsTab.widget(tab_index).findChild(QtGui.QLabel, 'sessionSectionName').setText(
            "[" + section_name + "]")
        namebox = self.sessionsTab.widget(tab_index).findChild(QtGui.QLineEdit, "sessionNameBox")
        namebox.setText(value)
        namebox.editingFinished.connect(self.sessionNameBoxChanged)
        self.sessionsTab.setTabText(tab_index, value)
        self.autoRunComboBox.addItem(value)
        self.simmodulebox.addItem(value)  # Login Sim combobox
        if self.sessionsTab.count() > 0:
            if tab_index == 0:
                self.setXrdpCheckboxVisibility()
            else:
                self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox, 'debugXRDPCheckbox').setVisible(False)
            self.deleteSessionButton.setEnabled(True)

    def addSessionLib(self, tab_index, value):
        lib_box = self.sessionsTab.widget(tab_index).findChild(QtGui.QComboBox, "libraryComboBox")
        if value == "libxup.so":
            lib_box.setCurrentIndex(0)
        if value == "libvnc.so":
            lib_box.setCurrentIndex(1)
        if value == "librdp.so":
            lib_box.setCurrentIndex(2)
            self.tabUserPasswordToggle(tab_index, 0)
        if value == "libxrdpfreerdp1.so":
            lib_box.setCurrentIndex(3)
        if value == "libxrdpneutrinordp.so":
            lib_box.setCurrentIndex(4)
        lib_box.currentIndexChanged.connect(self.tabLibraryComboBoxChanged)

    def setsessionserverbpp(self, tab_index, value):
        bppbox = self.sessionsTab.widget(tab_index).findChild(QtGui.QComboBox, 'serverbppcombobox')
        if value == "15":
            bppbox.setCurrentIndex(1)
        if value == "16":
            bppbox.setCurrentIndex(2)
        if value == "24":
            bppbox.setCurrentIndex(3)
        if value == "32":
            bppbox.setCurrentIndex(4)

    def addSessionIP(self, tab_index, value):
        sess_ip = self.sessionsTab.widget(tab_index).findChild(QtGui.QLineEdit, "sessionIPAddress")
        sess_ip.setText(value)
        sess_ip.editingFinished.connect(self.sessionIPAddressChanged)

    def addSessionPort(self, tab_index, value):
        sess_port = self.sessionsTab.widget(tab_index).findChild(QtGui.QLineEdit, "sessionPortEntryBox")
        chansrvport_widget = self.sessionsTab.widget(tab_index).findChild(QtGui.QLineEdit, "chansrvPortEntryBox")
        chansrvport_label_widget = self.sessionsTab.widget(tab_index).findChild(QtGui.QLabel, "chansrvport_label")
        if value == "/tmp/.xrdp/xrdp_display_10":
            self.xrdp_debug_checkbox.setCheckState(QtCore.Qt.CheckState(2))
            chansrvport_widget.setText("/tmp/.xrdp/xrdp_chansrv_socket_7210")
            if not self.xrdp_ini_file.has_option('xrdp1', 'chansrvport'):
                self.xrdp_ini_file.set('xrdp1', 'chansrvport', '/tmp/.xrdp/xrdp_chansrv_socket_7210')
        else:
            chansrvport_widget.setVisible(False)
            chansrvport_label_widget.setVisible(False)
        sess_port.setText(value)
        sess_port.editingFinished.connect(self.sessionPortBoxChanged)

    def addSessionUsername(self, tab_index, value):
        uname_widget = self.sessionsTab.widget(tab_index).findChild(QtGui.QLineEdit, "sessionUserNameEntryBox")
        uname_widget.setText(value)
        uname_widget.editingFinished.connect(self.sessionUsernameBoxChanged)

    def addSessionPassword(self, tab_index, value):
        pass_widget = self.sessionsTab.widget(tab_index).findChild(QtGui.QLineEdit, "sessionPasswordEntryBox")
        pass_widget.setText(value)
        pass_widget.editingFinished.connect(self.sessionPasswordBoxChanged)

    def parseXrdpIniSessions(self):
        tab_index = 0
        for sectname in self.xrdp_ini_file.sections():
            if "xrdp" in sectname:  # for each [xrdpN] section...
                self.createsessionstab(sectname)  # create the session tab...
                for name, value in self.xrdp_ini_file.items(sectname):
                    if name == "name":
                        self.addSessionName(tab_index, value)
                    elif name == "xserverbpp":
                        self.setsessionserverbpp(tab_index, value)
                    elif name == "lib":
                        self.addSessionLib(tab_index, value)
                    elif name == "ip":
                        self.addSessionIP(tab_index, value)
                    elif name == "port":
                        self.addSessionPort(tab_index, value)
                    elif name == "username":
                        self.addSessionUsername(tab_index, value)
                    elif name == "password":
                        self.addSessionPassword(tab_index, value)
                    elif name == "channel.rdpdr" and value == "true":
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QFrame, "channelsFrame").setEnabled(True)
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                                     "enableOverridesCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox, "useRdpDrCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                    elif name == "channel.rdpsnd" and value == "true":
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QFrame, "channelsFrame").setEnabled(True)
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                                     "enableOverridesCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                                     "useRdpSndCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                    elif name == "channel.drdynvc" and value == "true":
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QFrame, "channelsFrame").setEnabled(True)
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                                     "enableOverridesCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                                     "useDrDynVcCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                    elif name == "channel.cliprdr" and value == "true":
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QFrame, "channelsFrame").setEnabled(True)
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                                     "enableOverridesCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                                     "useClipRdrCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                    elif name == "channel.rail" and value == "true":
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QFrame, "channelsFrame").setEnabled(True)
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                                     "enableOverridesCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox, "useRAILCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                    elif name == "channel.xrdpvr" and value == "true":
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QFrame, "channelsFrame").setEnabled(True)
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                                     "enableOverridesCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                        self.sessionsTab.widget(tab_index).findChild(QtGui.QCheckBox,
                                                                     "useXrdpVrCheckBox").setCheckState(
                            QtCore.Qt.CheckState(2))
                self.sessionsOverrideUpdateActiveList(tab_index, "add")
                self.sessionsOverrideAddToArray(tab_index)
                self.sessionsTab.widget(tab_index).findChild(QtGui.QComboBox,
                                                             'serverbppcombobox').currentIndexChanged.connect(
                    self.sessionbppcomboboxchanged)
                tab_index += 1
            self.configuredSessionsLabel.setText(str(tab_index))

    def parseXrdpAutoRun(self):
        if self.xrdp_ini_file.has_option('globals', 'autorun'):
            self.autoRunComboBox.blockSignals(True)
            value = self.xrdp_ini_file.get('globals', 'autorun')
            count = self.autoRunComboBox.count()
            index = 0
            while value != self.autoRunComboBox.currentText():
                self.autoRunComboBox.setCurrentIndex(index)
                index += 1
                if index > count:
                    self.xrdp_ini_file.remove_option('globals', 'autorun')
                    break
            self.autoRunComboBox.blockSignals(False)

    def resetAutorunComboBox(self):
        # Reset Autorun Combo Box...
        items = self.autoRunComboBox.count()
        if items > 1:
            self.autoRunComboBox.blockSignals(True)
            count = items
            while count >= 1:
                self.autoRunComboBox.removeItem(count)
                count -= 1
            self.autoRunComboBox.blockSignals(False)

    def resetModuleBox(self):
        count = self.simmodulebox.count()
        while count >= 0:
            self.simmodulebox.removeItem(count)
            count -= 1

    def parseXrdpIni(self, fname):

        self.xrdp_ini_file_opened = 1

        # Display the filename of the ini file
        self.xrdpfilename = fname
        self.nameOfOpenFile.setText(fname)
        # Set up the xrdp.ini editor page
        self.showXrdpIniPage()

        # reset/clear any existing data...
        del self.xrdp_ini_file
        self.xrdp_ini_file = ConfigParser()

        # Initialise and keep note of original channel overrides state for each session
        self.sessions_channel_override_active_list[:] = []
        self.overridearray[:] = []
        # clear any sessionTabs...
        if self.sessionsTab.count() > 0:
            self.sessionsTab.clear()

        # Reset Autorun Combo Box...
        self.resetAutorunComboBox()

        # Parse the contents of the xrdp.ini file
        self.xrdp_ini_file.read(fname)

        if self.xrdp_ini_file.has_option('globals', 'ini_version'):
            if self.xrdp_ini_file.get('globals', 'ini_version') == '1':
                self.new_version_flag = 1

        #Initialize the Login Window Simulator...
        self.setupWinSim()
        self.resetPage(self.xrdpIniEditPage)

        # [GLOBALS] section...
        self.parseXrdpGlobalsSection()
        # [LOGGING] section...
        if self.xrdp_ini_file.has_section("Logging"):
            self.parseXrdpLoggingSection()
        else:  # if no [logging] section then add one...
            message_window = InfoWindow(
                "<html><head/><body><p>This xrdp.ini file didn't have a [Logging] section."
                "<p>A default one has been added.</p></body></html>")
            message_window.exec_()
            self.addDefaultLoggingSection()
            self.parseXrdpLoggingSection()
        #[CHANNELS] section...
        if self.xrdp_ini_file.has_section("channels"):
            self.parseXrdpChannelsSection()
        else:  # If no [channels] section, add one...
            message_window = InfoWindow(
                "<html><head/><body><p>This xrdp.ini file didn't have a [channels] section."
                "<p>A default one has been added.</p></body></html>")
            message_window.exec_()
            self.addDefaultChannelsSection()
            self.parseXrdpChannelsSection()

        # [SESSIONS Tabs]...
        self.parseXrdpIniSessions()
        # Finally, parse the "autorun" option, if any.
        # we do this last because at the parsing Globals stage we
        # haven't added any sessions yet.
        self.parseXrdpAutoRun()
        self.resequenceINI()

        self.something_xrdp_changed = 0

    def parseSesmanIni(self, fname):
        # clear edited params indicators...
        self.resetPage(self.sesmanIniEditPage)
        self.sesman_ini_file_opened = 1
        self.sesmanfilename = fname
        self.nameOfOpenFile.setText(self.sesmanfilename)
        self.fileopenlabel.setVisible(True)
        self.nameOfOpenFile.setVisible(True)
        self.filenameFrame.setVisible(True)
        self.showSesmanIniPage()
        # reset/clear any existing data...
        self.sesman_ini_file = ConfigParser()
        self.sesman_ini_file.optionxform = str
        # read in the ini file...
        self.sesman_ini_file.read(fname)
        # globals
        self.parseSesmanGlobalsSection()
        # security
        self.parseSesmanSecuritySection()
        # sessions
        self.parseSesmanSessionsSection()
        # Logging
        self.parseSesmanLoggingSection()
        #X11rdp params
        self.parseSesmanXServerParamSections("X11rdp")
        # Xvnc params
        self.parseSesmanXServerParamSections("Xvnc")

        self.something_sesman_changed = 0

    def parseSesmanGlobalsSection(self):
        for name, value in self.sesman_ini_file.items("Globals"):
            if name == "ListenAddress":
                self.sesmanListeningAddressEntryBox.setText(value)
            if name == "ListenPort":
                self.sesmanListeningPortEntryBox.setText(value)
            if name == "EnableUserWindowManager" and value == "1":
                self.enableUserWindowManager.setCheckState(QtCore.Qt.CheckState(2))
            if name == "UserWindowManager":
                self.userWindowManagerEntryBox.setText(value)
            if name == "DefaultWindowManager":
                self.defaultWindowManagerEntryBox.setText(value)

    def parseSesmanSecuritySection(self):
        for name, value in self.sesman_ini_file.items("Security"):
            if name == "AllowRootLogin":
                self.allowRootLoginCheckBox.setCheckState(QtCore.Qt.CheckState(2))
            if name == "MaxLoginRetry":
                self.maxLoginRetrySpinBox.blockSignals(True)
                self.maxLoginRetrySpinBox.setValue(int(value))
                self.maxLoginRetrySpinBox.blockSignals(False)
            if name == "TerminalServerUsers":
                self.terminalServiceUsersEntryBox.setText(value)
            if name == "TerminalServerAdmins":
                self.terminalServiceAdminsEntryBox.setText(value)
            if name == "AlwaysGroupCheck" and value == "true":
                self.alwaysCheckGroupCheckBox.setCheckState(QtCore.Qt.CheckState(2))

    def parseSesmanSessionsSection(self):
        for name, value in self.sesman_ini_file.items("Sessions"):
            if name == "X11DisplayOffset":
                self.x11DisplayOffsetSpinBox.blockSignals(True)
                self.x11DisplayOffsetSpinBox.setValue(int(value))
                self.x11DisplayOffsetSpinBox.blockSignals(False)
            if name == "MaxSessions":
                self.maxSessionsSpinBox.blockSignals(True)
                self.maxSessionsSpinBox.setValue(int(value))
                self.maxSessionsSpinBox.blockSignals(False)
            if name == "KillDisconnected" and value == "1":
                self.killDisconnectedCheckBox.setCheckState(QtCore.Qt.CheckState(2))
            if name == "IdleTimeLimit":
                self.idleTimeLimitSpinBox.blockSignals(True)
                self.idleTimeLimitSpinBox.setValue(int(value))
                self.idleTimeLimitSpinBox.blockSignals(False)
            if name == "DisconnectedTimeLimit":
                self.disconnectedTimeLimitSpinBox.blockSignals(True)
                self.disconnectedTimeLimitSpinBox.setValue(int(value))
                self.disconnectedTimeLimitSpinBox.blockSignals(False)

    def parseSesmanLoggingSection(self):
        for name, value in self.sesman_ini_file.items("Logging"):
            if name == "LogFile":
                self.sesmanLogFileNameEntryBox.setText(value)
            if name == "Loglevel":
                self.sesmanLogLevelComboBox.blockSignals(True)
                if value in ["CORE", "0"]:
                    self.sesmanLogLevelComboBox.setCurrentIndex(0)
                if value in ["ERROR", "1"]:
                    self.sesmanLogLevelComboBox.setCurrentIndex(1)
                if value in ["WARNING", "WARN", "2"]:
                    self.sesmanLogLevelComboBox.setCurrentIndex(2)
                if value in ["INFO", "3"]:
                    self.sesmanLogLevelComboBox.setCurrentIndex(3)
                if value in ["DEBUG", "4"]:
                    self.sesmanLogLevelComboBox.setCurrentIndex(4)
                self.sesmanLogLevelComboBox.blockSignals(False)
            if name == "EnableSyslog" and value in ["1", "yes", "true"]:
                self.enableSesmanSyslogCheckBox.blockSignals(True)
                self.enableSesmanSyslogCheckBox.setCheckState(QtCore.Qt.Checked)
                self.enableSesmanSyslogCheckBox.blockSignals(False)
            if name == "SysLogLevel":
                self.sesmanSysLogLevelComboBox.blockSignals(True)
                if value in ["CORE", "0"]:
                    self.sesmanSysLogLevelComboBox.setCurrentIndex(0)
                if value in ["ERROR", "1"]:
                    self.sesmanSysLogLevelComboBox.setCurrentIndex(1)
                if value in ["WARNING", "WARN", "2"]:
                    self.sesmanSysLogLevelComboBox.setCurrentIndex(2)
                if value in ["INFO", "3"]:
                    self.sesmanSysLogLevelComboBox.setCurrentIndex(3)
                if value in ["DEBUG", "4"]:
                    self.sesmanSysLogLevelComboBox.setCurrentIndex(4)
                self.sesmanSysLogLevelComboBox.blockSignals(False)

    def parseSesmanXServerParamSections(self, secname):
        text = ""
        for name, value in self.sesman_ini_file.items(secname):
            if "param" in name:
                text = text + value + " "
        if secname == "X11rdp":
            self.x11rdpParamsLineEdit.setText(text)
        elif secname == "Xvnc":
            self.xvncParamsLineEdit.setText(text)

    def sesmanListeningIPAddressChanged(self):
        if self.sesmanListeningAddressEntryBox.isModified():
            self.sesman_ini_file.set("Globals", "ListenAddress", self.sesmanListeningAddressEntryBox.text())
            self.sesmanListeningAddressEntryBox.setStyleSheet(self.line_edit_changed_stylesheet)
            self.sesman_changed()
            self.sesmanListeningAddressEntryBox.setModified(0)

    def sesmanListenPortChanged(self):
        if self.sesmanListeningPortEntryBox.isModified():
            self.sesman_ini_file.set('Globals', 'ListenPort', self.sesmanListeningPortEntryBox.text())
            self.sesmanListeningPortEntryBox.setStyleSheet(self.line_edit_changed_stylesheet)
            self.sesman_changed()
            self.sesmanListeningPortEntryBox.setModified(0)
            #            self.focusNextChild()

    def sesmanEnableUserWindowManagerChanged(self):
        if self.enableUserWindowManager.checkState() == 2:
            self.sesman_ini_file.set('Globals', 'EnableUserWindowManager', '1')
            self.userWindowManagerEntryBox.setEnabled(True)
            self.label_21.setEnabled(True)
            self.sesman_ini_file.set('Globals', 'UserWindowManager', 'startwm.sh')
            self.userWindowManagerEntryBox.setText('startwm.sh')
        else:
            self.sesman_ini_file.set('Globals', 'EnableUserWindowManager', '0')
            self.sesman_ini_file.remove_option('Globals', 'UserWindowManager')
            self.userWindowManagerEntryBox.setText('')
            self.userWindowManagerEntryBox.setEnabled(False)
            self.label_21.setEnabled(False)
        self.sesman_changed()
        self.enableUserWindowManager.setStyleSheet(self.checkbox_changed_stylesheet)

    def userWindowManagerEntryBoxChanged(self):
        if self.userWindowManagerEntryBox.isModified():
            self.sesman_ini_file.set('Globals', 'UserWindowManager', self.userWindowManagerEntryBox.text())
            self.userWindowManagerEntryBox.setStyleSheet(self.line_edit_changed_stylesheet)
            self.sesman_changed()
            self.userWindowManagerEntryBox.setModified(0)

    def defaultWindowManagerEntryBoxChanged(self):
        if self.defaultWindowManagerEntryBox.isModified():
            self.sesman_ini_file.set('Globals', 'DefaultWindowManager', self.defaultWindowManagerEntryBox.text())
            self.defaultWindowManagerEntryBox.setStyleSheet(self.line_edit_changed_stylesheet)
            self.sesman_changed()
            self.defaultWindowManagerEntryBox.setModified(0)

    # SESMAN [Security]

    def allowRootLoginCheckBoxChanged(self):
        if self.allowRootLoginCheckBox.checkState() == 2:
            self.sesman_ini_file.set('Security', 'AllowRootLogin', '1')
        else:
            self.sesman_ini_file.set('Security', 'AllowRootLogin', '0')
        self.sesman_changed()
        self.allowRootLoginCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def alwaysCheckGroupCheckBoxChanged(self):
        if self.alwaysCheckGroupCheckBox.checkState() == 2:
            self.sesman_ini_file.set('Security', 'AlwaysGroupCheck', '1')
        else:
            self.sesman_ini_file.set('Security', 'AlwaysGroupCheck', '0')
        self.sesman_changed()
        self.alwaysCheckGroupCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def terminalServiceUsersEntryBoxChanged(self):
        if self.terminalServiceUsersEntryBox.isModified():
            self.sesman_ini_file.set('Security', 'TerminalServerUsers', self.terminalServiceUsersEntryBox.text())
            self.terminalServiceUsersEntryBox.setStyleSheet(self.line_edit_changed_stylesheet)
            self.sesman_changed()
            self.terminalServiceUsersEntryBox.setModified(0)

    def terminalServiceAdminsEntryBoxChanged(self):
        if self.terminalServiceAdminsEntryBox.isModified():
            self.sesman_ini_file.set('Security', 'TerminalServerAdmins', self.terminalServiceAdminsEntryBox.text())
            self.terminalServiceAdminsEntryBox.setStyleSheet(self.line_edit_changed_stylesheet)
            self.sesman_changed()
            self.terminalServiceAdminsEntryBox.setModified(0)

    def maxLoginRetrySpinBoxChanged(self, value):
        self.sesman_ini_file.set('Security', 'MaxLoginRetry', str(value))
        self.maxLoginRetrySpinBox.setStyleSheet(self.spinbox_changed_stylesheet)
        self.sesman_changed()

    # SESMAN [Sessions]
    def x11DisplayOffsetSpinBoxChanged(self, value):
        self.sesman_ini_file.set('Sessions', 'X11DisplayOffset', str(value))
        self.x11DisplayOffsetSpinBox.setStyleSheet(self.spinbox_changed_stylesheet)
        self.sesman_changed()

    def maxSessionsSpinBoxChanged(self, value):
        self.sesman_ini_file.set('Sessions', 'MaxSessions', str(value))
        self.maxSessionsSpinBox.setStyleSheet(self.spinbox_changed_stylesheet)
        self.sesman_changed()

    def idleTimeLimitSpinBoxChanged(self, value):
        self.sesman_ini_file.set('Sessions', 'IdleTimeLimit', str(value))
        self.idleTimeLimitSpinBox.setStyleSheet(self.spinbox_changed_stylesheet)
        self.sesman_changed()

    def disconnectedTimeLimitSpinBoxChanged(self, value):
        self.sesman_ini_file.set('Sessions', 'DisconnectedTimeLimit', str(value))
        self.disconnectedTimeLimitSpinBox.setStyleSheet(self.spinbox_changed_stylesheet)
        self.sesman_changed()

    def killDisconnectedCheckBoxChanged(self):
        if self.killDisconnectedCheckBox.checkState() == 2:
            self.sesman_ini_file.set('Sessions', 'KillDisconnected', '1')
        else:
            self.sesman_ini_file.set('Sessions', 'KillDisconnected', '0')
        self.sesman_changed()
        self.killDisconnectedCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    # SESMAN [Logging]

    def sesmanLogFileNameEntryBoxChanged(self):
        if self.sesmanLogFileNameEntryBox.isModified():
            self.sesman_ini_file.set('Logging', 'LogFile', self.sesmanLogFileNameEntryBox.text())
            self.sesmanLogFileNameEntryBox.setStyleSheet(self.line_edit_changed_stylesheet)
            self.sesman_changed()
            self.sesmanLogFileNameEntryBox.setModified(0)

    def sesmanLogLevelComboBoxChanged(self):
        if not self.sesman_ini_file.has_option('Logging', 'LogLevel'):
            self.sesman_ini_file.set('Logging', 'LogLevel', 'DEBUG')
        self.sesman_ini_file.set('Logging', 'LogLevel', self.sesmanLogLevelComboBox.currentText())
        self.sesmanLogLevelComboBox.setStyleSheet(self.combobox_changed_stylesheet)
        self.sesman_changed()
        self.sesmanSyslogLevelChanged()

    def sesmanEnableSyslogChanged(self):
        if not self.sesman_ini_file.has_option('Logging', 'EnableSyslog'):
            self.sesman_ini_file.set('Logging', 'EnableSyslog', '0')
        if self.enableSesmanSyslogCheckBox.checkState() == 0:
            self.sesman_ini_file.set('Logging', 'EnableSyslog', "0")
            self.label_32.setEnabled(False)
            self.sesmanSysLogLevelComboBox.setEnabled(False)
            if self.sesman_ini_file.has_option('Logging', 'SyslogLevel'):
                self.sesman_ini_file.remove_option('Logging', 'SyslogLevel')
        else:
            self.sesman_ini_file.set('Logging', 'EnableSyslog', "yes")
            self.label_32.setEnabled(True)
            self.sesmanSysLogLevelComboBox.setEnabled(True)
            self.sesman_ini_file.set('Logging', 'SyslogLevel', self.sysLogLevelComboBox.currentText())
            self.sesmanSyslogLevelChanged()
        self.sesman_changed()
        self.enableSesmanSyslogCheckBox.setStyleSheet(self.checkbox_changed_stylesheet)

    def sesmanSyslogLevelChanged(self):
        if self.sesman_ini_file.has_option('Logging', 'SyslogLevel'):
            if self.sesmanSysLogLevelComboBox.currentIndex() > self.sesmanLogLevelComboBox.currentIndex():
                self.sesman_ini_file.set('Logging', 'SyslogLevel', self.sesman_ini_file.get('Logging', 'SyslogLevel'))
                self.sesmanSysLogLevelComboBox.setCurrentIndex(self.sesmanLogLevelComboBox.currentIndex())
            else:
                self.sesman_ini_file.set('Logging', 'SyslogLevel', self.sesmanSysLogLevelComboBox.currentText())
        self.sesman_changed()
        self.sesmanSysLogLevelComboBox.setStyleSheet(self.combobox_changed_stylesheet)

    # SESMAN [X11rdp] and [Xvnc]
    # Turns the human-readable X11rdp and Xvnc back-end X server command line switches
    # into "paramX=" INI file format.
    # Depending on the calling function (e.g. if the X11rdp or Xvnc line was altered), the function handles to suit.
    def xserverParamsChanged(self):
        calling_function = self.sender().objectName()
        if calling_function == "x11rdpParamsLineEdit":
            secname = "X11rdp"
            widget = self.x11rdpParamsLineEdit
        elif calling_function == "xvncParamsLineEdit":
            secname = "Xvnc"
            widget = self.xvncParamsLineEdit
        for option in self.sesman_ini_file.items(secname):
            self.sesman_ini_file.remove_option(secname, option[0])
        param_num = 1
        if widget.isModified():
            if widget.text() == "":
                return
            else:
                for value in widget.text().split():
                    param = "param" + str(param_num)
                    if value != '':
                        self.sesman_ini_file.set(secname, param, value)
                    param_num += 1
                widget.setStyleSheet(self.line_edit_changed_stylesheet)
                self.something_sesman_changed = 1
                self.settitleforsesman()

    @staticmethod
    def resetPage(parent_widget):
        types = [QtGui.QLineEdit, QtGui.QSpinBox, QtGui.QCheckBox, QtGui.QComboBox]
        for reset_list in types:
            for widget in parent_widget.findChildren(reset_list):
                if (reset_list == QtGui.QCheckBox) or (reset_list == QtGui.QComboBox):
                    widget.setStyleSheet("")
                else:
                    widget.setStyleSheet("")
                    widget.clear()

# xrdpconfigurator.setStyle("cleanlooks") <--Uncomment this, change to your chosen Qt look if you want it hard coded.
xrdpconfigurator = QtGui.QApplication(sys.argv)
window = XRDPConfigurator()
window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
winSim = LoginWindowSimulator(None)
# At startup, we need to "display" the Login Window Simulator window then hide again, because
# otherwise the Qt widgets don't seem to get initialised properly.
#
# For example - if I don't do this, the colour "swatches" in the Login Simulator
# don't get initialised, and odd things then happen.

winSim.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)
winSim.setAttribute(QtCore.Qt.WA_DontShowOnScreen, True)
winSim.show()
winSim.hide()
window.setupColourSelector()
window.setupWinSimButtonConnections()
winSim.setAttribute(QtCore.Qt.WA_DontShowOnScreen, False)
window.setWindowIcon(QtGui.QPixmap(":/icons/images/icons/XRDPConfiguratorWindowIcon.png"))
winSim.setWindowIcon(QtGui.QPixmap(":/icons/images/icons/XRDPConfiguratorWindowIcon.png"))
window.filenameFrame.setVisible(False)
window.sesmanIniEditPage.setVisible(False)
window.newsesswindow = NewSession()  # <-- new session window
window.show()
xrdpconfigurator.exec_()
xrdpconfigurator.deleteLater()
sys.exit()
