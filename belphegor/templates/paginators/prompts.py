from belphegor.templates import ui_ex
from .base import BasePaginator

#=============================================================================================================================#

class ConfirmedButton(ui_ex.ConfirmedButton):
    paginator: "YesNoPrompt"

class DeniedButton(ui_ex.DeniedButton):
    paginator: "YesNoPrompt"

class YesNoPrompt(BasePaginator):
    confirmed_button: ConfirmedButton
    denied_button: DeniedButton

    def render(self):
        if not self.view:
            view = self.view = ui_ex.View()
            self.confirmed_button = self.get_paginator_attribute("confirmed_button")
            self.denied_button = self.get_paginator_attribute("denied_button")
            view.add_item(self.confirmed_button)
            view.add_item(self.denied_button)

        return self
