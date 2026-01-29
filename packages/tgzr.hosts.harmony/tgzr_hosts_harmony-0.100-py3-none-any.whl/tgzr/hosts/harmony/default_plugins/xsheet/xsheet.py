"""

XSheet

Usage:
    from tgzr.hosts.harmony.default_plugin.xsheet import xsheet

    # Create an XSheet and populate it:
    xsheet = xsheet.XSheet(
        name='BestXSheetEver',
        first=0,
        last=100,
        elements=['Alice', 'Bob', 'Carol],
    )
    xrow = xsheet.add_row():
    xrow.set_element('Alice', 1)
    xrow.set_element('Carol', 2)
    ...

    # Get XSheet from the current scene:
    xsheet = xsheet.get_xsheet()

    # Save xsheet to csv:
    xsheet.save_csv(filename)

Notes:
    - If an element in the scene is named "Frame", it's armageddon.
"""

from __future__ import annotations

from typing import TypeVar
import os
from pathlib import Path
import csv
from io import StringIO
import logging

from ToonBoom import harmony  # type: ignore import from harmony

T = TypeVar("T")

KeyType = TypeVar("KeyType", bound=int)
FrameType = TypeVar("FrameType", bound=int)

logger = logging.getLogger(__name__)


class XRow:
    def __init__(self, xsheet: XSheet):
        self._xsheet = xsheet
        self._element_keys: dict[str, KeyType] = dict()

    def set_key(self, element: str, key: KeyType) -> None:
        if element not in self._xsheet.elements():
            raise ValueError(f"Unknown XSheet element {element!r}")
        self._element_keys[element] = key

    def get_element(self, element: str) -> KeyType | None:
        if element not in self._xsheet.elements():
            raise ValueError(f"Unknown XSheet element {element!r}")
        return self._element_keys.get(element)

    def frame(self) -> KeyType:
        return self._xsheet.frame_for_row(self)

    def to_dict(self) -> dict[str, KeyType]:
        d = dict(self._element_keys)  # copy!
        d["Frame"] = self.frame()
        return d


class XSheet:
    @classmethod
    def get_ordered_element_names(cls, scene) -> list[str]:
        composites = [n for n in scene.top.nodes if n.type == "COMPOSITE"]

        if not composites:
            return []
        if len(composites) > 1:
            raise ValueError("More than on Composite found in scene.Top :/")
        composite = composites[0]

        element_names = []
        for i in range(len(composite.ports_in)):
            node = composite.ports_in[i].source_node
            # print(node.name, type(node))
            element_names.append(node.name)

        return reversed(element_names)

    @classmethod
    def from_scene(cls: T) -> T:
        current_session = harmony.session()
        project = current_session.project
        scene = project.scene  # The primary scene in the project

        element_names = cls.get_ordered_element_names(scene)

        element_columns = {}
        for column in scene.columns:
            if column.type == "DRAWING":
                element_columns[column.element.name] = column

        first = 1  # FIXME: this should come from reading the scene info, I guess...
        last = scene.frame_count

        xsheet = cls(
            name=Path(project.project_path).stem,
            first=first,
            last=last,
            elements=element_names,
        )
        for i in range(scene.frame_count):
            frame = i + 1
            xrow = xsheet.add_row()
            keys = {}
            for element_name, column in element_columns.items():
                value = column.get_entry(frame)
                keys[element_name] = value
            for element_name, column in keys.items():
                xrow.set_key(element_name, keys[element_name])

        return xsheet

    def __init__(
        self, name: str, first: FrameType, last: FrameType, elements: list[str]
    ):
        super().__init__()
        self._name = name
        self._first = first
        self._last = last
        self._elements: tuple[str] = tuple(elements)  # copy to avoid inplace edit
        self._rows: list[XRow] = []

    def name(self) -> str:
        return self._name

    def first(self) -> FrameType:
        return self._first

    def last(self) -> FrameType:
        return self._last

    def elements(self) -> tuple[str]:
        return self._elements

    def rows(self) -> tuple[XRow]:
        return tuple(self._rows)

    def add_row(self) -> XRow:
        row = XRow(self)
        self._rows.append(row)
        return row

    def frame_for_row(self, xrow: XRow) -> FrameType:
        # TODO: this could be cached and invalidate by `add_row()`
        try:
            index = self._rows.index(xrow)
        except IndexError:
            raise ValueError("This row doesn't belong to this sheet!")
        return index + self.first()

    def save_csv(
        self, filename: str, overwrite: bool = False, prune_duplicate_keys: bool = True
    ) -> None:
        if os.path.exists(filename):
            if not os.path.isfile(filename):
                raise ValueError(
                    f"The path {filename} is not a file, cannot save xsheet."
                )
            if not overwrite:
                raise Exception(
                    f"The path {filename} already exists, use `overwrite=True` to overwrite."
                )
        with open(filename, "w") as fp:
            self._write_csv(fp, prune_duplicate_keys)
        logger.info("XSheet saved as CSV file {filename!r}")

    def rows_without_duplicate_keys(self) -> list[dict[str, KeyType]]:
        # TODO: maybe we should return a whole new XSheet?
        rows = []
        prev_keys = {}
        for xrow in self._rows:
            row = xrow.to_dict()
            rows.append(row)
            for k, v in tuple(row.items()):
                if prev_keys.get(k) == v:
                    del row[k]
            prev_keys = xrow.to_dict()
        return rows

    def csv_string(self, prune_duplicate_keys: bool = True) -> str:
        csv_content = StringIO()
        self._write_csv(csv_content, prune_duplicate_keys)
        return csv_content.getvalue()

    def _write_csv(self, fp, prune_duplicate_keys: bool):
        field_names = ("Frame",) + self.elements()

        if prune_duplicate_keys:
            rows = self.rows_without_duplicate_keys()
        else:
            rows = [row.to_dict() for row in self._rows]

        fp.write(f"{self._name}, {self._first}, {self._last}\n")
        writer = csv.DictWriter(
            fp,
            fieldnames=field_names,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def get_xsheet():
    return XSheet.from_scene()
