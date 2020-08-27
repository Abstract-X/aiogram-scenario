from typing import Optional, Callable
import logging

from .fsm import FiniteStateMachine
from aiogram_scenario.helpers import EVENT_UNION_TYPE


logger = logging.getLogger(__name__)


class FSMPointer:

    def __init__(self, fsm: FiniteStateMachine,
                 signal_handler: Callable,
                 event: EVENT_UNION_TYPE,
                 context_kwargs: dict,
                 user_id: Optional[int] = None,
                 chat_id: Optional[int] = None):

        self._fsm = fsm
        self._signal_handler = signal_handler
        self._event = event
        self._context_kwargs = context_kwargs
        self._user_id = user_id
        self._chat_id = chat_id

    async def go_next(self) -> None:

        logger.debug("FSM received a request to move to next state for "
                     f"'user_id={self._user_id}' in 'chat_id={self._chat_id}'")
        await self._fsm.execute_next_transition(
            signal_handler=self._signal_handler,
            event=self._event,
            context_kwargs=self._context_kwargs,
            user_id=self._user_id,
            chat_id=self._chat_id
        )

    async def go_back(self) -> None:

        logger.debug("FSM received a request to move to previous state for "
                     f"'user_id={self._user_id}' in 'chat_id={self._chat_id}'")
        await self._fsm.execute_back_transition(
            event=self._event,
            context_kwargs=self._context_kwargs,
            user_id=self._user_id,
            chat_id=self._chat_id
        )
