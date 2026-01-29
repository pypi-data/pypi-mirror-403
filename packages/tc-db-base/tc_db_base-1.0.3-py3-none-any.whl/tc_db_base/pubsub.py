"""Pub/Sub Module - Real-time change notifications using MongoDB Change Streams."""

import logging
import threading
import queue
from typing import Callable, Dict, List, Optional, Set
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of document changes."""
    INSERT = 'insert'
    UPDATE = 'update'
    REPLACE = 'replace'
    DELETE = 'delete'
    INVALIDATE = 'invalidate'
    DROP = 'drop'
    RENAME = 'rename'


@dataclass
class ChangeEvent:
    """Represents a change event from MongoDB Change Stream."""
    change_type: ChangeType
    collection: str
    document_id: Optional[str]
    document: Optional[Dict]
    update_description: Optional[Dict]
    timestamp: datetime
    raw_event: Dict

    @classmethod
    def from_raw(cls, event: Dict) -> 'ChangeEvent':
        """Create ChangeEvent from raw MongoDB change event."""
        operation_type = event.get('operationType', 'unknown')
        try:
            change_type = ChangeType(operation_type)
        except ValueError:
            change_type = ChangeType.UPDATE

        doc_key = event.get('documentKey', {})
        document_id = str(doc_key.get('_id')) if doc_key.get('_id') else None

        return cls(
            change_type=change_type,
            collection=event.get('ns', {}).get('coll', 'unknown'),
            document_id=document_id,
            document=event.get('fullDocument'),
            update_description=event.get('updateDescription'),
            timestamp=event.get('clusterTime', datetime.now(timezone.utc)),
            raw_event=event
        )


@dataclass
class Subscription:
    """Represents a subscription to changes."""
    id: str
    collection: str
    callback: Callable[[ChangeEvent], None]
    change_types: Set[ChangeType]
    filter_query: Optional[Dict]
    active: bool = True

    def matches(self, event: ChangeEvent) -> bool:
        """Check if event matches this subscription."""
        # Check change type
        if self.change_types and event.change_type not in self.change_types:
            return False

        # Check collection
        if event.collection != self.collection:
            return False

        # Check filter (basic field matching on full document)
        if self.filter_query and event.document:
            for key, value in self.filter_query.items():
                if event.document.get(key) != value:
                    return False

        return True


class ChangeStreamWatcher:
    """Watches MongoDB Change Stream for a collection."""

    def __init__(self, collection, pipeline: List[Dict] = None):
        """Initialize watcher.

        Args:
            collection: MongoDB collection
            pipeline: Aggregation pipeline for filtering
        """
        self._collection = collection
        self._pipeline = pipeline or []
        self._stream = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._callbacks: List[Callable[[ChangeEvent], None]] = []
        self._error_callbacks: List[Callable[[Exception], None]] = []

    def add_callback(self, callback: Callable[[ChangeEvent], None]):
        """Add callback for change events."""
        self._callbacks.append(callback)

    def add_error_callback(self, callback: Callable[[Exception], None]):
        """Add callback for errors."""
        self._error_callbacks.append(callback)

    def start(self, full_document: str = 'updateLookup'):
        """Start watching for changes.

        Args:
            full_document: 'updateLookup' to get full document on updates
        """
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._watch_loop,
            args=(full_document,),
            daemon=True
        )
        self._thread.start()
        logger.info(f"Started change stream watcher for {self._collection.name}")

    def stop(self):
        """Stop watching."""
        self._running = False
        if self._stream:
            self._stream.close()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info(f"Stopped change stream watcher for {self._collection.name}")

    def _watch_loop(self, full_document: str):
        """Main watch loop (runs in thread)."""
        while self._running:
            try:
                with self._collection.watch(
                    pipeline=self._pipeline,
                    full_document=full_document
                ) as stream:
                    self._stream = stream
                    for event in stream:
                        if not self._running:
                            break
                        self._handle_event(event)
            except Exception as e:
                logger.error(f"Change stream error: {e}")
                self._handle_error(e)
                if self._running:
                    # Retry after delay
                    import time
                    time.sleep(1)

    def _handle_event(self, event: Dict):
        """Handle a change event."""
        try:
            change_event = ChangeEvent.from_raw(event)
            for callback in self._callbacks:
                try:
                    callback(change_event)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        except Exception as e:
            logger.error(f"Error processing event: {e}")

    def _handle_error(self, error: Exception):
        """Handle an error."""
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception:
                pass


class PubSub:
    """Pub/Sub system using MongoDB Change Streams.

    Provides real-time change notifications for collections.

    Usage:
        from tc_db_base import get_pubsub

        pubsub = get_pubsub()

        # Subscribe to all changes on users collection
        def on_user_change(event: ChangeEvent):
            print(f"User {event.document_id} was {event.change_type.value}")

        sub_id = pubsub.subscribe('users', on_user_change)

        # Subscribe to specific operations
        sub_id = pubsub.subscribe(
            'users',
            on_user_change,
            change_types=[ChangeType.INSERT, ChangeType.UPDATE]
        )

        # Subscribe with filter
        sub_id = pubsub.subscribe(
            'users',
            on_user_change,
            filter_query={'status': 'active'}
        )

        # Unsubscribe
        pubsub.unsubscribe(sub_id)

        # Publish (trigger callbacks manually, useful for testing)
        pubsub.publish('users', ChangeType.INSERT, document={'user_key': 'u123'})
    """

    _instance: Optional['PubSub'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._subscriptions: Dict[str, Subscription] = {}
        self._watchers: Dict[str, ChangeStreamWatcher] = {}
        self._event_queue: queue.Queue = queue.Queue()
        self._dispatcher_thread: Optional[threading.Thread] = None
        self._running = False
        self._subscription_counter = 0
        self._lock = threading.Lock()
        self._initialized = True

    def start(self):
        """Start the pub/sub system."""
        if self._running:
            return

        self._running = True
        self._dispatcher_thread = threading.Thread(
            target=self._dispatch_loop,
            daemon=True
        )
        self._dispatcher_thread.start()
        logger.info("PubSub system started")

    def stop(self):
        """Stop the pub/sub system."""
        self._running = False

        # Stop all watchers
        for watcher in self._watchers.values():
            watcher.stop()
        self._watchers.clear()

        # Stop dispatcher
        self._event_queue.put(None)  # Signal to stop
        if self._dispatcher_thread:
            self._dispatcher_thread.join(timeout=5)

        logger.info("PubSub system stopped")

    def subscribe(
        self,
        collection_name: str,
        callback: Callable[[ChangeEvent], None],
        change_types: List[ChangeType] = None,
        filter_query: Dict = None,
        repository=None
    ) -> str:
        """Subscribe to changes on a collection.

        Args:
            collection_name: Collection to watch
            callback: Function to call on changes
            change_types: Specific change types to watch (None = all)
            filter_query: Filter documents (matched against full document)
            repository: Optional DynamicRepository for the collection

        Returns:
            Subscription ID
        """
        with self._lock:
            self._subscription_counter += 1
            sub_id = f"sub_{self._subscription_counter}"

            subscription = Subscription(
                id=sub_id,
                collection=collection_name,
                callback=callback,
                change_types=set(change_types) if change_types else set(ChangeType),
                filter_query=filter_query
            )

            self._subscriptions[sub_id] = subscription

            # Ensure watcher exists for this collection
            self._ensure_watcher(collection_name, repository)

            logger.debug(f"Created subscription {sub_id} for {collection_name}")
            return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from changes.

        Args:
            subscription_id: Subscription ID

        Returns:
            True if unsubscribed
        """
        with self._lock:
            if subscription_id in self._subscriptions:
                sub = self._subscriptions.pop(subscription_id)
                sub.active = False

                # Check if we can stop the watcher
                remaining = [s for s in self._subscriptions.values() if s.collection == sub.collection]
                if not remaining and sub.collection in self._watchers:
                    self._watchers[sub.collection].stop()
                    del self._watchers[sub.collection]

                logger.debug(f"Removed subscription {subscription_id}")
                return True
            return False

    def publish(
        self,
        collection: str,
        change_type: ChangeType,
        document_id: str = None,
        document: Dict = None,
        update_description: Dict = None
    ):
        """Manually publish a change event.

        Useful for testing or triggering events from non-MongoDB sources.

        Args:
            collection: Collection name
            change_type: Type of change
            document_id: Document ID
            document: Full document
            update_description: Update description
        """
        event = ChangeEvent(
            change_type=change_type,
            collection=collection,
            document_id=document_id,
            document=document,
            update_description=update_description,
            timestamp=datetime.now(timezone.utc),
            raw_event={}
        )

        self._event_queue.put(event)

    def on(
        self,
        collection_name: str,
        change_types: List[ChangeType] = None
    ) -> Callable:
        """Decorator for subscribing to changes.

        Usage:
            @pubsub.on('users', [ChangeType.INSERT])
            def handle_new_user(event: ChangeEvent):
                print(f"New user: {event.document}")
        """
        def decorator(func: Callable[[ChangeEvent], None]) -> Callable:
            self.subscribe(collection_name, func, change_types)
            return func
        return decorator

    def on_insert(self, collection_name: str) -> Callable:
        """Decorator for insert events."""
        return self.on(collection_name, [ChangeType.INSERT])

    def on_update(self, collection_name: str) -> Callable:
        """Decorator for update events."""
        return self.on(collection_name, [ChangeType.UPDATE, ChangeType.REPLACE])

    def on_delete(self, collection_name: str) -> Callable:
        """Decorator for delete events."""
        return self.on(collection_name, [ChangeType.DELETE])

    def get_subscriptions(self, collection_name: str = None) -> List[Subscription]:
        """Get all subscriptions.

        Args:
            collection_name: Optional filter by collection

        Returns:
            List of subscriptions
        """
        subs = list(self._subscriptions.values())
        if collection_name:
            subs = [s for s in subs if s.collection == collection_name]
        return subs

    def _ensure_watcher(self, collection_name: str, repository=None):
        """Ensure a watcher exists for collection."""
        if collection_name in self._watchers:
            return

        # Get collection
        collection = None
        if repository:
            collection = repository.collection
        else:
            # Try to get from db_base
            try:
                from tc_db_base import get_repository
                repo = get_repository(collection_name)
                if repo:
                    collection = repo.collection
            except Exception as e:
                logger.warning(f"Could not get collection for {collection_name}: {e}")
                return

        if not collection:
            logger.warning(f"No collection found for {collection_name}, cannot watch")
            return

        # Create watcher
        watcher = ChangeStreamWatcher(collection)
        watcher.add_callback(self._on_change)
        watcher.add_error_callback(self._on_error)
        watcher.start()

        self._watchers[collection_name] = watcher

    def _on_change(self, event: ChangeEvent):
        """Handle change from watcher."""
        self._event_queue.put(event)

    def _on_error(self, error: Exception):
        """Handle error from watcher."""
        logger.error(f"Watcher error: {error}")

    def _dispatch_loop(self):
        """Dispatch events to subscribers."""
        while self._running:
            try:
                event = self._event_queue.get(timeout=1)
                if event is None:
                    break

                self._dispatch_event(event)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Dispatch error: {e}")

    def _dispatch_event(self, event: ChangeEvent):
        """Dispatch event to matching subscribers."""
        for subscription in list(self._subscriptions.values()):
            if not subscription.active:
                continue

            if subscription.matches(event):
                try:
                    subscription.callback(event)
                except Exception as e:
                    logger.error(f"Subscription callback error: {e}")


