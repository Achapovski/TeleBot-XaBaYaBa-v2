from enum import Enum
from typing import Union

from aiogram_dialog.widgets.kbd import Group, Button
from aiogram_dialog.widgets.kbd.button import OnClick
from aiogram_dialog.widgets.text import Format
from aiogram_dialog.widgets.widget_event import WidgetEventProcessor
from functools import lru_cache
from itertools import cycle


class KeyboardBuilder:
    # Закэшировать с помощью Redis
    @staticmethod
    @lru_cache
    def from_enum(titles: type[Enum], handler: Union[OnClick, WidgetEventProcessor, None, list[OnClick]], width: int = 4,
                  when: str | type[Enum] = None, enum_value: bool = False, postfix: str = ""):

        if isinstance(when, str) or when is None:
            when = (when, )
        if not isinstance(handler, list) or when is None:
            handler = (handler, )

        whens = cycle(when)
        on_clicks = cycle(handler)
        nv_attr = ("name", "value")[enum_value]

        titles = ((f"{{{getattr(element, nv_attr) + postfix}}}", f"{element.name}") for element in titles)
        kbd = ((Button(text=Format(text=title), id=id_, on_click=next(on_clicks),
                       when=getattr(next(whens), "__str__")()) for title, id_ in titles))

        return Group(*kbd, width=width)

    def from_iterable(self):
        pass
