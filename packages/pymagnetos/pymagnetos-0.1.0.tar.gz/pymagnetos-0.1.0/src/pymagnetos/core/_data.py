"""Classes to store data as NeXus objects."""

import importlib.metadata

import nexusformat.nexus as nx


class DataBase(nx.NXgroup):
    """Base Data class integrating NXgroup."""

    def __init__(self, attr: dict = {}, **kwargs) -> None:
        """
        Base Data class integrating NXgroup [1].

        `DataBase` should be used for subclassing. It allows to create a NXgroup with
        attributes specified as a dictionary.

        [1] https://nexpy.github.io/nexpy/treeapi.html#nexusformat.nexus.tree.NXgroup

        Parameters
        ----------
        attr : dict, optional
            Attributes for the NXgroup. Default is an empty dictionary.
        **kwargs : passed to `nexusformat.NXgroup()`.
        """
        super().__init__(**kwargs)

        # Set attributes
        for k, v in attr.items():
            self.attrs[k] = v


class DataRaw(DataBase):
    """Store raw data in a NeXus NXdata group."""

    def __init__(self, attr: dict = {}, **kwargs) -> None:
        """
        Store raw data in a NeXus group.

        The instantiated object will be of type `nexusformat.nexus.NXdata` [1].

        [1] https://nexpy.github.io/nexpy/treeapi.html#nexusformat.nexus.tree.NXdata

        Parameters
        ----------
        attr : dict, optional
            Attribute for the NXdata group. Default is an empty dictionary.
        **kwargs : passed to `pyuson.data.DataBase()`.
        """
        super().__init__(attr=attr, **kwargs)

        # Convert to NXdata
        self.nxclass = "NXdata"
        self.nxname = "data"


class DataProcessed(DataBase):
    """Store processed data in a NeXus NXprocess group."""

    def __init__(
        self,
        program: str = "generic",
        results_name: str = "results",
        serie_name: str = "serie",
        attr: dict = {},
        **kwargs,
    ) -> None:
        """
        Store processed data in a NeXus group.

        The instantiated object will be of type `nexusformat.nexus.NXprocess` [1]. It
        behaves like it, with an additional `create_serie()` method, that adds an NXData
        group.

        It has the following structure :
        ```
        analysis:NXprocess
          date = '2025-08-05T13:28:48.974923'
          program = '{program}'
          {results_name}:NXdata
          {results_name}_{serie_name}{serie_index}:NXdata
          version = '0.1.10'
        ```

        [1] https://nexpy.github.io/nexpy/treeapi.html#nexusformat.nexus.tree.NXprocess

        Parameters
        ----------
        program : str, optional
            Name of the package used to create the object. Must be an installed Python
            package. Default is the `PKG_NAME` global variable.
        results_name : str, optional
            Name of the results Nexus NXData group. Default is 'results'.
        serie_name : str, optional
            Name that will be appended to `results_name`, along with the serie index, to
            build the name of the per-serie Nexus NXData group. Default is 'serie'.
        attr : dict, optional
            Attribute for the NXdata group. Default is an empty dictionary.
        **kwargs : passed to `pyuson.data.DataBase()`.
        """
        self._res_name = results_name
        self._serie_name = serie_name

        super().__init__(attr=attr, **kwargs)

        # Inject method `create_serie()` before NXgroup changes __class__, making any
        # standard instance methods unbound
        nx.NXgroup.create_serie = lambda self, index: _create_serie(self, index)  # ty:ignore[unresolved-attribute]

        # Convert to NXprocess
        self.nxclass = "NXprocess"
        self.nxname = "analysis"

        # Create base datasets
        self["program"] = program
        self["version"] = importlib.metadata.version(program)
        self["results"] = nx.NXdata()

        def _create_serie(self: DataProcessed, index: int) -> None:
            """
            Create an NXdata group for serie data.

            The name of the created group is : '{results_name}_{serie_name}{index}'.

            Parameters
            ----------
            index : int
                Number appended to the serie name.
            """
            group_name = f"{self._res_name}_{self._serie_name}{index}"
            if group_name not in self:
                self[group_name] = nx.NXdata()
