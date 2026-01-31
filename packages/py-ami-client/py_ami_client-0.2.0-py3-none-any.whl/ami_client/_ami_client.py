import time, logging, socket, threading, traceback, queue
from classmods import ENVMod, suppress_errors, logwrap
from typing import (
    Any, Callable, Dict, List, Literal, Optional,
    Self, Set, Tuple, Type, Union, cast,
)
from .operation import (
    Operation, NotImplementedOperation,
    Action, PendingAction,
    Event, EventDispatcher, 
    Response,
    action_map, response_map, event_map,
)
from .operation.action import Login, Logoff, Ping

EXCEPTED_OS_ERROR = 'An operation was attempted on something that is not a socket'

logger = logging.getLogger('AMIClient')

class AMIClient:
    full_map: Tuple[
            Tuple[str, Dict[str, Type[Operation]]]
        ] = (
            ('Event', event_map),  # type: ignore
            ('Response', response_map),  # type: ignore
            ('Action', action_map),  # type: ignore
        )
    @ENVMod.register(section_name='AMIClient', cast={'events': str})
    def __init__(
            self,
            host: Optional[str] = None,
            port: Optional[int] = None,
            username: Optional[str] = None,
            secret: Optional[str] = None,
            auth_type: Optional[Literal['plain', 'MD5']] = None,
            key: Optional[str] = None,
            events: Optional[Union[Literal['on', 'off'], list[str]]] = None,
            timeout: Optional[int] = None,
            socket_buffer: Optional[int] = None,
        ) -> None:
        """
        A client for interacting with the Asterisk Manager Interface (AMI) over a socket connection.

        Handles authentication, event listening in a background thread, and provides methods
        to manage the connection and interaction lifecycle.

        Attributes:
            registry (Registry): Registry object used to manage and dispatch AMI operations.

        Args:
            host (str): Hostname or IP address of the AMI server.
            port (int): TCP port to connect to.
            username (Optional[str]): AMI username.
            secret (Optional[str]): AMI password.
            auth_type (Optional[Literal['plain', 'MD5']]): Authentication method.
            key (Optional[str]): Challenge key, used for MD5 authentication.
            events (Optional[Union[Literal['on', 'off'], list[str]]]): Event subscriptions or list.
            timeout (int): Socket connection timeout in seconds.
            socket_buffer (int): Size of buffer for reading socket data.
        """
        self._host = host or '127.0.0.1'
        self._port = port or 5038
        self._username = username
        self._secret = secret
        self._auth_type = auth_type
        self._key = key
        self._events = events
        self._timeout = timeout or 3
        self._socket_buffer = socket_buffer or 2048

        self._lock = threading.Lock()
        self._pending_actions: Dict[int, PendingAction] = {}

        self._event_dispatcher = EventDispatcher()
        self._event_queue = queue.Queue()

        self.whitelist: Set[Type[Operation]] = set()
        self.blacklist: Set[Type[Operation]] = set()


    @suppress_errors(False)
    def is_connected(self) -> bool:
        """
        Check whether the client socket is still connected.

        Returns:
            bool: True if connected, False if any socket error occurs.
        """
        if hasattr(socket, 'MSG_DONTWAIT'): 
            _ = self._socket.send(b'', socket.MSG_DONTWAIT)  # type: ignore
        else: self._socket.send(b'')
        return True

    @logwrap(
            before=False,
            on_exception=False,
            after=(logging.DEBUG, 'Checking authentication: {result}'),
            logger=logger,
    )
    @suppress_errors(False)
    def is_authenticated(self) -> bool:
        """
        Check whether the client is authenticated with the AMI server.

        Returns:
            bool: True if authenticated, False otherwise.
        """
        self.send_action(
            Ping(),
            check_connection=False,
            check_authentication=False,
        )
        return True


    @logwrap(
            before='Connecting to server...',
            on_exception='Error while connecting to server: {e}',
            after='Connected to server',
            logger=logger,
        )
    def connect(self) -> None:
        """Establish a TCP connection to the AMI server and start the dispatcher and listener thread."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self._timeout)
    
        self._listen_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self._event_dispatcher_thread = threading.Thread(
            target=self._event_dispatcher_loop, daemon=True
        )

        self._socket.connect((self._host, self._port))

        self._event_dispatcher_thread.start()
        self._listen_thread.start()

    @logwrap(
            before='Disconnecting from server...',
            on_exception='Error while disconnecting to server: {e}',
            after='Disconnected from server',
            logger=logger,
        )
    def disconnect(self) -> None:
        """
        Close the socket connection and stop the listening thread safely.
        Also logs out if authenticated.
        """
        self._socket.close()

        if not threading.current_thread() == self._listen_thread:
            self._listen_thread.join()


    def _operation_factory(self, operation_dict: Dict[str, Any]) -> Operation | None:
        # Determine operation class using key-priority map
        for key, op_map in self.full_map:
            if key in operation_dict:
                operation_class = op_map.get(operation_dict[key], NotImplementedOperation)
                break

        else:
            raise ValueError('Parsed unknown data from server')

        # Whitelist and Blacklist filtering
        if self.whitelist and not any(issubclass(operation_class, cls) and operation_class != cls for cls in self.whitelist): return
        if self.blacklist and     any(issubclass(operation_class, cls) or  operation_class == cls for cls in self.blacklist): return

        return operation_class(**operation_dict)

    @logwrap(
            before='Starting `event_dispatcher_loop`',
            on_exception='Error in `event_dispatcher_loop`: {e}',
            after='`event_dispatcher_loop` stoped',
            logger=logger,
        )
    def _event_dispatcher_loop(self) -> None:
        """Worker thread: consumes events from queue and calls handlers."""
        while self.is_connected():
            try:
                # Wait for event, timeout allows checking stop_event periodically
                operation = self._event_queue.get(timeout=self._timeout)
            except queue.Empty:
                continue

            try:
                self._event_dispatcher.dispatch(operation)
            except Exception:
                logger.error(
                    f"Error while dispatching event: <{getattr(operation, 'Event', None)}>\n"
                    f"{traceback.format_exc()}"
                )
            finally:
                self._event_queue.task_done()

    @logwrap(
            before='Starting `_listener_loop`',
            on_exception='Error in `_listener_loop`: {e}',
            after='`_listener_loop` stoped',
            logger=logger,
        )
    def _listener_loop(self) -> None:
        """
        Internal method that runs in a separate thread to continuously receive and
        decode messages from the AMI server.
        """
        buffer = b''

        while self.is_connected():
            try:
                data = self._socket.recv(self._socket_buffer)
            except TimeoutError:
                time.sleep(self._timeout)
                continue

            except OSError as e:
                if EXCEPTED_OS_ERROR in str(e): continue
                raise
            
            except Exception:
                self.disconnect()
                logger.error(f"Error while receiving data from server:\n{traceback.format_exc()}")
                break

            buffer += data

            while b'\r\n\r\n' in buffer:
                raw_operation, buffer = buffer.split(b'\r\n\r\n', 1)

                try:
                    decoded_operation = raw_operation.decode("utf-8", errors="ignore")
                    operation = self._operation_factory(
                        Operation.parse_raw(decoded_operation)
                    )
                except Exception:
                    logger.error(
                        f"Error while creating Operation object:\n{traceback.format_exc()}"
                    )
                    continue

                if operation is None:
                    logger.debug(
                        f"Operation blocked: <{decoded_operation[0:60].replace('\r\n', ' ')}...>"
                    )
                    continue

                if isinstance(operation, Event):
                    self._event_queue.put(operation, block=False)

                if isinstance(operation, Response):
                    with self._lock:
                        pending = self._pending_actions.get(operation.ActionID)
                        if pending:
                            pending.set_response(operation)


    @logwrap(
        before=False,
        on_exception=False,
        after='New Function registered for dispatching: {kwargs}',
        logger=logger,
    )
    def on_event(self, event: Type[Event]):
        """
        Decorator to register an event handler.

        Usage:
            @client.on_event(Hangup)
            def handler(event): ...

            @client.on_event(NewExten)
            def handler(event): ...
        """
        def decorator(func: Callable[[Event], None]):
            self._event_dispatcher.register(event, func)
            return func

        return decorator

    @logwrap(
        before='Sending action: {kwargs}',
        on_exception='Error while sending action: {kwargs} error: {e}',
        after='Action sent: {kwargs}',
        logger=logger,
    )
    def send_action(
            self,
            action: Action,
            check_connection: bool = True,
            check_authentication: bool = True,
            close_connection: bool = False,
        ) -> PendingAction:
        pending = PendingAction(action)
        
        with self._lock:
            self._pending_actions[action.ActionID] = pending

        if check_connection:
            self.connect() if not self.is_connected() else None

        if check_authentication:
            self.login() if not self.is_authenticated() else None

        self._socket.sendall(action.to_raw().encode())

        if close_connection:
            self.disconnect()

        return pending


    @logwrap(
        before='Login to server',
        on_exception='Error while login: {e}',
        after='Login completed',
        logger=logger,
    )
    def login(self) -> Response:
        """
        Authenticate with the AMI server using the provided credentials.

        Returns:
            Response: The response received from the server after login attempt.
        """
        return self.send_action(
            Login(
                Username = self._username,
                Secret = self._secret,
                AuthType = cast(Optional[Literal['plain', 'MD5']], self._auth_type),
                Key = self._key,
                Events = cast(Optional[Union[Literal['on', 'off'], list[str]]], self._events),
            ),
            check_authentication=False,
        ).wait(self._timeout)

    @logwrap(
        before='Logoff from server',
        on_exception='Error while Logoff: {e}',
        after='Logoff Completed',
        logger=logger,
    )
    def logoff(self) -> None:
        """
        Send a logoff command to the AMI server if currently authenticated.

        Returns:
            Response | None: The logoff response or None if not authenticated.
        """
        self.send_action(
            Logoff(),
            close_connection=True,
        )

    @logwrap(
        before=False,
        on_exception=False,
        after='Added Events to whitelist: {kwargs}',
        logger=logger,
    )
    def add_whitelist(self, events: List[Type]) -> None:
        """
        Add item types to the whitelist.

        Args:
            events (List[Type]): A list of operation types to allow.
        """
        for event in events:
            self.whitelist.add(event)

    @logwrap(
        before=False,
        on_exception=False,
        after='Added Events to blacklist: {kwargs}',
        logger=logger,
    )
    def add_blacklist(self, events: List[Type]) -> None:
        """
        Add item types to the blacklist.

        Args:
            events (List[Type]): A list of operation types to block.
        """
        for event in events:
            self.blacklist.add(event)

    @logwrap(
        before=False,
        on_exception=False,
        after='Removed Events from whitelist: {kwargs}',
        logger=logger,
    )
    def remove_whitelist(self, events: List[Type]) -> None:
        """
        Remove item types from the whitelist.

        Args:
            events (List[Type]): A list of operation types to remove.
        """
        for event in events:
            self.whitelist.remove(event)

    @logwrap(
        before=False,
        on_exception=False,
        after='Removed Events from blacklist: {kwargs}',
        logger=logger,
    )
    def remove_blacklist(self, events: List[Type]) -> None:
        """
        Remove item types from the blacklist.

        Args:
            events (List[Type]): A list of operation types to remove.
        """
        for event in events:
            self.whitelist.remove(event)


    def __enter__(self) -> Self:
        self.connect()
        self.login()
        return self

    def __exit__(self, type, value, traceback) -> None:
        self.logoff()
        self.disconnect()


    def __str__(self) -> str:
        return f'<AMIClient {self._host}:{self._port}>'
    
    def __repr__(self) -> str:
        return f'AMIClient(host={self._host}, port={self._port})'