import sys

from PyQt5 import QtSvg, Qt, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from statemachine import StateMachine, State
from svgelements import SVG
from pyqt_tools import messages

import cdm_bindings
from pycdm import PyCDM, Cfg
from pycdm.structs import BsdaSettings, FramingType, EbiSettings
from .ui_form import Ui_MainWindow


class PyCdmStateMachine(StateMachine):
    disconnected = State(initial=True)
    cdm_connected = State()
    ebi_connected = State()
    bcg_configured = State()

    connect_cdm = (disconnected.to(cdm_connected))
    connect_ebis = (cdm_connected.to(ebi_connected))
    configure_bcg = (cdm_connected.to(bcg_configured))
    disconnect_ebis = (ebi_connected.to(cdm_connected))

    def __init__(self, widget):
        super().__init__()
        self._w = widget
        self._previous_properties = {}
        # After restoring pixmap property the text disappears. As a workaround create a list of properties
        # that we change and restore only those.
        self._valid_properties = ["enabled", "text", "styleSheet"]

    def on_enter_cdm_connected(self, v = None):
        self._w.ui.connectEbiButton.setEnabled(True)
        self._w.ui.connectCdmButton.setDisabled(True)
        if v:
            self._w.statusBar().showMessage("Running CDM version {} with git {} ".format(v["version"], v["git"]))

    def on_enter_ebi_connected(self, e, s):
        self._store_properties()
        self._w.ui.connectEbiButton.setDisabled(True)
        self._w.ui.disconnectEbiButton.setEnabled(True)
        self._w.ui.configureButton.setEnabled(True)

        el = e["ebi_left"]
        self._w.ui.label_ebi_left_git.setText(el["git"])
        self._w.ui.label_ebi_left_version.setText(el["version"])
        self._w.ui.label_ebi_left_status.setStyleSheet("color: green;")
        self._w.ui.label_ebi_left_status.setText("CONNECTED")

        er = e["ebi_right"]
        self._w.ui.label_ebi_right_git.setText(er["git"])
        self._w.ui.label_ebi_right_version.setText(er["version"])

        bcg_left = s["left"]
        bcg_right = s["right"]

        def getEbiTextAndColor(ebi_status):
            ebi_color = "color: green;"
            if ebi_status == 0:
                ebi_text = "Initialized"
            elif ebi_status == 1:
                ebi_text = "Ready"
            elif ebi_status == 2:
                ebi_text = "Reading"
            elif ebi_status == 3:
                ebi_text = "Dead"
                ebi_color = "color: read;"
            else:
                ebi_text = "Unkown"
                ebi_color = "color: read;"

            return ebi_text, ebi_color

        text, color = getEbiTextAndColor(bcg_left["ebi"])
        self._w.ui.label_ebi_right_status.setText(text.upper())
        self._w.ui.label_ebi_right_status.setStyleSheet(color)

        text, color = getEbiTextAndColor(bcg_right["ebi"])
        self._w.ui.label_ebi_right_status.setText(text.upper())
        self._w.ui.label_ebi_right_status.setStyleSheet(color)

        def get_bsda_text_and_color(bsda_status):
            bsda_color = "color: green;"
            if bsda_status == 0:
                bsda_text = "Initialized"
            elif bsda_status == 1:
                bsda_text = "Ready"
            elif bsda_status == 2:
                bsda_text = "Reading"
            elif bsda_status == 3:
                bsda_text = "Dead"
                bsda_color = "color: red;"
            elif bsda_status == 4:
                bsda_text = "Disabled"
                bsda_color = "color: yellow;"
            else:
                bsda_text = "Unkown"
                bsda_color = "color: read;"

            return bsda_text, bsda_color

        for i in range(3):
            text, color = get_bsda_text_and_color(bcg_left["bsda"][i])
            tmp = getattr(self._w.ui, "bsdaL{}Label".format(i))
            tmp.setText(text.upper())
            tmp.setStyleSheet(color)

        for i in range(3):
            text, color = get_bsda_text_and_color(bcg_right["bsda"][i])
            tmp = getattr(self._w.ui, "bsdaR{}Label".format(i))
            tmp.setText(text.upper())
            tmp.setStyleSheet(color)

    def on_exit_ebi_connected(self):
        self._restore_properties()

    def on_enter_bcg_configured(self):
        self._w.ui.disconnectEbiButton.setEnabled(True)
        self._w.ui.startButton.setEnabled(True)

    def _store_properties(self):
        for i in self._w.ui.__dict__:
            v = self._w.ui.__dict__[i]
            mo = v.metaObject()
            for j in range(mo.propertyCount()):
                pn = mo.property(j).name()
                if pn in self._valid_properties:
                    key = "{}_{}".format(v.objectName(), pn)
                    self._previous_properties[key] = mo.property(j).read(v)

    def _restore_properties(self):
        for i in self._w.ui.__dict__:
            v = self._w.ui.__dict__[i]
            mo = v.metaObject()
            for j in range(mo.propertyCount()):
                pn = mo.property(j).name()
                if pn in self._valid_properties:
                    key = "{}_{}".format(v.objectName(), pn)
                    v.setProperty(pn, self._previous_properties[key])


