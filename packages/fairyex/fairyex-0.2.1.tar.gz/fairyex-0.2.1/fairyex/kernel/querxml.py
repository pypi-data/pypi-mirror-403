"""QUERy on the XML file"""

from xml.etree import ElementTree


FLOAT_SIZE = 8


def _set_query(xml, query: str):
    root = xml.getroot()
    default_namespace = root.tag[:-len("SolutionDataset")]
    return f"{default_namespace}{query}"


def _query(xml, element: str, kwargs: dict):
    leaves = xml.findall(_set_query(xml, f"t_{element}"))
    for leaf in leaves:
        if all(
            leaf.find(_set_query(xml, filter_key)).text == filter_id
            for filter_key, filter_id in kwargs.items()
        ) or not kwargs:
            yield leaf


def get_all(xml: ElementTree, element: str, query: str, kwargs: dict):
    for leaf in _query(xml, element, kwargs):
        leaf_attr = leaf.find(_set_query(xml, query)).text
        yield leaf_attr


def _get_id(xml: ElementTree, element: str, **kwargs):
    for leaf in _query(xml, element, kwargs):
        id_found = leaf.find(_set_query(xml, f"{element}_id")).text
        return id_found


def _get_from_key_id(xml, element: str, key_name: str, key_id: str):
    leaves = xml.findall(_set_query(xml, f"t_{element}"))
    for leaf in leaves:
        if leaf.find(_set_query(xml, f"{key_name}_id")).text == key_id:
            return leaf


def get_key_index(xml: ElementTree, **kwargs):
    key_id = _get_id(xml, "key", **kwargs)
    leaf = _get_from_key_id(xml, "key_index", "key", key_id)
    position = leaf.find(_set_query(xml, "position")).text
    length = leaf.find(_set_query(xml, "length")).text
    return int(position) // FLOAT_SIZE, int(length)
