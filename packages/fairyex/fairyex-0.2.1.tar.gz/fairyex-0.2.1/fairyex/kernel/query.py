from .querxml import (
    get_all, get_key_index, _query, _set_query
)
from .querid import (
    get_category_id, get_class_id, get_collection_id,
    get_membership_id, get_model_name, get_model_id, get_object_id,
    get_property_id, get_system_id, get_timeslice_id,
)


_PHASES = {
    # "Preview": '0',
    "LTPlan": '1',
    "PASA": '2',
    "MTSchedule": '3',
    "STSchedule": '4',
}


def query_horizon(xml, phase, period_type):
    if period_type == "Interval":
        return get_datetime(xml, phase)
    return list(get_fiscal_year(xml))


def get_fiscal_year(xml):
    return get_all(xml, "period_4", "year_ending", {})


def get_datetime(xml, phase):
    interval = {
        dt.find(_set_query(xml, "interval_id")).text: dt.find(_set_query(xml, "datetime")).text
        for dt in _query(xml, "period_0", {})
    }
    horizon = [interval[interval_id] for interval_id in _get_datetime(xml, phase)]
    return horizon


def _get_datetime(xml, phase):
    period_counter = {}
    phase_id = get_phase_id(phase)
    for period in _query(xml, f"phase_{phase_id}", {}):
        period_id = int(period.find(_set_query(xml, "period_id")).text)
        interval_id = int(period.find(_set_query(xml, "interval_id")).text)
        if current_interval_id := period_counter.get(period_id):
            period_counter[period_id] = min(current_interval_id, interval_id)
        else:
            period_counter[period_id] = interval_id
    for period_id in sorted(period_counter.keys()):
        yield str(period_counter[period_id])


def query_key_index(
        xml,
        parent,
        parent_class,
        child,
        child_class,
        model,
        phase,
        property_name,
        property_collection,
        period_type,
        band,
        sample,
        timeslice
):
    return get_key_index(
        xml,
        membership_id=query_membership_id(
            xml, parent_class, parent, child_class, child
        ),
        model_id=query_model_id(xml, model),
        phase_id=get_phase_id(phase),
        property_id=query_property_id(xml, property_name, property_collection),
        period_type_id=get_period_type_id(period_type),
        band_id=band,
        sample_id=sample,
        timeslice_id=query_timeslice_id(xml, timeslice),
    )


def query_collection_id(xml, child_class, parent_class):
    property_child_class_id = get_class_id(xml, child_class)
    property_parent_class_id = get_class_id(xml, parent_class)
    return get_collection_id(xml, property_child_class_id, property_parent_class_id)


def query_membership_id(
    xml,
    parent_class,
    parent,
    child_class,
    child,
):
    parent_class_id = get_class_id(xml, parent_class)
    parent_id = get_object_id(xml, parent, parent_class_id)
    child_class_id = get_class_id(xml, child_class)
    child_id = get_object_id(xml, child, child_class_id)
    return get_membership_id(
        xml, parent_id, parent_class_id, child_id, child_class_id,
    )


def query_model_name(xml, model_id='1'):
    return next(get_all(xml, "model", "name", {"model_id": model_id}))


def query_model_id(xml, model_name):
    return '1'


def get_phase_id(phase: str):
    return _PHASES[phase]


def get_period_id(period: str):
    return {"FiscalYear": '4', "Interval": '0'}[period]


def get_period_type_id(period_type: str):
    return {"FiscalYear": '1', "Interval": '0'}[period_type]


def query_property_id(xml, property_name, property_child_class, property_parent_class="System"):
    collection_id = query_collection_id(xml, property_child_class, property_parent_class)
    return get_property_id(xml, property_name, collection_id)


def query_property_unit(xml, property_name, property_child_class, property_parent_class="System"):
    property_child_class_id = get_class_id(xml, property_child_class)
    property_parent_class_id = get_class_id(xml, property_parent_class)
    collection_id = get_collection_id(xml, property_child_class_id, property_parent_class_id)
    property_filter = {"name": property_name, "collection_id": collection_id}
    unit_id = next(
        get_all(xml, "property", "unit_id", property_filter)
    )
    unit_value = next(
        get_all(xml, "unit", "value", {"unit_id": unit_id})
    )
    return unit_value


def query_timeslice_id(xml, timeslice_name):
    return get_timeslice_id(xml, timeslice_name)


def query_categories(xml, category_class):
    class_id = get_class_id(xml, category_class)
    return get_all(xml, "category", "name", {"class_id": class_id})


def query_classes(xml):
    return get_all(xml, "class", "name", {})


def query_children(xml, child_class, category=None):
    child_class_id = get_class_id(xml, child_class)
    children_filter = {"class_id": child_class_id}
    if category is not None:
        category_id = get_category_id(xml, category, child_class_id)
        children_filter |= {"category_id": category_id}
    return get_all(xml, "object", "name", children_filter)


def query_phases(xml):
    for phase_name, phase_id in _PHASES.items():
        if xml.find(_set_query(xml, f"t_phase_{phase_id}")):
            yield phase_name


def query_properties(xml, child_class, parent_class):
    collection_id = query_collection_id(xml, child_class, parent_class)
    return get_all(xml, "property", "name", {"collection_id": collection_id})


def query_samples(xml):
    return get_all(xml, "sample", "sample_id", {})


def query_samples_name(xml):
    return get_all(xml, "sample", "sample_name", {})
