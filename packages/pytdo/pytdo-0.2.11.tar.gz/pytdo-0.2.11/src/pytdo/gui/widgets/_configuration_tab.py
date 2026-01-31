from PyQt6.QtCore import pyqtSignal
from pyqtgraph.parametertree import Parameter
from pyuson import gui


class ConfigurationWidget(gui.widgets.BaseConfigurationWidget):
    """
    Configuration Parameter Tree for TDO experiments.

    Base : pyuson.gui.widgets.BaseConfigurationWidget

    Extra signals :
    sig_syncroi_changed : emitted when the "Sync ROI" checkbox is changed.
    sig_timeoffset_changed : emitted when the "Time offset" parameter is changed.
    sig_fitdeg_changed : emitted when the n points interp 1/B parameter is changed.
    """

    sig_syncroi_changed = pyqtSignal()
    sig_timeoffset_changed = pyqtSignal()
    sig_spectro_nperseg_changed = pyqtSignal()
    sig_fitdeg_changed = pyqtSignal()
    sig_npoints_interp_changed = pyqtSignal()
    sig_curveoffset_changed = pyqtSignal()

    def __init__(self, param_content: type):
        super().__init__(param_content)

        self.add_extra_parameters()
        self.connect_extras()

    def add_extra_parameters(self):
        """Add extra parameters used only in the GUI."""
        # Sync ROIs parameter
        self.syncroi_parameter = Parameter.create(
            name="syncroi",
            type="bool",
            value=False,
            title="Sync. fit and FFT field-window",
        )
        self.host_parameters.addChild(self.syncroi_parameter)

        # Show nperseg parameter in µs
        nperseg = Parameter.create(
            name="spectro_time_window",
            type="float",
            readonly=True,
            value=1024 / 100e6,
            suffix="s",
            siPrefix=True,
            title="Spectro: time window (n/persegment)",
        )
        self.host_parameters.addChild(nperseg)

    def connect_extras(self):
        """Extra connections."""
        self.syncroi_parameter.sigValueChanged.connect(self.sig_syncroi_changed.emit)
        self.settings_parameters.child("time_offset").sigValueChanged.connect(
            self.sig_timeoffset_changed.emit
        )
        self.settings_parameters.child("spectro_nperseg").sigValueChanged.connect(
            self.sig_spectro_nperseg_changed.emit
        )
        self.settings_parameters.child("poly_deg").sigValueChanged.connect(
            self.sig_fitdeg_changed.emit
        )
        self.settings_parameters.child(
            "npoints_interp_inverse"
        ).sigValueChanged.connect(self.sig_npoints_interp_changed.emit)
        self.settings_parameters.child("offset").sigValueChanged.connect(
            self.sig_curveoffset_changed.emit
        )
