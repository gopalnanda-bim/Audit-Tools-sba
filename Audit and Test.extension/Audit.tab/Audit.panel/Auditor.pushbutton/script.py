# Category Parameter Auditor (pyRevit 2022 / IronPython 2.7)
# README:
# - Place this folder `CategoryParameterAuditor.pushbutton` inside a pyRevit extension (e.g. %APPDATA%\\pyRevit\\Extensions\\YourExtension\\YourExtension.extension).
# - Ensure `script.py`, `ui.xaml`, and `lib/` stay together.
# - Launch from pyRevit: Add-Ins > pyRevit > Category Parameter Auditor button.
# - Supports Active View (default) or Whole Model scopes. Text parameters only.

import os
import sys
import csv
import clr
import System

clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
clr.AddReference('System')
clr.AddReference('System.Xaml')
from System.Windows import RoutedEventHandler
from System.Windows.Markup import XamlReader
from System.IO import FileStream, FileMode, FileAccess
from System.Windows.Controls import TextChangedEventHandler, SelectionChangedEventHandler
from System.Windows.Input import MouseButtonEventHandler

clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
_ui_instance = None

SCRIPT_DIR = os.path.dirname(__file__)
LIB_DIR = os.path.join(SCRIPT_DIR, 'lib')
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

import audit_engine as ae


class CategoryWrapper(object):
    def __init__(self, category):
        self.category = category
        try:
            self.Name = category.Name
        except Exception:
            self.Name = "Unknown"

    def __str__(self):
        return self.Name


