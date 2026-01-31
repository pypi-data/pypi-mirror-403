# -*- coding: UTF-8 -*-
# Copyright 2026 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

"""React frontend features models."""

from lino.api import dd, _


class PrimeReactTheme(dd.Choice):
    """A single PrimeReact theme choice."""
    def __init__(self, value, color_scheme):
        # super().__init__(value, value.replace('-', " ").capitalize(), value.replace("-", "_"))
        super().__init__(value, value.replace('-', " ").capitalize(), value)
        self.color_scheme = color_scheme


class PrimeReactThemes(dd.ChoiceList):
    """Choice list of PrimeReact themes."""
    verbose_name = _("PrimeReact Theme")
    item_class = PrimeReactTheme


add = PrimeReactThemes.add_item
add('rhea', "light")
add('bootstrap4-light-blue', "light")
add('bootstrap4-light-purple', "light")
add('bootstrap4-dark-blue', "dark")
add('bootstrap4-dark-purple', "dark")
add('md-light-indigo', "light")
add('md-light-deeppurple', "light")
add('md-dark-indigo', "dark")
add('md-dark-deeppurple', "dark")
add('mdc-light-indigo', "light")
add('mdc-light-deeppurple', "light")
add('mdc-dark-indigo', "dark")
add('mdc-dark-deeppurple', "dark")
add('tailwind-light', "light")
add('fluent-light', "light")
add('lara-light-blue', "light")
add('lara-light-indigo', "light")
add('lara-light-purple', "light")
add('lara-light-teal', "light")
add('lara-dark-blue', "dark")
add('lara-dark-indigo', "dark")
add('lara-dark-purple', "dark")
add('lara-dark-teal', "dark")
add('soho-light', "light")
add('soho-dark', "dark")
add('viva-light', "light")
add('viva-dark', "dark")
add('mira', "light")
add('nano', "light")
add('saga-blue', "light")
add('saga-green', "light")
add('saga-orange', "light")
add('saga-purple', "light")
add('vela-blue', "dark")
add('vela-green', "dark")
add('vela-orange', "dark")
add('vela-purple', "dark")
add('arya-blue', "dark")
add('arya-green', "dark")
add('arya-orange', "dark")
add('arya-purple', "dark")

if dd.is_installed("system"):
    dd.inject_field("system.SiteConfig",
                    "primereact_theme",
                    PrimeReactThemes.field(default=dd.plugins.react.primereact_theme_name))
