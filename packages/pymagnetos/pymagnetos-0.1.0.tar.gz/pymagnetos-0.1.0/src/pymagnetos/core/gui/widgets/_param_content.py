"""
Define various parameters to set in a PyQtGraph Parameter Tree.

To be able to automatically update them from the configuration file, their name should
match exactly the one in the configuration file.
Use the "title" kwarg to set the displayed name on the widget.

It is used in the ConfigurationWidget.
"""


class BaseParamContent:
    PARAMS_TO_PARSE: list[str]
    children_files: list[dict[str, str | bool]] = [
        dict(name="file", type="file", value="", title="Configuration file"),
        dict(name="expid", type="str", value="", readonly=False, title="Experiment ID"),
        dict(name="autoload", type="bool", value=True, title="Load data automatically"),
    ]
    children_parameters: list[dict[str, str | bool | list | float | int | None]]
    children_settings: list[dict[str, str | bool | list | float | int | None]]