class MainWindow(object):
    def __init__(self):
        xaml_path = os.path.join(SCRIPT_DIR, 'ui.xaml')
        fs = FileStream(xaml_path, FileMode.Open, FileAccess.Read)
        self.window = XamlReader.Load(fs)
        fs.Close()

        # bind doc/uidoc into instance to avoid global lookup issues
        self.doc = __revit__.ActiveUIDocument.Document
        self.uidoc = __revit__.ActiveUIDocument
        self.loaded_elements = []
        self.filtered_elements = []
        self.all_param_names = []
        self.results = []
        self.family_type_map = {}
        self.family_list = []

        self._bind_controls()
        self._wire_events()
        self._populate_categories()
        self._update_status("Ready")

    def _ensure_engine(self):
        """Guard against stale import issues inside pyRevit."""
        global ae
        try:
            # touch attribute to ensure it exists
            _ = ae.collect_elements
        except Exception:
            try:
                import audit_engine as ae  # re-import
                # refresh globals for safety
                globals()['ae'] = ae
            except Exception:
                pass

    def _bind_controls(self):
        # Grab named controls from XAML
        n = self.window.FindName
        self.ActiveViewRadio = n("ActiveViewRadio")
        self.WholeModelRadio = n("WholeModelRadio")
        self.CategoryCombo = n("CategoryCombo")
        self.CategorySearchBox = n("CategorySearchBox")
        self.LoadElementsButton = n("LoadElementsButton")
        self.RefreshButton = n("RefreshButton")
        self.StatusText = n("StatusText")
        self.SearchBox = n("SearchBox")
        self.ParameterList = n("ParameterList")
        self.FailMissingCheck = n("FailMissingCheck")
        self.FailEmptyCheck = n("FailEmptyCheck")
        self.AuditButton = n("AuditButton")
        self.FamilyFilterCombo = n("FamilyFilterCombo")
        self.TypeFilterCombo = n("TypeFilterCombo")
        self.ResultsGrid = n("ResultsGrid")
        self.SelectAllButton = n("SelectAllButton")
        self.IsolateButton = n("IsolateButton")
        self.ExportButton = n("ExportButton")
        self.ClearButton = n("ClearButton")

    # ---------------- UI Wiring ----------------
    def _wire_events(self):
        self.LoadElementsButton.Click += RoutedEventHandler(self.load_elements)
        self.RefreshButton.Click += RoutedEventHandler(self.load_elements)
        self.AuditButton.Click += RoutedEventHandler(self.run_audit)
        self.SearchBox.TextChanged += TextChangedEventHandler(self._filter_params)
        self.ParameterList.MouseDoubleClick += MouseButtonEventHandler(self.run_audit)
        self.CategorySearchBox.TextChanged += TextChangedEventHandler(self._filter_categories)
        self.FamilyFilterCombo.SelectionChanged += SelectionChangedEventHandler(self.on_filter_changed)
        self.TypeFilterCombo.SelectionChanged += SelectionChangedEventHandler(self.on_filter_changed)
        self.SelectAllButton.Click += RoutedEventHandler(self.select_all_failures)
        self.IsolateButton.Click += RoutedEventHandler(self.isolate_failures)
        self.ClearButton.Click += RoutedEventHandler(self.clear_results)
        self.ExportButton.Click += RoutedEventHandler(self.export_csv)
        self.ResultsGrid.SelectionChanged += SelectionChangedEventHandler(self.on_result_selected)

    # ---------------- Helpers ----------------
    def _update_status(self, msg):
        try:
            self.StatusText.Text = msg
        except Exception:
            pass

    def _get_scope(self):
        if self.WholeModelRadio.IsChecked:
            return 'whole_model'
        return 'active_view'

    def _populate_categories(self):
        cats = []
        try:
            for cat in self.doc.Settings.Categories:
                if cat is None or cat.Id is None:
                    continue
                try:
                    name = cat.Name
                except Exception:
                    name = ""
                if not name:
                    continue
                cats.append(cat)
        except Exception:
            pass
        cats = sorted(cats, key=lambda c: c.Name)
        wrappers = [CategoryWrapper(c) for c in cats]
        self.all_categories = wrappers
        self._filter_categories()

    def _filter_categories(self, sender=None, args=None):
        query = ""
        try:
            query = self.CategorySearchBox.Text or ""
        except Exception:
            query = ""
        query = query.strip().lower()
        filtered = []
        for w in getattr(self, "all_categories", []):
            try:
                name = w.Name.lower()
            except Exception:
                name = ""
            if query == "" or query in name:
                filtered.append(w)
        self.CategoryCombo.ItemsSource = filtered
        if filtered:
            # keep existing selection if still present
            current = self._get_selected_category()
            if current and any((w.category.Id == current.Id) for w in filtered):
                try:
                    self.CategoryCombo.SelectedItem = [w for w in filtered if w.category.Id == current.Id][0]
                except Exception:
                    self.CategoryCombo.SelectedIndex = 0
            else:
                self.CategoryCombo.SelectedIndex = 0

    def _get_selected_category(self):
        wrapper = self.CategoryCombo.SelectedItem
        if wrapper and hasattr(wrapper, "category"):
            return wrapper.category
        return None

    def _filter_params(self, sender=None, args=None):
        query = self.SearchBox.Text or ""
        query = query.strip().lower()
        if query == "":
            filtered = self.all_param_names
        else:
            filtered = [p for p in self.all_param_names if query in p.lower()]
        self.ParameterList.ItemsSource = filtered
        if filtered:
            self.ParameterList.SelectedIndex = 0

    def _extract_family_and_type(self, elem):
        fam = ""
        typ = ""
        try:
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
                try:
                    type_id = elem.GetTypeId()
                    if type_id and type_id.IntegerValue > 0:
                        t_elem = self.doc.GetElement(type_id)
                        if t_elem:
                            typ = t_elem.Name or ""
                except Exception:
                    pass
        except Exception:
            pass
        return fam, typ

    def _build_family_type_filters(self, elements):
        fam_map = {}
        for el in elements:
            fam, typ = self._extract_family_and_type(el)
            if fam not in fam_map:
                fam_map[fam] = set()
            if typ:
                fam_map[fam].add(typ)
        fam_names = list(fam_map.keys())
        fam_names.sort()
        fam_names.insert(0, "<All Families>")
        self.family_type_map = fam_map
        self.family_list = fam_names
        self.FamilyFilterCombo.ItemsSource = fam_names
        if fam_names:
            self.FamilyFilterCombo.SelectedIndex = 0
        self._populate_type_filter()

    def _populate_type_filter(self):
        selected_fam = self._get_selected_family()
        type_list = ["<All Types>"]
        if selected_fam and selected_fam != "<All Families>":
            type_set = self.family_type_map.get(selected_fam, set())
            type_list.extend(sorted(list(type_set)))
        else:
            # aggregate all types
            type_set_all = set()
            for v in self.family_type_map.values():
                type_set_all.update(v)
            type_list.extend(sorted(list(type_set_all)))
        self.TypeFilterCombo.ItemsSource = type_list
        if type_list:
            self.TypeFilterCombo.SelectedIndex = 0

    def _get_selected_family(self):
        try:
            return self.FamilyFilterCombo.SelectedItem
        except Exception:
            return None

    def _get_selected_type(self):
        try:
            return self.TypeFilterCombo.SelectedItem
        except Exception:
            return None

    def on_filter_changed(self, sender=None, args=None):
        # When family changes, repopulate type list
        if sender == self.FamilyFilterCombo:
            self._populate_type_filter()
        self._apply_filters(update_params=True)

    def _apply_filters(self, update_params=False):
        fam_sel = self._get_selected_family()
        typ_sel = self._get_selected_type()
        fam_sel = fam_sel or "<All Families>"
        typ_sel = typ_sel or "<All Types>"
        filtered = []
        for el in self.loaded_elements:
            fam, typ = self._extract_family_and_type(el)
            fam_ok = (fam_sel == "<All Families>") or (fam == fam_sel)
            typ_ok = (typ_sel == "<All Types>") or (typ == typ_sel)
            if fam_ok and typ_ok:
                filtered.append(el)
        self.filtered_elements = filtered
        if update_params:
            self.all_param_names = ae.discover_parameter_names(self.doc, self.filtered_elements, sample_limit=200)
            if not self.all_param_names:
                self.ParameterList.ItemsSource = []
                self._update_status("No text parameters found on filtered elements.")
            else:
                self._filter_params()
                self._update_status("Filtered to {0} elements. {1} text parameters (sampled).".format(len(self.filtered_elements), len(self.all_param_names)))

    def _set_results(self, rows):
        self.results = rows or []
        self.ResultsGrid.ItemsSource = self.results
        try:
            self.ResultsGrid.Items.Refresh()
        except Exception:
            pass

    # ---------------- Actions ----------------
    def load_elements(self, sender=None, args=None):
        try:
            self._ensure_engine()
            cat = self._get_selected_category()
            if cat is None:
                self._update_status("Pick a category to load.")
                return
            scope = self._get_scope()
            self._update_status("Working...")
            self.loaded_elements = ae.collect_elements(self.doc, self.uidoc, scope, cat.Id)
            count = len(self.loaded_elements)
            if count == 0:
                self.all_param_names = []
                self.ParameterList.ItemsSource = []
                self._set_results([])
                self._update_status("Loaded 0 elements for category '{0}'.".format(cat.Name))
                return
            self._build_family_type_filters(self.loaded_elements)
            self._apply_filters(update_params=True)
            if not self.filtered_elements:
                self._update_status("No elements match the selected filters.")
            else:
                self._update_status("Loaded {0} elements. Filtered to {1}.".format(count, len(self.filtered_elements)))
        except Exception as ex:
            try:
                self._update_status("Load failed: {0}".format(str(ex)))
            except Exception:
                pass

    def _get_selected_param_name(self):
        try:
            return self.ParameterList.SelectedItem
        except Exception:
            return None

    def run_audit(self, sender=None, args=None):
        try:
            if not self.loaded_elements:
                self._update_status("Load elements first.")
                return
            param_name = self._get_selected_param_name()
            if not param_name:
                self._update_status("Select a parameter to audit.")
                return
            fail_missing = bool(self.FailMissingCheck.IsChecked)
            fail_empty = bool(self.FailEmptyCheck.IsChecked)
            elements_to_check = self.filtered_elements if self.filtered_elements else self.loaded_elements
            self._update_status("Auditing '{0}' on {1} elements...".format(param_name, len(elements_to_check)))
            rows = ae.audit(self.doc, elements_to_check, param_name, fail_missing=fail_missing, fail_empty=fail_empty)
            self._set_results(rows)
            total = len(elements_to_check)
            fails = len(rows)
            passes = total - fails
            if fails == 0:
                self._update_status("Audit complete. 0 failures, {0} passed.".format(passes))
            else:
                self._update_status("Audit complete. {0} failures, {1} passed.".format(fails, passes))
        except Exception as ex:
            try:
                self._update_status("Audit error: {0}".format(str(ex)))
            except Exception:
                pass

    def on_result_selected(self, sender=None, args=None):
        if not self.ResultsGrid.SelectedItem:
            return
        try:
            row = self.ResultsGrid.SelectedItem
            eid = row.get("ElementIdObj", None)
            ae.show_element(self.uidoc, eid)
        except Exception:
            pass

    def select_all_failures(self, sender=None, args=None):
        if not self.results:
            self._update_status("No failures to select.")
            return
        ids = []
        for row in self.results:
            eid = row.get("ElementIdObj", None)
            if eid:
                ids.append(eid)
        if ids:
            ae.select_elements(self.uidoc, ids)
            self._update_status("Selected {0} failed elements.".format(len(ids)))
        else:
            self._update_status("No selectable failures found.")

    def isolate_failures(self, sender=None, args=None):
        if not self.results:
            self._update_status("No failures to isolate.")
            return
        ids = []
        for row in self.results:
            eid = row.get("ElementIdObj", None)
            if eid:
                ids.append(eid)
        if ids:
            ae.temp_isolate(self.doc, self.doc.ActiveView, ids)
            ae.select_elements(self.uidoc, ids)
            self._update_status("Temporarily isolated {0} elements.".format(len(ids)))
        else:
            self._update_status("No isolatable failures.")

    def clear_results(self, sender=None, args=None):
        self._set_results([])
        self._update_status("Results cleared.")

    def export_csv(self, sender=None, args=None):
        if not self.results:
            self._update_status("No failures to export.")
            return
        try:
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            path = os.path.join(desktop, 'category_parameter_audit.csv')
            with open(path, 'wb') as fp:
                writer = csv.writer(fp)
                writer.writerow(["ElementId", "Category", "Family", "Type", "CurrentValue", "FailReason"])
                for row in self.results:
                    writer.writerow([
                        row.get("ElementId", ""),
                        row.get("Category", ""),
                        row.get("Family", ""),
                        row.get("Type", ""),
                        row.get("CurrentValue", ""),
                        row.get("FailReason", ""),
                    ])
            self._update_status("Exported CSV to {0}".format(path))
        except Exception:
            self._update_status("CSV export failed.")


def main():
    global _ui_instance
    try:
        if _ui_instance is not None and _ui_instance.window is not None:
            _ui_instance.window.Close()
    except Exception:
        pass
    _ui_instance = MainWindow()
    try:
        _ui_instance.window.Closed += RoutedEventHandler(on_window_closed)
    except Exception:
        pass
    _ui_instance.window.Show()


def on_window_closed(sender, args):
    global _ui_instance
    try:
        _ui_instance = None
    except Exception:
        pass


if __name__ == '__main__':
    main()
