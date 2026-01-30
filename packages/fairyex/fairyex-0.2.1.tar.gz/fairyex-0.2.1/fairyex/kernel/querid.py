"""QUERy based on ID """

from .querxml import  _get_id


def get_system_id():
    return '1'


def get_category_id(xml, category_name, category_class_id):
    return _get_id(xml, "category", name=category_name, class_id=category_class_id)


def get_class_id(xml, class_name):
    return _get_id(xml, "class", name=class_name)


def get_collection_id(xml, child_class_id, parent_class_id):
    return _get_id(
        xml, "collection", child_class_id=child_class_id, parent_class_id=parent_class_id
    )


def get_membership_id(
    xml,
    parent_id,
    parent_class_id,
    child_id,
    child_class_id,
):
    return _get_id(
        xml,
        "membership",
        parent_object_id=parent_id,
        parent_class_id=parent_class_id,
        child_object_id=child_id,
        child_class_id=child_class_id,
    )


def get_model_name(xml, model_id):
    return _get_id(xml, "model", model_id=model_id)


def get_model_id(xml, model_name):
    return _get_id(xml, "model", name=model_name)


def get_object_id(xml, object_name, class_id):
   return _get_id(
        xml, "object", name=object_name, class_id=class_id
    )


def get_property_id(xml, property_name, collection_id):
    return _get_id(
        xml, "property", name=property_name, collection_id=collection_id
    )


def get_timeslice_id(xml, timeslice_name):
    return _get_id(xml, "timeslice", name=timeslice_name)
