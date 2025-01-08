from enum import Enum
from typing import Union

from aiogram_dialog.widgets.kbd import Group, Button
from aiogram_dialog.widgets.kbd.button import OnClick
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.widget_event import WidgetEventProcessor


class KeyboardBuilder:
    @staticmethod
    def from_enum(titles: type[Enum], handler: Union[OnClick, WidgetEventProcessor, None],
                  width: int = 4, when: str = None, enum_value: bool = False, postfix: str = ""):
        if enum_value:
            titles = [(f"{{{element.value + postfix}}}", f"{element.name}") for element in titles]
        else:
            titles = [(f"{{{element.name + postfix}}}", f"{element.name}") for element in titles]

        kbd = Group(*[Button(text=Format(text=title), id=id_, on_click=handler) for title, id_ in titles],
                    when=when, width=width)
        return kbd

    def from_iterable(self):
        pass
