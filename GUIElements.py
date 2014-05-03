############################################################
# FlatCAM: 2D Post-processing for Manufacturing            #
# http://caram.cl/software/flatcam                         #
# Author: Juan Pablo Caram (c)                             #
# Date: 2/5/2014                                           #
# MIT Licence                                              #
############################################################

from gi.repository import Gtk
import re
from copy import copy
import FlatCAMApp


class RadioSet(Gtk.Box):
    def __init__(self, choices):
        """
        The choices are specified as a list of dictionaries containing:

        * 'label': Shown in the UI
        * 'value': The value returned is selected

        :param choices: List of choices. See description.
        :type choices: list
        """
        Gtk.Box.__init__(self)
        self.choices = copy(choices)
        self.group = None
        for choice in self.choices:
            if self.group is None:
                choice['radio'] = Gtk.RadioButton.new_with_label(None, choice['label'])
                self.group = choice['radio']
            else:
                choice['radio'] = Gtk.RadioButton.new_with_label_from_widget(self.group, choice['label'])
            self.pack_start(choice['radio'], expand=True, fill=False, padding=2)
            choice['radio'].connect('toggled', self.on_toggle)

        self.group_toggle_fn = lambda x, y: None

    def on_toggle(self, btn):
        if btn.get_active():
            self.group_toggle_fn(btn, self.get_value)
        return

    def get_value(self):
        for choice in self.choices:
            if choice['radio'].get_active():
                return choice['value']
        FlatCAMApp.App.log.error("No button was toggled in RadioSet.")
        return None

    def set_value(self, val):
        for choice in self.choices:
            if choice['value'] == val:
                choice['radio'].set_active(True)
                return
        FlatCAMApp.App.log.error("Value given is not part of this RadioSet: %s" % str(val))


class LengthEntry(Gtk.Entry):
    def __init__(self, output_units='IN'):
        Gtk.Entry.__init__(self)
        self.output_units = output_units
        self.format_re = re.compile(r"^([^\s]+)(?:\s([a-zA-Z]+))?$")

        # Unit conversion table OUTPUT-INPUT
        self.scales = {
            'IN': {'MM': 1/25.4},
            'MM': {'IN': 25.4}
        }

        self.connect('activate', self.on_activate)

    def on_activate(self, *args):
        val = self.get_value()
        if val is not None:
            self.set_text(str(val))
        else:
            FlatCAMApp.App.log.warning("Could not interpret entry: %s" % self.get_text())

    def get_value(self):
        raw = self.get_text().strip(' ')
        match = self.format_re.search(raw)
        if not match:
            return None
        try:
            if match.group(2) is not None and match.group(2).upper() in self.scales:
                return float(match.group(1))*self.scales[self.output_units][match.group(2).upper()]
            else:
                return float(match.group(1))
        except:
            FlatCAMApp.App.log.error("Could not parse value in entry: %s" % str(raw))
            return None

    def set_value(self, val):
        self.set_text(str(val))


class FloatEntry(Gtk.Entry):
    def __init__(self):
        Gtk.Entry.__init__(self)

        self.connect('activate', self.on_activate)

    def on_activate(self, *args):
        val = self.get_value()
        if val is not None:
            self.set_text(str(val))
        else:
            FlatCAMApp.App.log.warning("Could not interpret entry: %s" % self.get_text())

    def get_value(self):
        raw = self.get_text().strip(' ')
        try:
            evaled = eval(raw)
        except:
            FlatCAMApp.App.log.error("Could not evaluate: %s" % str(raw))
            return None

        return float(evaled)

    def set_value(self, val):
        self.set_text(str(val))


class IntEntry(Gtk.Entry):
    def __init__(self):
        Gtk.Entry.__init__(self)

    def get_value(self):
        return int(self.get_text())

    def set_value(self, val):
        self.set_text(str(val))


class FCEntry(Gtk.Entry):
    def __init__(self):
        Gtk.Entry.__init__(self)

    def get_value(self):
        return self.get_text()

    def set_value(self, val):
        self.set_text(str(val))


class EvalEntry(Gtk.Entry):
    def __init__(self):
        Gtk.Entry.__init__(self)

    def on_activate(self, *args):
        val = self.get_value()
        if val is not None:
            self.set_text(str(val))
        else:
            FlatCAMApp.App.log.warning("Could not interpret entry: %s" % self.get_text())

    def get_value(self):
        raw = self.get_text().strip(' ')
        try:
            return eval(raw)
        except:
            FlatCAMApp.App.log.error("Could not evaluate: %s" % str(raw))
            return None

    def set_value(self, val):
        self.set_text(str(val))


class FCCheckBox(Gtk.CheckButton):
    def __init__(self, label=''):
        Gtk.CheckButton.__init__(self, label=label)

    def get_value(self):
        return self.get_active()

    def set_value(self, val):
        self.set_active(val)