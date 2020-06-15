import functools
from typing import List, Callable
import logging

from aiogram import Dispatcher

from aiogram_scenario.state import AbstractState


logger = logging.getLogger(__name__)


def _log_registration_handlers(states: List[AbstractState], callback: Callable, handler_type: str) -> None:

    logger.debug(f"""For the states '{" ,".join([i.name for i in states])}', a {handler_type}_handler """
                 f"is registered: '{callback.__qualname__}'")


class CommonRegistrar:

    def __init__(self, dispatcher: Dispatcher):

        self._dispatcher = dispatcher

    def register_message_handler(self, callback: Callable, states: List[AbstractState], *custom_filters, commands=None,
                                 regexp=None, content_types=None, run_task=None, **kwargs) -> None:

        reg_partial = functools.partial(self._dispatcher.register_message_handler, callback, *custom_filters,
                                        commands=commands, regexp=regexp, content_types=content_types,
                                        run_task=run_task, **kwargs)
        self._register_handler(states, reg_partial)
        _log_registration_handlers(states, callback, "message")

    def register_callback_query_handler(self, callback: Callable, states: List[AbstractState], *custom_filters,
                                        run_task=None, **kwargs) -> None:

        reg_partial = functools.partial(self._dispatcher.callback_query_handler, callback, *custom_filters,
                                        run_task=run_task, **kwargs)
        self._register_handler(states, reg_partial)
        _log_registration_handlers(states, callback, "callback_query")

    def register_channel_post_handler(self, callback: Callable, states: List[AbstractState], *custom_filters,
                                      commands=None, regexp=None, content_types=None, run_task=None, **kwargs) -> None:

        reg_partial = functools.partial(self._dispatcher.register_channel_post_handler, callback, *custom_filters,
                                        commands=commands, regexp=regexp, content_types=content_types,
                                        run_task=run_task, **kwargs)
        self._register_handler(states, reg_partial)
        _log_registration_handlers(states, callback, "channel_post")

    def register_chosen_inline_handler(self, callback: Callable, states: List[AbstractState], *custom_filters,
                                       run_task=None, **kwargs) -> None:

        reg_partial = functools.partial(self._dispatcher.register_chosen_inline_handler, callback, *custom_filters,
                                        run_task=run_task, **kwargs)
        self._register_handler(states, reg_partial)
        _log_registration_handlers(states, callback, "chosen_inline")

    def register_edited_channel_post_handler(self, callback: Callable, states: List[AbstractState], *custom_filters,
                                             commands=None, regexp=None, content_types=None,
                                             run_task=None, **kwargs) -> None:

        reg_partial = functools.partial(self.register_edited_channel_post_handler, callback, *custom_filters,
                                        commands=commands, regexp=regexp, content_types=content_types,
                                        run_task=run_task, **kwargs)
        self._register_handler(states, reg_partial)
        _log_registration_handlers(states, callback, "edited_channel_post")

    def register_edited_message_handler(self, callback: Callable, states: List[AbstractState], *custom_filters,
                                        commands=None, regexp=None, content_types=None,
                                        run_task=None, **kwargs) -> None:

        reg_partial = functools.partial(self.register_edited_message_handler, callback, *custom_filters,
                                        commands=commands, regexp=regexp, content_types=content_types,
                                        run_task=run_task, **kwargs)
        self._register_handler(states, reg_partial)
        _log_registration_handlers(states, callback, "edited_message")

    def register_inline_handler(self, callback: Callable, states: List[AbstractState], *custom_filters,
                                run_task=None, **kwargs) -> None:

        reg_partial = functools.partial(self._dispatcher.register_inline_handler, callback, *custom_filters,
                                        run_task=run_task, **kwargs)
        self._register_handler(states, reg_partial)
        _log_registration_handlers(states, callback, "inline")

    def register_pre_checkout_query_handler(self, callback: Callable, states: List[AbstractState], *custom_filters,
                                            run_task=None, **kwargs) -> None:

        reg_partial = functools.partial(self._dispatcher.register_pre_checkout_query_handler, callback, *custom_filters,
                                        run_task=run_task, **kwargs)
        self._register_handler(states, reg_partial)
        _log_registration_handlers(states, callback, "pre_checkout_query")

    def register_shipping_query_handler(self, callback: Callable, states: List[AbstractState], *custom_filters,
                                        run_task=None, **kwargs) -> None:

        reg_partial = functools.partial(self._dispatcher.shipping_query_handler, callback, *custom_filters,
                                        run_task=run_task, **kwargs)
        self._register_handler(states, reg_partial)
        _log_registration_handlers(states, callback, "shipping_query")

    @staticmethod
    def _register_handler(states: List[AbstractState], reg_partial: Callable):

        for state in states:
            reg_partial(state=state)
