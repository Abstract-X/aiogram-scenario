from typing import Optional, List, Callable, Collection, Dict
import logging

from aiogram import Dispatcher

from .state import AbstractState
from .magazine import Magazine
from .locking import TransitionsLocksStorage
from aiogram_scenario import exceptions, helpers
from aiogram_scenario.fsm.storages import BaseStorage


logger = logging.getLogger(__name__)


class FiniteStateMachine:

    def __init__(self, dispatcher: Dispatcher, storage: BaseStorage):

        self._dispatcher = dispatcher
        self._storage = storage
        self._locks_storage = TransitionsLocksStorage()
        self._initial_state: Optional[AbstractState] = None
        self._states_routes: Dict[AbstractState, Collection[Callable]] = {}

    @property
    def initial_state(self) -> AbstractState:

        if self._initial_state is None:
            raise exceptions.InitialStateError("initial state not set!")

        return self._initial_state

    @property
    def states(self) -> List[AbstractState]:

        try:
            states = [self.initial_state]
        except exceptions.InitialStateError:
            states = []
        states.extend(self._states_routes.keys())

        return states

    def set_initial_state(self, state: AbstractState) -> None:

        if self._initial_state is not None:
            raise exceptions.SettingInitialStateError("initial state has already been set before!")
        elif state.is_assigned:
            raise exceptions.SettingInitialStateError(f"state '{state}' has already been assigned!")
        elif state in self.states:
            raise exceptions.DuplicateError(f"state '{state}' is already exists!")

        state.is_assigned = True
        state.is_initial = True
        self._initial_state = state

        logger.debug(f"Added initial state for FSM: '{self._initial_state}'")

    def add_state(self, state: AbstractState, pointing_handlers: Collection[Callable]) -> None:

        if state.is_assigned:
            raise exceptions.AddingStateError(f"state '{state}' has already been assigned!")
        elif state in self.states:
            raise exceptions.DuplicateError(f"state '{state}' is already exists!")
        elif len(set(pointing_handlers)) != len(pointing_handlers):
            raise exceptions.DuplicateError("there are repetitions in pointing handlers!")

        existing_pointing_handlers = self._existing_pointing_handlers
        for i in pointing_handlers:
            if i in existing_pointing_handlers:
                raise exceptions.DuplicateError(f"handler '{i.__qualname__}' has already been added earlier!")

        state.is_assigned = True
        self._states_routes[state] = set(pointing_handlers)

        logger.debug(f"Added state to FSM: '{state}'")

    def remove_state(self, state: AbstractState) -> None:

        try:
            del self._states_routes[state]
        except KeyError:
            raise exceptions.StateNotFoundError("no state found to remove!")
        else:
            state.is_assigned = False

    async def execute_transition(self, current_state: AbstractState,
                                 target_state: AbstractState,
                                 proc_args: Collection,
                                 context_kwargs: dict,
                                 magazine: Magazine,
                                 user_id: Optional[int] = None,
                                 chat_id: Optional[int] = None) -> None:

        logger.debug(f"Started transition from '{current_state}' to '{target_state}' "
                     f"for '{user_id=}' in '{chat_id=}'...")

        if not magazine.is_loaded:
            raise exceptions.TransitionError("magazine is not loaded!")

        with self._locks_storage.acquire(current_state, target_state, user_id, chat_id):

            exit_kwargs = helpers.get_existing_kwargs(current_state.process_exit, check_varkw=True, **context_kwargs)
            enter_kwargs = helpers.get_existing_kwargs(target_state.process_enter, check_varkw=True, **context_kwargs)

            await current_state.process_exit(*proc_args, **exit_kwargs)
            logger.debug(f"Produced exit from state '{current_state}' for '{user_id=}' in '{chat_id=}'")
            await target_state.process_enter(*proc_args, **enter_kwargs)
            logger.debug(f"Produced enter to state '{target_state}' for '{user_id=}' in '{chat_id=}'")

            await self._set_state(target_state, user_id=user_id, chat_id=chat_id)

            magazine.set(str(target_state))
            await magazine.commit()

        logger.debug(f"Transition to '{target_state}' for '{user_id=}' in '{chat_id=}' completed!")

    async def execute_next_transition(self, pointing_handler: Callable,
                                      event,
                                      context_kwargs: dict,
                                      user_id: Optional[int] = None,
                                      chat_id: Optional[int] = None) -> None:

        magazine = self.get_magazine(user_id, chat_id)
        try:
            await magazine.load()
        except exceptions.MagazineInitializationError:
            await magazine.initialize(str(self.initial_state))

        current_state = self._get_state_by_name(magazine.current_state)
        target_state = self._get_state_by_pointing_handler(pointing_handler)

        await self.execute_transition(
            current_state=current_state,
            target_state=target_state,
            proc_args=(event,),
            context_kwargs=context_kwargs,
            magazine=magazine,
            user_id=user_id,
            chat_id=chat_id
        )

    async def execute_back_transition(self, event,
                                      context_kwargs: dict,
                                      user_id: Optional[int] = None,
                                      chat_id: Optional[int] = None) -> None:

        magazine = self.get_magazine(user_id, chat_id)
        await magazine.load()

        penultimate_state = magazine.penultimate_state
        if penultimate_state is None:
            raise exceptions.TransitionError("there are not enough states in the magazine to return!")

        current_state = self._get_state_by_name(magazine.current_state)
        target_state = self._get_state_by_name(penultimate_state)

        await self.execute_transition(
            current_state=current_state,
            target_state=target_state,
            proc_args=(event,),
            context_kwargs=context_kwargs,
            magazine=magazine,
            user_id=user_id,
            chat_id=chat_id
        )

    def get_magazine(self, user_id: Optional[int] = None, chat_id: Optional[int] = None) -> Magazine:

        return Magazine(storage=self._storage, user_id=user_id, chat_id=chat_id)

    async def set_transitions_chronology(self, states: List[AbstractState],
                                         user_id: Optional[int] = None,
                                         chat_id: Optional[int] = None) -> None:

        # TODO: Add ability to check correctness of the chronology
        magazine = self.get_magazine(user_id, chat_id)
        await magazine.initialize(str(self.initial_state))

        for state in states:
            magazine.set(str(state))
        await magazine.commit()

    async def _set_state(self, state: AbstractState,
                         user_id: Optional[int] = None,
                         chat_id: Optional[int] = None) -> None:

        fsm_context = self._dispatcher.current_state(chat=chat_id, user=user_id)
        await fsm_context.set_state(state.raw_value)

        logger.debug(f"State '{state}' is set for '{user_id=}' in '{chat_id=}'")

    def _get_state_by_pointing_handler(self, pointing_handler: Callable) -> AbstractState:

        for state, pointing_handlers in self._states_routes.items():
            if pointing_handler in pointing_handlers:
                return state

        raise exceptions.StateNotFoundError(f"no target state found for '{pointing_handler.__qualname__}' handler!")

    def _get_state_by_name(self, name: str) -> AbstractState:

        for state in self.states:
            if name == state.name:
                return state

        raise exceptions.StateNotFoundError(f"no state found for '{name}' name!")

    @property
    def _existing_pointing_handlers(self) -> List[Callable]:

        handlers = []
        for pointing_handlers in self._states_routes.values():
            handlers.extend(pointing_handlers)

        return handlers
