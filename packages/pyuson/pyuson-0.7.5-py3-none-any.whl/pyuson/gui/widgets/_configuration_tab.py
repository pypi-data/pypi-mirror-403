"""
The Configuration tab.

Contains the PyQtGraph ParameterTree that represents a configuration file, hosting all
the parameters and settings for the analysis.
"""

import re
from functools import partial

from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtSignal
from pyqtgraph.parametertree import Parameter, ParameterTree


class BaseConfigurationWidget(QtWidgets.QWidget):
    """
    Initialize a PyQtGraph ParameterTree.

    Signals
    -------
    sig_file_changed : emits when the file parameter changed.
    sig_expid_changed : emits when the "Reload data" button is clicked or the experiment
        ID parameter changed.
    sig_autoload_changed : emits when the autoload checkbox in the File section is
        changed.
    sig_reload_config : emits when the "Reload config" button is clicked.
    sig_save_config : emits when the "Save config" button is clicked.
    sig_parameter_changed : emits when any other parameter in the tree is changed. Emits
        the parameter name and the scope ("parameters", "settings").
    """

    sig_file_changed = pyqtSignal()
    sig_expid_changed = pyqtSignal()
    sig_autoload_changed = pyqtSignal()

    sig_save_config = pyqtSignal()
    sig_reload_config = pyqtSignal()

    sig_parameter_changed = pyqtSignal(str, str)

    def __init__(self, param_content: type):
        super().__init__()
        self._param_content = param_content
        self.parameters_to_parse = self._param_content.PARAMS_TO_PARSE

        # Create trees and buttons
        self.init_files_tree()
        self.init_buttons()
        self.init_configuration_tree()

        # Connect
        self.connect_to_signals()

        # Create layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.files_tree, stretch=3)
        layout.addWidget(self.widget_buttons, stretch=1)
        layout.addWidget(self.config_tree, stretch=10)

        self.setLayout(layout)

    def init_files_tree(self):
        # Files section
        self.files_parameters = Parameter.create(
            name="Files", type="group", children=self._param_content.children_files
        )
        self.files_tree = ParameterTree(showHeader=False)
        self.files_tree.setParameters(self.files_parameters)

    def init_buttons(self):
        # Create buttons
        self.button_reload_data = QtWidgets.QPushButton("Reload data", self)
        self.button_reload_config = QtWidgets.QPushButton("Reload config", self)
        self.button_save_config = QtWidgets.QPushButton("Save config", self)

        # Connect
        self.button_reload_data.clicked.connect(self.sig_expid_changed.emit)
        self.button_reload_config.clicked.connect(self.sig_reload_config.emit)
        self.button_save_config.clicked.connect(self.sig_save_config)

        # Create a layout
        layout_buttons = QtWidgets.QHBoxLayout(self)
        layout_buttons.addWidget(self.button_reload_data)
        layout_buttons.addWidget(self.button_reload_config)
        layout_buttons.addWidget(self.button_save_config)
        self.widget_buttons = QtWidgets.QWidget(self)
        self.widget_buttons.setLayout(layout_buttons)

    def init_configuration_tree(self):
        # Parameters section
        self.param_parameters = Parameter.create(
            name="Parameters",
            type="group",
            children=self._param_content.children_parameters,
        )
        # Settings section
        self.settings_parameters = Parameter.create(
            name="Settings",
            type="group",
            children=self._param_content.children_settings,
        )

        # Host Tree
        self.host_parameters = Parameter.create(
            name="Configuration",
            type="group",
            children=[
                self.param_parameters,
                self.settings_parameters,
            ],
        )
        self.config_tree = ParameterTree(showHeader=False)
        self.config_tree.setParameters(self.host_parameters)

    def get_numbers_from_text(self, inds: str | list | tuple) -> list[float] | str:
        """Parse input as list of numbers, or the other way around."""
        if isinstance(inds, str):
            pattern = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
            return [float(el) for el in re.findall(pattern, inds)]
        elif isinstance(inds, list | tuple):
            return ", ".join(f"{int(e)}" if int(e) == e else f"{e:.4f}" for e in inds)

    def connect_to_signals(self):
        """Connect changes to signals."""
        self.files_parameters.child("file").sigValueChanged.connect(
            self.sig_file_changed.emit
        )
        self.files_parameters.child("expid").sigValueChanged.connect(
            self.sig_expid_changed.emit
        )
        self.files_parameters.child("autoload").sigValueChanged.connect(
            self.sig_autoload_changed.emit
        )

        for p in self.param_parameters:
            self.param_parameters.child(p.name()).sigValueChanged.connect(
                partial(self.sig_parameter_changed.emit, p.name(), "parameters")
            )

        for p in self.settings_parameters:
            self.settings_parameters.child(p.name()).sigValueChanged.connect(
                partial(self.sig_parameter_changed.emit, p.name(), "settings")
            )

    def enable_buttons(self):
        self.button_reload_data.setEnabled(True)
        self.button_reload_config.setEnabled(True)
        self.button_save_config.setEnabled(True)

    def disable_buttons(self):
        self.button_reload_data.setEnabled(False)
        self.button_reload_config.setEnabled(False)
        self.button_save_config.setEnabled(False)


class ConfigurationWidget(BaseConfigurationWidget):
    """
    Initialize a PyQtGraph ParameterTree.

    Signals
    -------
    sig_echo_index_changed : emits when the echo index (in the Settings section ) is
        changed.
    sig_find_f0 : emits when the "Find f0" button is clicked.
    sig_demodulate : emits when the "Demodulate" button is clicked.
    """

    sig_echo_index_changed = pyqtSignal()
    sig_find_f0 = pyqtSignal()
    sig_demodulate = pyqtSignal()

    def __init__(self, param_content: type):
        super().__init__(param_content)

    def init_demodulation_tree(self):
        """Create ParameterTree for demodulation parameters."""
        self.demodulation_parameters = Parameter.create(
            name="Demodulation",
            type="group",
            children=self._param_content.children_demodulation,
        )
        self.host_parameters.addChild(self.demodulation_parameters)

        # Store buttons as the others
        self.button_findf0 = self.demodulation_parameters.child("find_f0")
        self.button_findf0.setOpts(enabled=False)
        self.button_demodulate = self.demodulation_parameters.child("demodulate")
        self.button_demodulate.setOpts(enabled=False)

        self.connect_to_signals_demodulation()

    def connect_to_signals(self):
        """Connect changes to signals."""
        super().connect_to_signals()

        # Special case for echo_index to sync it with another spinbox in the Batch
        # processing tab
        self.settings_parameters.child("echo_index").sigValueChanged.connect(
            self.sig_echo_index_changed.emit
        )

    def connect_to_signals_demodulation(self):
        """Additionnal connections for demodulation."""
        self.button_findf0.sigActivated.connect(self.sig_find_f0.emit)
        self.button_demodulate.sigActivated.connect(self.sig_demodulate.emit)

        for p in self.demodulation_parameters:
            self.demodulation_parameters.child(p.name()).sigValueChanged.connect(
                partial(self.sig_parameter_changed.emit, p.name(), "demodulation")
            )

    def enable_buttons(self):
        super().enable_buttons()
        if hasattr(self, "button_findf0"):
            self.button_findf0.setOpts(enabled=True)
        if hasattr(self, "button_demodulate"):
            self.button_demodulate.setOpts(enabled=True)

    def disable_buttons(self):
        super().disable_buttons()
        if hasattr(self, "button_findf0"):
            self.button_findf0.setOpts(enabled=False)
        if hasattr(self, "button_demodulate"):
            self.button_demodulate.setOpts(enabled=False)
