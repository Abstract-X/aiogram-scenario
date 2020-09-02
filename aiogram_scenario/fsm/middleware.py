from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import current_handler, ctx_data
from aiogram.types import User, Chat

from .fsm import FiniteStateMachine
from .trigger import FSMTrigger
from aiogram_scenario import helpers


class FSMMiddleware(BaseMiddleware):

    def __init__(self, fsm: FiniteStateMachine, trigger_arg: str = "fsm"):

        super().__init__()
        self._fsm = fsm
        self._trigger_arg = trigger_arg

    async def on_process(self, _, data: dict):

        self._setup_trigger(data)

    async def on_process_error(self, _, exception: Exception, data: dict):  # noqa

        self._setup_trigger(data)

    on_process_message = on_process

    on_process_edited_message = on_process

    on_process_channel_post = on_process

    on_process_edited_channel_post = on_process

    on_process_inline_query = on_process

    on_process_chosen_inline_result = on_process

    on_process_callback_query = on_process

    on_process_shipping_query = on_process

    on_process_pre_checkout_query = on_process

    def _setup_trigger(self, data: dict) -> None:

        user = User.get_current()
        chat = Chat.get_current()

        user_id = user.id if user is not None else None
        chat_id = chat.id if chat is not None else None

        data[self._trigger_arg] = FSMTrigger(
            fsm=self._fsm,
            trigger_func=current_handler.get(),
            event=helpers.get_current_event(),
            context_kwargs=ctx_data.get(),
            user_id=user_id,
            chat_id=chat_id
        )
