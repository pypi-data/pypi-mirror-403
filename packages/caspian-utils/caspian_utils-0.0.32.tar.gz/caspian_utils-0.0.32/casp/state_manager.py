import json
from contextvars import ContextVar
from typing import Any, Callable, Dict, Optional
from fastapi import Request

# Context variables for request-scoped state
_state_data: ContextVar[Dict] = ContextVar('state_data', default={})
_state_listeners: ContextVar[list] = ContextVar('state_listeners', default=[])
_current_request: ContextVar[Optional[Request]
                             ] = ContextVar('current_request', default=None)


class AttributeDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(
                f"'AttributeDict' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value


class StateManager:
    APP_STATE_KEY = 'app_state_cL7y4KirLp'

    @staticmethod
    def set_request(request: Request):
        _current_request.set(request)

    @staticmethod
    def _get_session() -> dict:
        request = _current_request.get()
        if request and hasattr(request.state, 'session'):
            return request.state.session
        return {}

    @staticmethod
    def _set_session(key: str, value: Any):
        request = _current_request.get()
        if request:
            if not hasattr(request.state, 'session'):
                request.state.session = {}
            request.state.session[key] = value

    @staticmethod
    def _get_state_data() -> Dict:
        return _state_data.get()

    @staticmethod
    def _set_state_data(data: Dict) -> None:
        _state_data.set(data)

    @staticmethod
    def _get_listeners() -> list:
        return _state_listeners.get()

    @staticmethod
    def init(request: Request) -> None:
        StateManager.set_request(request)
        _state_data.set({})
        _state_listeners.set([])
        StateManager.load_state()

        is_wire = request.headers.get('X-PulsePoint-Wire', False)
        if not is_wire:
            StateManager.reset_state()

    @staticmethod
    def get_state(key: Optional[str] = None, initial_value: Any = None) -> Any:
        state = StateManager._get_state_data()
        if key is None:
            return AttributeDict(state)
        value = state.get(key, initial_value)
        return AttributeDict(value) if isinstance(value, dict) else value

    @staticmethod
    def set_state(key: str, value: Any = None) -> None:
        state = StateManager._get_state_data()
        state[key] = value
        _state_data.set(state)
        StateManager.notify_listeners()
        StateManager.save_state()

    @staticmethod
    def subscribe(listener: Callable) -> Callable:
        listeners = StateManager._get_listeners()
        listeners.append(listener)
        listener(StateManager._get_state_data())

        def unsubscribe():
            current_listeners = StateManager._get_listeners()
            if listener in current_listeners:
                current_listeners.remove(listener)

        return unsubscribe

    @staticmethod
    def save_state() -> None:
        state = StateManager._get_state_data()
        StateManager._set_session(
            StateManager.APP_STATE_KEY, json.dumps(state))

    @staticmethod
    def load_state() -> None:
        session = StateManager._get_session()
        if StateManager.APP_STATE_KEY in session:
            try:
                loaded_state = json.loads(session[StateManager.APP_STATE_KEY])
                if isinstance(loaded_state, dict):
                    StateManager._set_state_data(loaded_state)
                    StateManager.notify_listeners()
            except json.JSONDecodeError:
                pass

    @staticmethod
    def reset_state(key: Optional[str] = None) -> None:
        state = StateManager._get_state_data()
        if key is not None:
            if key in state:
                state[key] = None
        else:
            state = {}
        _state_data.set(state)
        StateManager.notify_listeners()
        StateManager.save_state()

    @staticmethod
    def notify_listeners() -> None:
        listeners = StateManager._get_listeners()
        state = StateManager._get_state_data()
        for listener in listeners:
            listener(state)
