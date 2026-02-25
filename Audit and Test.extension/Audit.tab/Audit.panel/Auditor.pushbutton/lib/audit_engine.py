import clr
clr.AddReference('System')
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, StorageType, TemporaryViewMode, ElementId


def collect_elements(doc, uidoc, scope, category_id):
    """Collect elements for the given category and scope."""
    if category_id is None:
        return []
    try:
        if scope == 'active_view':
            view = doc.ActiveView
            collector = FilteredElementCollector(doc, view.Id)
        else:
            collector = FilteredElementCollector(doc)
        elements = collector.OfCategoryId(category_id).WhereElementIsNotElementType().ToElements()
        return list(elements)
    except Exception:
        return []


def discover_parameter_names(doc, elements, sample_limit=200):
    """Return sorted unique parameter names from a sample set, preferring text parameters (instance + type)."""
    names = set()
    count = 0
    for elem in elements:
        try:
            for p in elem.Parameters:
                if p.StorageType == StorageType.String:
                    names.add(p.Definition.Name)
            # include type parameters
            type_id = None
            try:
                type_id = elem.GetTypeId()
            except Exception:
                type_id = None
            if type_id and type_id.IntegerValue > 0:
                t_elem = doc.GetElement(type_id)
                if t_elem:
                    for p in t_elem.Parameters:
                        if p.StorageType == StorageType.String:
                            names.add(p.Definition.Name)
            count += 1
            if count >= sample_limit:
                break
        except Exception:
            continue
    name_list = list(names)
    name_list.sort()
    return name_list


def get_param_text(doc, elem, param_name):
    """Lookup a parameter by name (instance or type) and return (exists, normalized_string_value)."""
    try:
        p = elem.LookupParameter(param_name)
    except Exception:
        p = None
    if p is None:
        try:
            type_id = elem.GetTypeId()
            if type_id and type_id.IntegerValue > 0:
                t_elem = doc.GetElement(type_id)
                if t_elem:
                    p = t_elem.LookupParameter(param_name)
        except Exception:
            p = None
    if p is None:
        return False, ""
    try:
        if p.StorageType == StorageType.String:
            v = p.AsString()
        else:
            v = p.AsValueString()
        if v is None:
            v = ""
        v = v.strip()
    except Exception:
        v = ""
    return True, v


def _get_family_and_type(elem, doc):
    fam = ""
    typ = ""
    try:
        # FamilyInstance has Symbol and Family
        sym = getattr(elem, "Symbol", None)
        if sym:
            try:
                fam_obj = sym.Family
                if fam_obj:
                    fam = fam_obj.Name or ""
            except Exception:
                pass
            try:
                typ = sym.Name or ""
            except Exception:
                pass
        else:
            # Non FamilyInstance
            try:
                type_id = elem.GetTypeId()
                if type_id and type_id.IntegerValue > 0:
                    type_elem = doc.GetElement(type_id)
                    if type_elem:
                        typ = type_elem.Name or ""
            except Exception:
                pass
    except Exception:
        pass
    return fam, typ


def audit(doc, elements, param_name, fail_missing=True, fail_empty=True):
    """Audit parameter existence and emptiness on provided elements."""
    results = []
    if not param_name:
        return results
    for elem in elements:
        try:
            exists, value = get_param_text(doc, elem, param_name)
            fail_reason = None
            if (not exists) and fail_missing:
                fail_reason = "Missing"
            elif fail_empty and value == "":
                fail_reason = "Empty"

            # Only capture failures
            if fail_reason:
                cat_name = ""
                try:
                    cat = elem.Category
                    if cat:
                        cat_name = cat.Name or ""
                except Exception:
                    pass
                fam_name, type_name = _get_family_and_type(elem, doc)
                row = {
                    "Element": elem,
                    "ElementIdObj": elem.Id,
                    "ElementId": elem.Id.IntegerValue,
                    "Category": cat_name,
                    "Family": fam_name,
                    "Type": type_name,
                    "CurrentValue": value,
                    "FailReason": fail_reason,
                }
                results.append(row)
        except Exception:
            continue
    return results


def select_elements(uidoc, element_ids):
    """Select elements in the UI document."""
    if not element_ids:
        return
    try:
        id_list = List[ElementId]()
        for eid in element_ids:
            id_list.Add(eid)
        uidoc.Selection.SetElementIds(id_list)
    except Exception:
        pass


def show_element(uidoc, element_id):
    """Show and select an element."""
    if element_id is None:
        return
    try:
        uidoc.ShowElements(element_id)
        id_list = List[ElementId]()
        id_list.Add(element_id)
        uidoc.Selection.SetElementIds(id_list)
    except Exception:
        pass


def temp_isolate(doc, view, element_ids):
    """Temporarily isolate the provided element ids in the active view."""
    if view is None or doc is None:
        return
    if not element_ids:
        return
    try:
        active_flag = False
        try:
            active_flag = bool(view.IsTemporaryHideIsolateActive)
        except Exception:
            try:
                active_flag = bool(view.IsTemporaryHideIsolateActive())
            except Exception:
                active_flag = False
        if active_flag:
            view.DisableTemporaryViewMode(TemporaryViewMode.TemporaryHideIsolate)
    except Exception:
        pass
    try:
        id_list = List[ElementId]()
        for eid in element_ids:
            id_list.Add(eid)
        view.IsolateElementsTemporary(id_list)
    except Exception:
        pass
