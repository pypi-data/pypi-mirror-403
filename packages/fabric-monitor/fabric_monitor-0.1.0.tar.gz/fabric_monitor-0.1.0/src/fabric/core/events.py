"""Event system module"""

from typing import Callable, List, Dict, Any, Awaitable, Union
import asyncio
import logging

logger = logging.getLogger(__name__)

# Event handler types
SyncHandler = Callable[..., None]
AsyncHandler = Callable[..., Awaitable[None]]
EventHandler = Union[SyncHandler, AsyncHandler]


class EventEmitter:
    """Event emitter
    
    Provides simple event subscription and publishing mechanism,
    supports both synchronous and asynchronous handlers.
    
    Example:
        >>> emitter = EventEmitter()
        >>> @emitter.on("request")
        ... async def handle_request(record):
        ...     print(f"New request: {record.path}")
        >>> await emitter.emit("request", record)
    """
    
    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = {}
    
    def on(self, event: str) -> Callable[[EventHandler], EventHandler]:
        """Decorator: Register event handler
        
        Args:
            event: Event name
            
        Returns:
            Decorator function
        """
        def decorator(handler: EventHandler) -> EventHandler:
            self.add_listener(event, handler)
            return handler
        return decorator
    
    def add_listener(self, event: str, handler: EventHandler) -> None:
        """Add event listener
        
        Args:
            event: Event name
            handler: Event handler
        """
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
    
    def remove_listener(self, event: str, handler: EventHandler) -> None:
        """Remove event listener
        
        Args:
            event: Event name
            handler: Event handler
        """
        if event in self._handlers:
            try:
                self._handlers[event].remove(handler)
            except ValueError:
                pass
    
    def remove_all_listeners(self, event: str = None) -> None:
        """Remove all listeners
        
        Args:
            event: Event name, if None removes listeners for all events
        """
        if event is None:
            self._handlers.clear()
        elif event in self._handlers:
            del self._handlers[event]
    
    async def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit event
        
        Args:
            event: Event name
            *args: Positional arguments to pass to handlers
            **kwargs: Keyword arguments to pass to handlers
        """
        if event not in self._handlers:
            return
        
        for handler in self._handlers[event]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(*args, **kwargs)
                else:
                    handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in event handler for '{event}': {e}")
    
    def emit_sync(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit event synchronously (only calls sync handlers)
        
        Args:
            event: Event name
            *args: Positional arguments to pass to handlers
            **kwargs: Keyword arguments to pass to handlers
        """
        if event not in self._handlers:
            return
        
        for handler in self._handlers[event]:
            if not asyncio.iscoroutinefunction(handler):
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in sync event handler for '{event}': {e}")
    
    @property
    def events(self) -> List[str]:
        """Get all registered event names"""
        return list(self._handlers.keys())
    
    def listener_count(self, event: str) -> int:
        """Get listener count for specified event"""
        return len(self._handlers.get(event, []))