class EventEmitter:
    """Simple event emitter for local pub/sub (without MongoDB).

    Usage:
        emitter = EventEmitter()

        def on_data(data):
            print(f"Got: {data}")

        emitter.on('my_event', on_data)
        emitter.emit('my_event', {'key': 'value'})
        emitter.off('my_event', on_data)
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._once_listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, callback: Callable):
        """Subscribe to event.

        Args:
            event: Event name
            callback: Callback function
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def once(self, event: str, callback: Callable):
        """Subscribe to event (fires once).

        Args:
            event: Event name
            callback: Callback function
        """
        if event not in self._once_listeners:
            self._once_listeners[event] = []
        self._once_listeners[event].append(callback)

    def off(self, event: str, callback: Callable = None):
        """Unsubscribe from event.

        Args:
            event: Event name
            callback: Specific callback to remove (None = remove all)
        """
        if callback is None:
            self._listeners.pop(event, None)
            self._once_listeners.pop(event, None)
        else:
            if event in self._listeners:
                self._listeners[event] = [c for c in self._listeners[event] if c != callback]
            if event in self._once_listeners:
                self._once_listeners[event] = [c for c in self._once_listeners[event] if c != callback]

    def emit(self, event: str, *args, **kwargs):
        """Emit event to all subscribers.

        Args:
            event: Event name
            *args: Positional arguments for callback
            **kwargs: Keyword arguments for callback
        """
        # Regular listeners
        for callback in self._listeners.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

        # Once listeners
        once_callbacks = self._once_listeners.pop(event, [])
        for callback in once_callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Once callback error: {e}")

    def listeners(self, event: str) -> List[Callable]:
        """Get all listeners for event."""
        return self._listeners.get(event, []) + self._once_listeners.get(event, [])

    def has_listeners(self, event: str) -> bool:
        """Check if event has listeners."""
        return bool(self.listeners(event))

    def clear(self):
        """Remove all listeners."""
        self._listeners.clear()
        self._once_listeners.clear()


# Module-level singleton
_pubsub: Optional[PubSub] = None
_emitter: Optional[EventEmitter] = None


def get_pubsub() -> PubSub:
    """Get PubSub singleton.

    Returns:
        PubSub instance
    """
    global _pubsub
    if _pubsub is None:
        _pubsub = PubSub()
    return _pubsub


def get_emitter() -> EventEmitter:
    """Get EventEmitter singleton.

    Returns:
        EventEmitter instance
    """
    global _emitter
    if _emitter is None:
        _emitter = EventEmitter()
    return _emitter
