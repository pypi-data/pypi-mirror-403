"""
Plugin callbacks to register and handle the markers.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

import pytest

_AC_REF_REGEX = re.compile(r"__ac(?P<story_id>\d+)_(?P<criterion_id>\d+)")


@dataclass(frozen=True, slots=True, order=True)
class ACMarker:
    """Represents a single ac marker instance."""

    story_id: int
    criterion_id: int
    ref_prefix: str = "ac"
    ref_suffix: str = ""

    @staticmethod
    def from_mark(mark: pytest.Mark) -> "ACMarker":
        """
        Constructs an ACMarker from a pytest.Mark instance.

        :param mark: The pytest.Mark instance to parse.
        :type mark: pytest.Mark
        :raises pytest.UsageError: If the mark is malformed.
        :return: The constructed ACMarker.
        :rtype: ACMarker
        """
        if "story_id" in mark.kwargs:
            story_id = mark.kwargs["story_id"]
            if "criterion_id" not in mark.kwargs:
                raise pytest.UsageError(
                    "@pytest.mark.ac requires both story_id and criterion_id as keyword arguments "
                    "if the story_id is provided as a keyword argument"
                )
            criterion_id = mark.kwargs["criterion_id"]
        else:
            if len(mark.args) < 1:
                raise pytest.UsageError(
                    "@pytest.mark.ac requires at least a story_id as positional argument"
                )
            story_id = mark.args[0]
            if "criterion_id" in mark.kwargs:
                criterion_id = mark.kwargs["criterion_id"]
            elif len(mark.args) == 2:
                criterion_id = mark.args[1]
            else:
                raise pytest.UsageError(
                    "@pytest.mark.ac requires a criterion_id either as positional or keyword "
                    "argument"
                )
        if not isinstance(story_id, int):
            raise pytest.UsageError(f"ac: story_id must be int, got {type(story_id).__name__}")
        if not isinstance(criterion_id, int):
            raise pytest.UsageError(
                f"ac: criteria_id must be int, got {type(criterion_id).__name__}"
            )
        ref_prefix: str = str(mark.kwargs.get("ref_prefix", "ac"))
        ref_suffix: str = str(mark.kwargs.get("ref_suffix", ""))
        return ACMarker(
            story_id=story_id,
            criterion_id=criterion_id,
            ref_prefix=ref_prefix,
            ref_suffix=ref_suffix,
        )

    @staticmethod
    def get_inivalue_line() -> str:
        """
        Provides the inivalue line for pytest marker registration.

        :return: The inivalue line string.
        :rtype: str
        """
        return (
            "ac(story_id: int, criterion_id: int, "
            'ref_prefix: str = "ac", ref_suffix: str = ""): '
            "appends a suffix in the form __<ref_prefix><story_id>_<criterion_id><ref_suffix> "
            "to the test nodeid"
        )

    def to_test_nodeid_suffix(self) -> str:
        """
        Generates the test nodeid suffix for this ACMarker.

        :return: The test nodeid suffix string.
        :rtype: str
        """
        return f"__{self.ref_prefix}{self.story_id}_{self.criterion_id}{self.ref_suffix}"

    def add_keywords(self, item: pytest.Item) -> None:
        """
        Adds keywords to the pytest item for this ACMarker.

        :param item: The pytest item to which keywords will be added.
        :type item: pytest.Item
        """
        item.keywords[f"{self.ref_prefix}{self.story_id}_"] = True
        item.keywords[f"{self.ref_prefix}{self.story_id}_{self.criterion_id}{self.ref_suffix}"] = (
            True
        )

    def __hash__(self) -> int:
        return hash((self.story_id, self.criterion_id, self.ref_prefix, self.ref_suffix))


@dataclass(frozen=True, slots=True)
class ACsMarker:
    """Represents a marker instance with multiple criteria."""

    story_id: int
    criteria_ids: list[int]
    ref_prefix: str = "ac"
    ref_suffix: str = ""

    @staticmethod
    def from_mark(mark: pytest.Mark) -> "ACsMarker":
        """
        Constructs an ACsMarker from a pytest.Mark instance.

        :param mark: The pytest.Mark instance to parse.
        :type mark: pytest.Mark
        :raises pytest.UsageError: If the mark is malformed.
        :return: The constructed ACsMarker.
        :rtype: ACsMarker
        """
        if len(mark.args) != 2:
            raise pytest.UsageError(
                "@pytest.mark.acs requires 2 positional arguments: "
                "(story_id:int, criteria_ids:Sequence[int])"
            )
        story_id, criteria_ids = mark.args
        if not isinstance(story_id, int):
            raise pytest.UsageError(f"acs: story_id must be int, got {type(story_id).__name__}")
        if isinstance(criteria_ids, (str, bytes)) or not isinstance(criteria_ids, Sequence):
            raise pytest.UsageError("acs: criteria_ids must be an int sequence")
        ref_prefix: str = str(mark.kwargs.get("ref_prefix", "ac"))
        ref_suffix: str = str(mark.kwargs.get("ref_suffix", ""))
        cids: list[int] = []
        for idx, cid in enumerate(criteria_ids):
            if not isinstance(cid, int):
                raise pytest.UsageError(
                    f"acs: each criterion must be int; got {type(cid).__name__} at position {idx}"
                )
            cids.append(cid)
        return ACsMarker(
            story_id=story_id,
            criteria_ids=cids,
            ref_prefix=ref_prefix,
            ref_suffix=ref_suffix,
        )

    def to_ac_markers(self) -> list[ACMarker]:
        """
        Converts this ACsMarker into a list of ACMarker instances.

        :return: The list of ACMarker instances.
        :rtype: list[ACMarker]
        """
        return [
            ACMarker(
                story_id=self.story_id,
                criterion_id=cid,
                ref_prefix=self.ref_prefix,
                ref_suffix=self.ref_suffix,
            )
            for cid in self.criteria_ids
        ]

    @staticmethod
    def get_inivalue_line() -> str:
        """
        Provides the inivalue line for pytest marker registration.

        :return: The inivalue line string.
        :rtype: str
        """
        return (
            "acs(story_id: int, criteria_ids: Sequence[int], "
            'ref_prefix: str = "ac", ref_suffix: str = ""): '
            "convenience marker that appends several suffixes in the form "
            "__<ref_prefix><story_id>_<criterion_id><ref_suffix> "
            "to the test nodeid, one for each criterion_id in criteria_ids"
        )


def pytest_configure(config: pytest.Config) -> None:
    """
    Register the custom markers with pytest.
    """
    config.addinivalue_line("markers", ACMarker.get_inivalue_line())
    config.addinivalue_line("markers", ACsMarker.get_inivalue_line())


def _add_implicit_marks(items: list[pytest.Item]) -> None:
    for item in items:
        if "__ac" in item.nodeid:
            ac_refs = _AC_REF_REGEX.findall(item.nodeid)
            for story_id_str, criterion_id_str in ac_refs:
                story_id = int(story_id_str)
                criterion_id = int(criterion_id_str)
                item.add_marker(
                    pytest.mark.ac(
                        story_id=story_id,
                        criterion_id=criterion_id,
                    )
                )


def pytest_collection_modifyitems(
    session: pytest.Session,  # pylint: disable=unused-argument
    config: pytest.Config,  # pylint: disable=unused-argument
    items: list[pytest.Item],
) -> None:
    """
    Modifies collected test items to add AC markers based on acs/ac marks
    and implicit markings in the test nodeid.
    """
    _add_implicit_marks(items)
    for item in items:
        ac_ref_marks: set[ACMarker] = set()
        for acs_mark in item.iter_markers("acs"):
            ac_markers = ACsMarker.from_mark(acs_mark)
            ac_ref_marks.update(ac_markers.to_ac_markers())
        for ac_mark in item.iter_markers("ac"):
            ac_ref_mark = ACMarker.from_mark(ac_mark)
            ac_ref_marks.add(ac_ref_mark)

        for ac_ref_mark in sorted(ac_ref_marks):
            item.add_marker(
                pytest.mark.ac(
                    story_id=ac_ref_mark.story_id,
                    criterion_id=ac_ref_mark.criterion_id,
                    ref_prefix=ac_ref_mark.ref_prefix,
                    ref_suffix=ac_ref_mark.ref_suffix,
                )
            )
            ac_ref_mark.add_keywords(item)

        suffixes: set[str] = set(
            ac_ref_mark.to_test_nodeid_suffix() for ac_ref_mark in ac_ref_marks
        )
        suffixes = {s for s in suffixes if s not in item.nodeid}
        if suffixes:
            item._nodeid = (  # pylint: disable=protected-access
                item.nodeid + "".join(sorted(suffixes))
            )
