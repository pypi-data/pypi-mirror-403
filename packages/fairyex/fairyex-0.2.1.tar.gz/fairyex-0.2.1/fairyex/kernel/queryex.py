"""QUERy for EXtraction"""

from xml.etree import ElementTree

from .querxml import FLOAT_SIZE, _set_query, _get_from_key_id


class MastersEx:
    def __init__(self, xml: ElementTree):
        self.xml = xml
        self.default_namespace = _set_query(self.xml, '')
        self._objects = self.findall("object")
        self._children = {
            self.findattr(object, "object_id"): self.findattr(object, "name")
            for object in self._objects
        }
        self._memberships = self.findall("membership")
        self._keys = self.findall("key")
        self._key_index = {
            self.findattr(key_index, "key_id"): (
                self.findattr(key_index, "position"),
                self.findattr(key_index, "length")
            ) for key_index in self.findall("key_index")
        }

    def find(self, query):
        return self.xml.find(f"{self.default_namespace}t_{query}")

    def findall(self, query):
        return self.xml.findall(f"{self.default_namespace}t_{query}")

    def findattr(self, leaf, attr):
        try:
            return leaf.find(f"{self.default_namespace}{attr}").text
        except AttributeError:
            raise AttributeError(f"{leaf} object has no attribute {attr}")

    def _find_id(self, attr, **kwargs):
        if hasattr(self, f"_{attr}s"):
            leaves = getattr(self, f"_{attr}s")
        else:
            leaves = self.findall(attr)
        for leaf in leaves:
            if all(
                self.findattr(leaf, filter_key) == filter_id
                for filter_key, filter_id in kwargs.items()
            ):
                return self.findattr(leaf, f"{attr}_id")

    def find_class_id(self, class_name: str):
        return self._find_id("class", name=class_name)

    def find_collection_id(self, collection_name: str):
        return self._find_id("collection", name=collection_name)

    def find_membership_id(self, parent_class_id, parent_id, child_class_id, child_id):
        return self._find_id(
            "membership",
            parent_object_id=parent_id,
            parent_class_id=parent_class_id,
            child_object_id=child_id,
            child_class_id=child_class_id,
        )

    def find_object_id(self, object_name, object_class_id):
        return self._find_id("object", name=object_name, class_id=object_class_id)

    def findall_membership_id(
        self,
        parent_class,
        parent,
        child_class,
        children,
    ):
        parent_class_id = self.find_class_id(parent_class)
        parent_id = self.find_object_id(parent, parent_class_id)
        child_class_id = self.find_class_id(child_class)
        for child in children:
            child_id = self.find_object_id(child, child_class_id)
            yield self.find_membership_id(parent_class_id, parent_id, child_class_id, child_id)

    def findall_key(self, **kwargs):
        # keys = []
        keys = {}
        for key in self._keys:
            if all(
                self.findattr(key, filter_key) == filter_id
                for filter_key, filter_id in kwargs.items()
            ) or not kwargs:
                prop_id = self.findattr(key, f"property_id")
                memb_id = self.findattr(key, f"membership_id")
                sample_id = self.findattr(key, f"sample_id")
                key_id = self.findattr(key, f"key_id")
                keys[(prop_id, memb_id, sample_id)] = key_id
                # keys.append(key)
        return keys

    def _find_key_id(self, kwargs, prefilter=None):
        key_ids = self._keys if prefilter is None else prefilter
        for key_id in key_ids:
            if all(
                self.findattr(key_id, filter_key) == filter_id
                for filter_key, filter_id in kwargs.items()
            ) or not kwargs:
                id_found = self.findattr(key_id, f"key_id")
                return id_found

    def find_key_index(self, prefilter, property_id, membership_id, sample_id):
        # key_id = self._find_key_id(kwargs, prefilter)
        key_id = prefilter[property_id, membership_id, sample_id]
        position, length = self._key_index[key_id]
        return int(position) // FLOAT_SIZE, int(length)


    def filter_children_from_parent(self, parent_class, parent, children_class, children):
        parent_class_id = self.find_class_id(parent_class)
        parent_id = self.find_object_id(parent, parent_class_id)
        children_class_id = self.find_class_id(children_class)
        for membership in self._memberships:
            membership_child_name = self._children[self.findattr(membership, "child_object_id")]
            if (
                self.findattr(membership, "parent_class_id") == parent_class_id
                and self.findattr(membership, "parent_object_id") == parent_id
                and self.findattr(membership, "child_class_id") == children_class_id
                and membership_child_name in children
            ):
                yield membership_child_name
