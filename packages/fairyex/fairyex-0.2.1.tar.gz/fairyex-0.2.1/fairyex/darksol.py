import itertools
import logging
import mmap
import os
import tempfile
import time
from typing import Literal, TypeAlias
from xml.etree import ElementTree
from zipfile import ZipFile

import numpy as np
import pandas as pd
import polars as pl

from .kernel import (
    MastersEx, FLOAT_SIZE,
    query_horizon,
    query_classes, query_categories, query_children,
    query_phases, query_samples, query_samples_name,
    query_properties, query_property_id, query_property_unit,
    query_model_name, get_phase_id, get_period_type_id,
    query_timeslice_id
)
from .utils import QueryError


PivotType: TypeAlias = Literal["auto", "none", "property", "melt"]


def _get_period_type(period_type: str) -> str:
    period_type = period_type.lower()
    if period_type.startswith('i'):
        return "Interval"
    elif period_type.startswith('f') or period_type.startswith('y'):
        return "FiscalYear"
    raise TypeError(f"{period_type} is not a supported PeriodType!")


def _get_sample_name(sample_id: str) -> str:
    if statistic_name := {"-3": "Max", "-2": "Min", "-1": "Std", "0": "Mean"}.get(sample_id):
        return statistic_name
    elif sample_id.startswith('-'):
        return f"Statistic {sample_id[1:]}"
    return f"Sample {sample_id}"


def _get_xml_and_bin(zip_path: str) -> tuple:
    with ZipFile(zip_path) as zipsol:
        xml_name = next(filter(lambda filename: filename.endswith("Solution.xml"), zipsol.namelist()))
        with zipsol.open(xml_name) as xml_file:
            pointer = ElementTree.parse(xml_file)
        try:
            with zipsol.open("t_data_4.BIN") as bin_file:
                yearray = np.frombuffer(bin_file.read())
        except KeyError:
            yearray = None
        tmp_dir = tempfile.mkdtemp(prefix="DarkEx")
        try:
            bin_path = zipsol.extract("t_data_0.BIN", tmp_dir)
            logging.info(f"Temporary directory created: {tmp_dir}")
        except KeyError:
            os.rmdir(tmp_dir)
            bin_path = ""
    return pointer, bin_path, yearray


def _map_array(bin_path: str) -> tuple:
    with open(bin_path, "r+b") as memmap_bin:
        memmap = mmap.mmap(memmap_bin.fileno(), 0)
        array_length = len(memmap) // FLOAT_SIZE
        array_shape = (array_length,)
        array = np.ndarray(array_shape, buffer=memmap, dtype=float)
    return memmap, array


