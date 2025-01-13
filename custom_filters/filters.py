from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram_dialog.api.entities import Context

from dialogs.dialogs_states import UserCategoriesStates as Ucs, WorkStates


class CategoriesStateFilter(BaseFilter):
    async def __call__(self, message: Message, aiogd_context: Context, **kwargs):
        if aiogd_context and aiogd_context.state == Ucs.get_categories and not message.text.startswith("/"):
            return True
        return False


class WorkStateFilter(BaseFilter):
    async def __call__(self, message: Message, aiogd_context: Context, *args, **kwargs):
        if aiogd_context and aiogd_context.state == WorkStates.add_category:
            return True
        return False