class Widget(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cdm = None
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.connectCdmButton.clicked.connect(self._connect_cdm)
        self.ui.connectEbiButton.clicked.connect(self._connect_ebis)
        self.ui.disconnectEbiButton.clicked.connect(self._disconnect_ebis)
        self.ui.configureButton.clicked.connect(self._configure_bcg)
        self.ui.serverEdit.setText(Cfg().get_cdm_addr())
        self._sm = PyCdmStateMachine(self)

        self._svg_widget = QtSvg.QSvgWidget("/tmp/cdm.svg", self.ui.svgContainer)
        self.ui.svgContainer.adjustSize()
        self._svg_widget.resize(Qt.QSize(self.ui.svgContainer.minimumSize()))
        self.ui.svgContainer.update()
        self._svg_widget.update()
        self._svg_widget.show()

    def closeEvent(self, event):
        if self._cdm:
            self._cdm.close()

    def _connect_cdm(self):
        try:
            def send_connect():
                e = self._cdm.ebi.version()
                s = self._cdm.bcg.get_state()
                self._sm.send("connect_ebis", e, s)

            self._cdm = PyCDM(self.ui.serverEdit.text())
            v = self._cdm.cdm.get_info()
            self._sm.send("connect_cdm", v)

            state = self._cdm.cdm.get_sm_state()
            if state == cdm_bindings.SM_STATE.ERBI_READY:
                send_connect()
            elif state == cdm_bindings.SM_STATE.BSDA_READY:
                send_connect()
                self._sm.send("configure_bcg")

        except Exception as e:
            messages.show_fatal(e, "Fatal error")

    def _connect_ebis(self):
        try:
            e = self._cdm.ebi.connect()
            # e = {'ebi_left': {'git': 'heads/dev-0-g027d9c1-dirty', 'name': 'erbi', 'version': '0.0.1'}, 'ebi_right': {'git': 'heads/dev-0-g027d9c1-dirty', 'name': 'erbi', 'version': '0.0.1'}}
            s = self._cdm.bcg.get_state()
            self._sm.send("connect_ebis", e, s)
        except Exception as e:
            messages.show_fatal(e, "Fatal error")

    def _disconnect_ebis(self):
        try:
            self._cdm.ebi.disconnect()
        except Exception as e:
            messages.show_fatal(e, "Fatal error")
        self._sm.send("disconnect_ebis")

    def _configure_bcg(self):
        try:
            bsda = BsdaSettings()
            selected_framing_type = self.ui.framingTypeComboBox.currentText().upper()
            if selected_framing_type == "FULL":
                bsda.framing = FramingType.FULL
            elif selected_framing_type == "SUM":
                bsda.framing = FramingType.SUM
            elif selected_framing_type == "HISTOGRAM":
                bsda.framing = FramingType.HISTOGRAM
            elif selected_framing_type == "TEST":
                bsda.framing = FramingType.TEST
            elif selected_framing_type == "SUM SQUARED":
                bsda.framing = FramingType.SUM_SQ
            else:
                raise Exception("Invalid framing type found \"{}\"".format(selected_framing_type))

            bsda.frame_duration_us = self.ui.frameDurationUsSpinBox.value()
            bsda.temperature_period_ms = self.ui.temperaturePeriodMsSpinBox.value()
            bsda.disabled = False
            bsda.light_enabled = self.ui.enableLightCheckBox.isEnabled()
            bsda.temperature_enabled = self.ui.enableTemperatureCheckBox.isEnabled()
            # TODO: Allow to configure ADC shadow
            bsda.adc_shadow = [0xf9f0, 0xf9f0]
            bsda.log_uart = True
            bsda.log_level = 3

            bsda_disabled = BsdaSettings()
            bsda_disabled.disabled = True

            left = EbiSettings()
            left.frame_reader_framing_type = bsda.framing
            left.frame_reader_period_ms = self.ui.elFramePeriodMsSpinBox.value()
            left.temperature_reader_period_ms = self.ui.elTemperaturePeriodMsSpinBox.value()
            left.bsda_settings[0] = bsda if self.ui.bsdaL0checkBox.isEnabled() else bsda_disabled
            left.bsda_settings[1] = bsda if self.ui.bsdaL1checkBox.isEnabled() else bsda_disabled
            left.bsda_settings[2] = bsda if self.ui.bsdaL2checkBox.isEnabled() else bsda_disabled
            left.log_uart = bsda.log_uart
            left.log_level = bsda.log_level

            right = EbiSettings()
            right.frame_reader_framing_type = bsda.framing
            right.frame_reader_period_ms = self.ui.erFramePeriodMsSpinBox.value()
            right.temperature_reader_period_ms = self.ui.erTemperaturePeriodMsSpinBox.value()
            right.bsda_settings[0] = bsda if self.ui.bsdaR0checkBox.isEnabled() else bsda_disabled
            right.bsda_settings[1] = bsda if self.ui.bsdaR1checkBox.isEnabled() else bsda_disabled
            right.bsda_settings[2] = bsda if self.ui.bsdaR2CheckBox.isEnabled() else bsda_disabled
            right.log_uart = bsda.log_uart
            right.log_level = bsda.log_level
            self._cdm.configure(left, right)
        except Exception as e:
            messages.show_fatal(e, "Fatal error")

        self._sm.send("configure_bcg")


def main():
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