class DarkSol:
    def __init__(self, path: str):
        logging.basicConfig(level=logging.INFO, format="\x1b[35;20m%(levelname)s: %(message)s\x1b[0m")
        logging.debug("Loading solution...")
        start_time = time.time()
        self._pointer, self._bin, self._yearray = _get_xml_and_bin(path)
        self._kernel = MastersEx(self._pointer)
        if self._bin:
            self._memmap, self._array = _map_array(self._bin)
        else:
            self._memmap, self._array = None, None
        end_time = time.time()
        loading_time = round(end_time - start_time, 3)
        logging.info(f"Solution loaded in {loading_time} s, ready for extraction")
        self._horizon_type = None
        self._horizon = []
        self._is_closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self._is_closed or self._array is None:
            return
        self._memmap.close()
        os.remove(self._bin)
        os.rmdir(os.path.dirname(self._bin))
        logging.info(f"Temporary directory deleted: {self._bin}")
        self._is_closed = True

    def query_category(self, category_class: str) -> list:
        """Return the list of all available categories.

        Examples
        ________
        >>> from fairyex import DarkSol
        >>>
        >>> with DarkSol("Model Open World Solution.zip") as ds:
        >>>     ds.query_category()
        ["foo", "bar"]
        """
        categories = list(query_categories(self._pointer, category_class))
        if categories:
            categories.remove('-')
        return categories

    def query_class(self) -> list:
        """Return the list of all available classes.

        Examples
        ________
        >>> from fairyex import DarkSol
        >>>
        >>> with DarkSol("Model Open World Solution.zip") as ds:
        >>>     ds.query_class()
        ["Generator", "Reserve", "Region", "Node"]
        """
        return list(query_classes(self._pointer))

    def query_children(
            self,
            children_class: str,
            category: str = None,
            parent_class: str = "System",
            parent: str = "System"
    ) -> list:
        """Return the list of all children.

        Parameters
        __________
        children_class
            Which objects to query.

        category
            Filter children from a category listed in self.query_category(children_class).
            Default is None which means no filtering.

        parent_class
            Filter children by keeping only objects linked to another object from this class. Must be used with parent.
            Default is "System" which means no filtering.

        parent
            Filter children by keeping only objects linked to another object named parent.
            parent must be an object of class parent_class.
            Default is "System" which means no filtering.

        Examples
        ________
        >>> from fairyex import DarkSol
        >>>
        >>> # Assumption: each generator of this solution is named after its region followed by its category.
        >>> with DarkSol("Model Open World Solution.zip") as ds:
        >>>     ds.query_children("Generator")
        ["Limgrave foo", "Limgrave bar", "Caelid foo"]
        >>>
        >>>     ds.query_children("Generator", category="foo")
        ["Limgrave foo", "Caelid foo"]
        >>>
        >>>     ds.query_children("Generator", parent_class="Region", parent="Limgrave")
        ["Limgrave foo", "Limgrave bar"]
        """
        children = list(query_children(self._pointer, children_class, category))
        if children and parent_class != "System" and parent != "System":
            children = list(self._kernel.filter_children_from_parent(parent_class, parent, children_class, children))
        return children

    def query_model(self) -> str:
        """Return the name of the model.

        Examples
        ________
        >>> from fairyex import DarkSol
        >>>
        >>> with DarkSol("Model Open World Solution.zip") as ds:
        >>>     ds.query_model()
        "Open World"
        """
        return query_model_name(self._pointer)

    def query_phase(self) -> list:
        """Return the list of all available phases.

        Examples
        ________
        >>> from fairyex import DarkSol
        >>>
        >>> with DarkSol("Model Open World Solution.zip") as ds:
        >>>     ds.query_phase()
        ["LTPlan", "MTSchedule", "STSchedule"]
        """
        return list(query_phases(self._pointer))

    def query_property(self, children_class: str, parent_class: str = "System") -> list:
        """Return the list of all properties of a class.

        Examples
        ________
        >>> from fairyex import DarkSol
        >>>
        >>> with DarkSol("Model Open World Solution.zip") as ds:
        >>>     ds.query_property("Generator")
        ["Installed Capacity", "Generation"]
        >>>
        >>>     ds.query_property("Generator", "Reserve")
        ["Available Response", "Provision"]
        """
        return list(query_properties(self._pointer, children_class, parent_class))

    def query_sample(self, *, exclude_statistics: bool = False) -> list:
        """Return the list of all available samples, including the negative ones that corresponds to statistical values (e.g. "0" to "Mean").

        Parameters
        ----------
        .. versionadded:: 0.2.0: exclude_statistics (see below)
        exclude_statistics:
            Exclude negative samples

        Examples
        ________
        >>> from fairyex import DarkSol
        >>>
        >>> with DarkSol("Model Open World Solution.zip") as ds:
        >>>     ds.query_sample()
        ["0", "1", "2", "3"]
        >>>
        >>>     ds.query_sample(exclude_statistics=True)
        ["1", "2", "3"]
        """
        samples = query_samples(self._pointer)
        if exclude_statistics:
            samples = filter(lambda sample: int(sample) > 0, samples)
        return list(samples)

    def query_sample_name(self, *, ignore_errors: bool = True) -> dict:
        """.. versionadded:: 0.2.0
        Return a dict that matches the sample with its name.

        Parameters
        ----------
        ignore_errors
            If the samples have no name, raise a QueryError if `ignore_errors` is False,
            or if `ignore_errors` is True, these names will be given (default behaviour):

            - 0 is "Mean", -1 is "Std", -2 is "Min", -3 is "Max"
            - Other negative samples will be named as "Statistic"
            - Positive samples will be named as "Sample"

        Example
        -------
        >>> from fairyex import DarkSol
        >>>
        >>> with DarkSol("Model Open World Solution.zip") as ds:
        >>>     ds.query_sample_name()
        {'0': 'Mean', '1': 'Sample 1', '2': 'Sample 2', '3': 'Sample 3'}
        """
        samples_id = self.query_sample()
        samples_name = query_samples_name(self._pointer)
        try:
            return dict(zip(samples_id, samples_name))
        except AttributeError:
            if ignore_errors:
                logging.warning("No sample name found; return based on fairly dark assumption.")
                samples_name = map(_get_sample_name, samples_id)
                return dict(zip(samples_id, samples_name))
            raise QueryError("Sample has no <sample_name> attribute.")

    def _format_extraction(
            self,
            array,
            prefilter,
            sample_id,
            child_name=None,
            membership_id=None,
            memberships={},
            property_name=None,
            property_id=None,
            properties={},
    ):
        result = {}
        if child_name is not None:
            result["Name"] = child_name
        if property_name is not None:
            result["Property"] = property_name
        result |= {
            "Sample": sample_id,
            "Datetime": self._horizon
        }
        size = len(self._horizon)
        # pivot == "none"
        for child, memb_id in memberships.items():
            try:
                address, size = self._kernel.find_key_index(
                    prefilter=prefilter,
                    membership_id=memb_id,
                    sample_id=sample_id,
                    property_id=property_id,
                )
            except KeyError:
                raise QueryError(f"No data found for {property_name} of {child} with Sample {sample_id}")
            result |= {child: array[address:address + size].copy()}
        # pivot == "property"
        for prop, prop_id in properties.items():
            try:
                address, size = self._kernel.find_key_index(
                    prefilter=prefilter,
                    membership_id=membership_id,
                    sample_id=sample_id,
                    property_id=prop_id,
                )
            except KeyError:
                raise QueryError(f"No data found for {prop} of {child_name} with Sample {sample_id}")
            result |= {prop: array[address:address + size].copy()}
        # pivot == "melt"
        if not memberships and not properties:
            try:
                address, size = self._kernel.find_key_index(
                    prefilter=prefilter,
                    membership_id=membership_id,
                    sample_id=sample_id,
                    property_id=property_id,
                )
            except KeyError:
                raise QueryError(f"No data found for {property_name} of {child_name} with Sample {sample_id}")
            result |= {"Value": array[address:address + size].copy()}
        if skipped_hours := len(self._horizon) - size:
            # logging.info(f"Dark behaviour: last {skipped_hours} hours don't have values")
            result["Datetime"] = self._horizon[:size]
        return pl.DataFrame(result)

    def _process_extraction(
            self,
            array,
            prefilter,
            memberships,
            properties,
            samples,
            pivot,
    ) -> pl.DataFrame:
        if pivot == "auto":
            pivot = "property" if len(properties) >= len(memberships) else "none"
        if pivot == "property":
            return pl.concat((
                self._format_extraction(
                    array,
                    prefilter,
                    sample_id,
                    child_name=child,
                    membership_id=membership_id,
                    properties=properties,
                )
                for sample_id, (child, membership_id)
                in itertools.product(samples, memberships.items())
            ))
        elif pivot == "none":
            return pl.concat((
                self._format_extraction(
                    array,
                    prefilter,
                    sample_id,
                    memberships=memberships,
                    property_name=property_name,
                    property_id=property_id,
                )
                for sample_id, (property_name, property_id)
                in itertools.product(samples, properties.items())
            ))
        elif pivot == "melt":
            return pl.concat((
                self._format_extraction(
                    array,
                    prefilter,
                    sample_id,
                    child_name=child,
                    membership_id=membership_id,
                    property_name=property_name,
                    property_id=property_id,
                )
                for sample_id, (property_name, property_id), (child, membership_id)
                in itertools.product(samples, properties.items(), memberships.items())
            ))
        else:
            raise Exception(f"Unknown pivot option, must match {PivotType}")

    def _process_query(
            self,
            phase: str,
            children_class: str,
            children: list,
            properties: list,
            samples: list,
            parent_class: str = "System",
            parent: str = "System",
            band: str = '1',
            period_type: str = "Interval",
            pivot: PivotType = "auto",
    ) -> pl.DataFrame:
        if self._horizon_type != (phase, period_type):
            self._horizon_type = (phase, period_type)
            self._horizon = query_horizon(self._pointer, phase, period_type)
        # Get all _id
        period_type_id = get_period_type_id(period_type)
        phase_id = get_phase_id(phase)
        timeslice_id = query_timeslice_id(self._pointer, "All Periods")
        # Membership dic
        membership_ids = self._kernel.findall_membership_id(parent_class, parent, children_class, children)
        memberships = dict(zip(children, membership_ids))
        # Property dic
        properties_name_id = {}
        for property_name in properties:
            property_unit = query_property_unit(self._pointer, property_name, children_class, parent_class)
            property_id = query_property_id(self._pointer, property_name, children_class, parent_class)
            properties_name_id[f"{property_name} ({property_unit})"] = property_id
        # Partial query
        array = self._array if period_type == "Interval" else self._yearray
        prefilter = self._kernel.findall_key(
            phase_id=phase_id,
            period_type_id=period_type_id,
            band_id=band,
            timeslice_id=timeslice_id,
        )
        return self._process_extraction(array, prefilter, memberships, properties_name_id, samples, pivot)

    def extract(
            self,
            phase: str,
            children_class: str,
            children: list,
            properties: list,
            samples: list,
            parent_class: str = "System",
            parent: str = "System",
            band: str = '1',
            period_type: str = "Interval",
            pivot: PivotType = "auto",
    ) -> pl.DataFrame:

        period_type = _get_period_type(period_type)

        if self._is_closed and period_type == "Interval":
            raise Exception("DarkSol is closed. No more hourly extraction.")
        elif period_type == "Interval" and self._array is None:
            raise QueryError("No Interval data to extract!")
        elif period_type == "FiscalYear" and self._yearray is None:
            raise QueryError("No FiscalYear data to extract!")

        try:
            df = self._process_query(
                phase,
                children_class,
                children,
                properties,
                samples,
                parent_class,
                parent,
                band,
                period_type,
                pivot
            )
            return df
        except (KeyError, StopIteration, QueryError) as extract_error:
            # Check inputs are valid
            assert phase in self.query_phase(), f"No {phase} data to extract!"
            assert parent_class in self.query_class(), f"'{parent_class}' not found"
            assert parent in self.query_children(parent_class), f"{parent_class} '{parent}' not found"
            assert children_class in self.query_class(), f"'{children_class}' not found"
            existing_children = self.query_children(children_class)
            for child in children:
                assert child in existing_children, f"{children_class} '{child}' not found"
            existing_properties = self.query_property(children_class, parent_class)
            for prop in properties:
                assert prop in existing_properties, f"{parent_class} {children_class} has no property '{prop}'"
            existing_samples = self.query_sample()
            for sample in samples:
                assert sample in existing_samples, f"Sample {sample} not found"
            # If all inputs are valid
            if not isinstance(extract_error, QueryError):
                raise extract_error
            query_error = f"{extract_error} in {phase}".replace("data", f"{period_type} data")
            raise QueryError(query_error)

    def query(
            self,
            phase: str,
            children_class: str,
            children: list,
            properties: list,
            samples: list,
            parent_class: str = "System",
            parent: str = "System",
            period_type: str = "Interval",
            pivot: PivotType = "auto",
    ) -> pd.DataFrame:
        """
        Perform query and extract result in pandas DataFrame.

        Parameters
        ----------
        phase
            Phase to query.
        children_class
            Class of the children. Must be the same for all children.
        children
            List of children to query.
        properties
            List of properties to query.
        samples
            List of samples to query.
        parent_class
            Class of the parent. Default is "System".
        parent
            Parent object of children. Default is "System".
        period_type
            Which PeriodType to query. Default is "Interval".
            Other available PeriodType is "FiscalYear".

            .. versionadded:: 0.1.3
                period_type is not case sensitive anymore (see below).

                - "Interval" can be written "interval" or "i"
                - "FiscalYear" can be written "Fiscal Year", "fiscalyear", "Year", "yearly" or "y"
        pivot
            Determines the pivot strategy used.
            "Pivot strategy" refers to the pivot() DataFrame method;
            it determines which result values should be added as a new column instead of stacked as new rows.

            - "auto" (default): Automatically switch between "none" and "property" strategy,
              depending which one will save the most rows ("property" strategy is prioritised).
            - "none": Each new child is added as a new column.
            - "property": Each property is added as a new column.
            - "melt": Put all result values in a "Value" column so the DataFrame stacks results only vertically.

        Returns
        -------
        A pandas DataFrame with ["Name", "Sample", "Datetime", "Property", "Value"] informations.
        The properties are renamed as "Property (Unit)".

        Examples
        --------
        >>> from fairyex import DarkSol
        >>>
        >>> with DarkSol("Model Open World Solution.zip") as ds:
        >>>     ds.query(
        ...         phase="STSchedule",
        ...         children_class="Generator",
        ...         children=["Limgrave foo"],
        ...         properties=["Generation"],
        ...         samples=["0", "1"],
        ...         # pivot as "auto" will be same as "property"
        ...     )
                     Name  Sample             Datetime  Generation (MW)
        0    Limgrave foo      0  01/01/2025 00:00:00              0.0
        1    Limgrave foo      1  01/01/2025 00:00:00              0.0
        >>>
        >>>     ds.query(
        ...         phase="STSchedule",
        ...         children_class="Generator",
        ...         children=["Limgrave foo", "Limgrave bar"],
        ...         properties=["Generation"],
        ...         samples=["0", "1"],
        ...         # pivot as "auto" will be same as "none"
        ...     )
                   Property Sample             Datetime  Limgrave foo  Limgrave bar
        0   Generation (MW)      0  01/01/2025 00:00:00           0.0           0.0
        1   Generation (MW)      1  01/01/2025 01:00:00           0.0           0.0
        """
        try:
            df = self.extract(
                phase,
                children_class,
                children,
                properties,
                samples,
                parent_class,
                parent,
                '1',
                period_type,
                pivot
            )
            return df.to_pandas()
        except (AssertionError, QueryError) as msg:
            query_error = QueryError(msg)
            logging.error("Query failed")
        raise query_error
