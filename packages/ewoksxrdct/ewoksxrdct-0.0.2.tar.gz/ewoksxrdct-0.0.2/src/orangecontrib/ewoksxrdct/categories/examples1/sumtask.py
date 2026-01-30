from AnyQt import QtWidgets
from ewoksorange.gui.owwidgets.threaded import OWEwoksWidgetOneThread

from ewoksxrdct.tasks.sumtask import SumTask1

__all__ = ["OWSumTask1"]


class OWSumTask1(OWEwoksWidgetOneThread, ewokstaskclass=SumTask1):
    ########################################
    # Attributes required by Orange:
    ########################################
    name = "SumTask1"
    description = "Adds two numbers"
    icon = "icons/sum.png"

    ########################################
    # Overwriten methods of the base class:
    ########################################

    def __init__(self) -> None:
        super().__init__()
        self._init_control_area()
        self._init_main_area()

    def _init_control_area(self) -> None:
        """Create widgets related to task inputs and add them to the 'control area'."""
        super()._init_control_area()

        self._input_widgets = QtWidgets.QWidget()
        self._get_control_layout().addWidget(self._input_widgets)

        grid = QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        self._input_widgets.setLayout(grid)

        self._widgetA_label = QtWidgets.QLabel("A")
        self._widgetA_value = QtWidgets.QSpinBox()
        grid.addWidget(self._widgetA_label, 0, 0)
        grid.addWidget(self._widgetA_value, 0, 1)

        self._widgetB_label = QtWidgets.QLabel("B")
        self._widgetB_value = QtWidgets.QSpinBox()
        grid.addWidget(self._widgetB_label, 1, 0)
        grid.addWidget(self._widgetB_value, 1, 1)

        self._widgetDelay_label = QtWidgets.QLabel("Delay")
        self._widgetDelay_value = QtWidgets.QDoubleSpinBox()
        grid.addWidget(self._widgetDelay_label, 2, 0)
        grid.addWidget(self._widgetDelay_value, 2, 1)

        # Fill all input widget values with the "default inputs" (saved in workflow file)
        self._set_input_widget_values(self.get_default_input_values())

        # Register a callback for when the user edits an input widget
        self._widgetA_value.editingFinished.connect(self._default_inputs_changed)
        self._widgetB_value.editingFinished.connect(self._default_inputs_changed)
        self._widgetDelay_value.editingFinished.connect(self._default_inputs_changed)

    def _init_main_area(self) -> None:
        """Create widgets related to task outputs and add them to the 'control area'."""
        super()._init_main_area()

        self._output_widgets = QtWidgets.QWidget()
        self._get_main_layout().addWidget(self._output_widgets)

        grid = QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        self._output_widgets.setLayout(grid)

        self._widgetResult_label = QtWidgets.QLabel("Result")
        self._widgetResult_value = QtWidgets.QLineEdit()
        grid.addWidget(self._widgetResult_label, 0, 0)
        grid.addWidget(self._widgetResult_value, 0, 1)

    def _default_inputs_changed(self) -> None:
        """Called when the value of one input widget is changed by the users.
        Take the widget values as task input values. These values are known as
        the task "default inputs" and will be saved in the workflow file.
        To optimize you should make a separate callback for each input widget
        """
        self.update_default_inputs(**self._get_input_widget_values())

    def handleNewSignals(self) -> None:
        """Called when a previous workflow node has been executed. Take the
        output values of the previous workflow node as task input values.
        These values are known as "dynamic inputs" and overwrite the "default inputs".
        """
        self._set_input_widget_values(self.get_dynamic_input_values())
        super().handleNewSignals()

    def task_output_changed(self) -> None:
        """Called when the task finished."""
        self._set_output_widget_values(self.get_task_output_values())
        super().task_output_changed()

    ########################################
    # Custom methods:
    ########################################

    def _get_input_widget_values(self) -> dict:
        """Get all values from the input widgets"""
        return {
            "a": self._widgetA_value.value(),
            "b": self._widgetB_value.value(),
            "delay": self._widgetDelay_value.value(),
        }

    def _set_input_widget_values(self, data: dict) -> None:
        """Set all values from the input widgets"""
        for name, value in data.items():
            if name == "a":
                self._widgetA_value.setValue(value)
            elif name == "b":
                self._widgetB_value.setValue(value)
            elif name == "delay":
                self._widgetDelay_value.setValue(value)

    def _set_output_widget_values(self, data: dict) -> None:
        """Set all values from the output widgets"""
        for name, value in data.items():
            if name == "result":
                self._widgetResult_value.setText(str(value))
