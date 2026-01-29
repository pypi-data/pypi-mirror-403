import socketio
import uuid
import inspect
import asyncio
import logging

from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Callable, Coroutine, Union, Any, Dict, List
from socketio.exceptions import ConnectionError

from . import enums
from . import types
from .addons import ui
from .addons import color

logger = logging.getLogger("wokkichat")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    logger.addHandler(ch)

async def get_response(bot: "Bot", event: str, payload: types.JSON = {}, is_special: bool = False) -> types.JSON:
    if not bot.connected:
        logger.error("Please connect before trying to fetch remote data!")
        return {}
    
    if not bot._loop: return {}
    fut = bot._loop.create_future()

    req_id = str(uuid.uuid4())
    payload["req_id"] = req_id
    bot._response_futures[(is_special and "_" or '') + req_id] = fut

    await bot._sio.emit(event, payload)

    try:
        return await asyncio.wait_for(fut, timeout=5)
    except asyncio.TimeoutError:
        logger.error("Response future timeout!")
        fut.cancel()
        return {}
    finally:
        bot._response_futures.pop((is_special and "_" or '') + req_id, None)


@dataclass
class TypingInfo: # TODO add autorefresh (using @property?)
    """
    Contains valuable information about a typing user.

    No default values because if the data is invalid,
    you wouldn't get an object of this class.
    """

    _bot: "Bot"
    server_id: str
    """
    The id of the server this user is typing in.
    """
    channel_id: str
    """
    The channel id this user is typing in.
    """
    user_id: types.UserId
    """
    The id of the user which is typing.
    """
    when: datetime
    """
    When this user started typing.
    """

    def __init__(self, bot: "Bot", server_id: str, channel_id: str, user_id: types.UserId, when: datetime):
        """
        @private
        """
        self._bot = bot

        self.server_id = server_id
        self.channel_id = channel_id
        self.user_id = user_id
        self.when = when

    async def get_user(self) -> "User":
        """
        Returns the User associated with this TypingInfo.
        """
        return await self._bot.get_user(self.user_id)


@dataclass
class User:
    """
    Represents a user or bot account on wokki chat.
    """

    id: types.UserId
    """
    The id of the user.
    
    Int if it's a real user, or uuid string if it's a bot.
    """
    username: str
    """
    The username of the user.
    """
    display_name: str
    """
    The display name of the user.
    """
    bio: str
    """
    The bio of the user.
    """
    status: enums.status
    """
    The current active status of the user.
    """
    profile_picture: str
    """
    The *relative* url of the user's pfp.
    """
    profile_banner: str
    """
    The *relative* url of the user's banner image.
    """
    premium: bool
    """
    Whether the user owns premium or not.
    """
    bot: bool
    """
    Whether the user is a bot or not.
    """
    staff: bool
    """
    Whether the user is an official staff member or not.
    """
    developer: bool
    """
    Whether the user is an official developer or not.
    """
    created_at: datetime
    """
    The moment the account got created.
    """

    def __init__(self, bot: "Bot", data: types.JSON):
        """
        @private
        """
        self._bot = bot
        self._update(data)

    def _update(self, data: types.JSON) -> None:
        if not isinstance(data, dict): return
        
        self.id: types.UserId = data.get('id', 0)
        self.username: str = data.get('username', '')
        self.display_name: str = data.get('display_name', '')
        self.bio: str = data.get('bio', '')
        self.status: enums.status = enums.status[data.get('status', 'offline').upper()]
        self.profile_picture: str = data.get('profile_picture', '/uploads/profile-pictures/default-profile.png')
        self.profile_banner: str = data.get('profile_banner', '')
        self.premium: bool = data.get('premium', False)
        self.bot: bool = data.get('bot', False)
        self.staff: bool = data.get('staff', False)
        self.developer: bool = data.get('developer', False)
        self.created_at: datetime = datetime.fromisoformat(
            data.get('created_at', '1970-01-01T00:00:00'))
        
        # TODO Add these items
        # tags? [{tag_name:"staff", tag_icon:"tag_staff", created_at:ISO}]
        # profile_color_primary? #0f1221
        # profile_color_accent? #0f1221
        # widgets? {}

    async def is_typing(self) -> Optional[TypingInfo]:
        """
        Returns the current typing info of the user, if available.
        """
        return await self._bot.is_typing(self.id)


@dataclass
class Message:
    """
    Represents a message sent by a user.
    """

    username: str
    """
    The username of the user which sent this message.
    """
    user_id: str
    """
    The id of the user which sent this message.
    """
    profile_picture: str
    """
    The *relative* url of the user's pfp.
    """
    id: str
    """
    The id of the message.
    """
    bot_message: bool
    """
    Whether the message was sent by a bot or not.
    """
    message: str
    """
    The content text of the message.
    """
    created_at: datetime
    """
    When the message was sent.
    """
    channel: "Channel"
    """
    The channel the message was sent in.
    """
    parent_message_id: Optional[str]
    """
    The id of the parent message, if this message is a reply.
    """
    assets: List[str]
    """
    A list of all assets atached to this message.
    Defaults to an empty list.

    Not officially supported yet.
    """
    command: Optional[str]
    """
    The command name which this message replies to,
    if this message is a command response.
    """
    command_user_id: Optional[types.UserId]
    """
    The user id of the user which used this command,
    if this message is a command response.
    """

    def __init__(self, bot: "Bot", data: types.JSON):
        """
        @private
        """
        self._bot: Bot = bot

        # TODO wrap in user object?
        self.username = data.get('username', '')
        self.user_id = data.get('user_id', 0)
        self.profile_picture = data.get('profile_picture', '/uploads/profile-pictures/default-profile.png')

        self.id = data.get('id', '')
        self.bot_message = bool(data.get('bot_message', 0))
        self.message = data.get('message', '')
        self.created_at = datetime.fromisoformat(
            data.get('created_at', '1970-01-01T00:00:00'))
        self.channel = Channel(bot, data.get('server_id', ''), data.get('channel_id', ''))
        self.parent_message_id = data.get('parent_message_id', '') # TODO make real message?
        self.assets = data.get('assets', [])  # TODO wrap in Image classes?
        self.command = data.get('command', None)
        self.command_user_id = data.get('command_user_id', 0)
        # TODO how to convert 'embed' to view?

    async def get_user(self) -> "User":
        """
        Returns the User associated with this Message.
        """
        return await self._bot.get_user(self.user_id)

    async def reply(self, message: Optional[str] = "", view: Optional[ui.View] = None) -> Optional["Message"]:
        """
        Replies to this message with another message.

        :param message: The message text to send.
        :param view: The view to send.
        """
        if not self.channel: return # should never happen, but it makes our type checker happy
        return await self._bot.send_message(self.channel.server.id, self.channel.id, parent_message_id=self.id, message=message, view=view)


@dataclass
class Server: # add get_channel or something later?
    """
    Represents a server on Wokki Chat.
    """

    id: str
    """
    The id of the server.
    """

    def __init__(self, id: str):
        """
        @private
        """
        self.id = id


class Channel:
    """
    Represents a channel on Wokki Chat.
    """

    id: str
    """
    The id of the channel.
    """
    server: Server
    """
    The server which owns this channel.
    """

    def __init__(self, bot: "Bot", server_id: str, channel_id: str):
        """
        @private
        """
        self._bot: Bot = bot

        self.id = channel_id
        self.server = Server(server_id)

    async def send_message(self, message: Optional[str] = "", view: Optional[ui.View] = None) -> Optional[Message]:
        """
        Sends a message in the channel.

        :param message: The message text to send.
        :param view: The view to send.
        """
        return await self._bot.send_message(self.server.id, self.id, message=message, view=view)


class ctx:
    """
    Special context shared in bot commands.
    """

    command: str
    """
    The name of the used command.
    """
    user: "User"
    """
    The user that used the command.
    """
    channel: "Channel"
    """
    The channel the command was used in.
    """

    def __init__(self, t: types.JSON):
        """
        @private
        """
        self._bot: Bot = t["bot"]
        self.command = t["command"]
        self.user = t["user"]
        self.channel = t["channel"]

    async def reply(self, message: Optional[str] = "", view: Optional[ui.View] = None) -> Optional[Message]:
        """
        Responds to this command with a message.

        :param message: The message text to send.
        :param view: The view to send.
        """
        return await self._bot.send_message(
            self.channel.server.id, self.channel.id, message=message, view=view,
            command=self.command, command_user_id=self.user.id
            )

class Bot:
    """
    The main class of this library.
    From this class you can manage everything.
    """

    bot_token: str
    """
    The token of your bot.
    """
    server_id: Optional[str]
    """
    The server id to connect with (optional).
    If None, the bot will connect globally.
    """
    connected: bool
    """
    Wether the bot is connected or not.
    """

    def __init__(self, bot_token: str, server_id: Optional[str] = None):
        self.bot_token = bot_token
        self.server_id = server_id
        self.connected = False
        # self.button_handler: Callable = None # TODO add button handler logic

        self._sio: socketio.AsyncClient = socketio.AsyncClient()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._reconnect_scheduled = False
        self._response_futures: Dict[str, asyncio.Future] = {}
        self._events: Dict[str, Callable] = {}
        self._commands: Dict[str, Callable] = {}
        self._typing_cache = {}

        @self._sio.on('connect') # pyright: ignore[reportOptionalCall]
        async def on_connect():
            await asyncio.sleep(5)
            if not self.connected:
                logger.error("Server is active but broken, please report to a developer!")

        @self._sio.on('bot_connected') # pyright: ignore[reportOptionalCall]
        async def on_bot_connect(data: types.JSON):
            # we were already connected but we need this to confirm our own identity
            logger.info("Connected!")
            # logger.debug((await self.get_user(data.get('bot_id', 0))).username)

            event = self._events.get("on_ready")
            if event:
                await event()

        @self._sio.on('error') # pyright: ignore[reportOptionalCall]
        async def on_error(data: types.JSON):
            logger.error("Server error:", data)

        async def on_send_response(data: types.JSON):
            req_id = data.get('req_id')
            if req_id and req_id in self._response_futures:
                fut = self._response_futures.pop(req_id)
                if fut != None:
                    fut.set_result(data)

        self._sio.on('1', on_send_response)
        self._sio.on('user_info', on_send_response)
        self._sio.on('send_message_response', on_send_response)

        @self._sio.on('bot_command_received') # pyright: ignore[reportOptionalCall]
        async def on_bot_command_received(data: types.JSON):
            c = data.get('command', 'nonexisting')
            command = self._commands.get(c[1:])

            if command:
                context = ctx({
                    "command": c,
                    "bot": self,
                    "user": await self.get_user(data.get('sent_by_user_id', 0)),
                    "channel": Channel(self, data.get("server_id", ''), data.get("channel_id", ''))
                })
                await command(context, **data.get("options", {}))

        # @self._sio.on('embed_button_pressed') # pyright: ignore[reportOptionalCall]
        # async def on_button_click_received(data: types.JSON):
        #     if self.button_handler:
        #         await self.button_handler(data)

        @self._sio.on('user_updated') # pyright: ignore[reportOptionalCall]
        async def on_user_updated(data: types.JSON):
            event = self._events.get("on_user_updated")
            if event:
                user = User(self, data)
                await event(user)

        @self._sio.on('users_typing') # pyright: ignore[reportOptionalCall]
        async def on_typing_updated(data: types.JSON):
            server_id = data.get('server_id')
            channel_id = data.get('channel_id')
            if server_id and channel_id:
                server = self._typing_cache.get(server_id)
                if not server:
                    self._typing_cache[server_id] = {}
                    server = self._typing_cache[server_id]

                old = server.get(channel_id)
                if not old:
                    server[channel_id] = {}
                    old = server[channel_id]

                server[channel_id] = {}
                channel = server[channel_id]

                user_ids = data.get('user_ids', [])
                event = self._events.get("on_typing")
                for id in user_ids:
                    if old.get(id):
                        channel[id] = old[id]
                    else:
                        channel[id] = datetime.now()

                    if event:
                        await event(TypingInfo(self, server_id, channel_id, id, channel[id]))

        @self._sio.on('new_message') # pyright: ignore[reportOptionalCall]
        async def on_new_message(data: types.JSON):
            req_id = "_" + data.get('req_id', '')
            if req_id in self._response_futures:
                fut = self._response_futures.pop(req_id)
                if fut != None:
                    fut.set_result(data)

            event = self._events.get("on_message")
            if event:
                # TODO add check whether message isn't your own here!
                await event(Message(self, data))

        @self._sio.on("*") # pyright: ignore[reportOptionalCall]
        async def catch_all(event, data: types.JSON):
            if event == "user_widget_updated": return # silence annoying spam message; TODO support it
            logger.debug(f"Unhandled event: {event} -> {data}")

    def event(self, func: Callable):
        """
        Binds a function to an event.

        :param func: The function to be called when the event fires.
        This function must be async!
        """

        if not inspect.iscoroutinefunction(func):
            raise RuntimeError("@bot.event must be async!")
        
        allowed = ["on_ready", "on_message", "on_user_updated", "on_typing"]
        if func.__name__ not in allowed:
            raise RuntimeError(f"{func.__name__} not valid for @bot.event")
        
        self._events[func.__name__] = func
        return func

    def command(self, name: Optional[str] = None):
        """
        Binds a function to a command.

        :param func: The function to be called when the command is used.
        This function must be async!
        """
        def decorator(func):
            if self.connected:
                # this is actually not needed?
                # the only issue is the commands are only passed through when starting
                raise RuntimeError(f"Commands must be added BEFORE calling bot.connect()")

            if not inspect.iscoroutinefunction(func):
                raise RuntimeError(f"@bot.command() must be async")

            cmd_name = name or func.__name__
            if not cmd_name or type(cmd_name) != str:
                raise RuntimeError(f"Command name is invalid for command \"{cmd_name}\"")

            self._commands[cmd_name] = func
            return func
        return decorator

    def connect(self):
        """
        Official method to connect.
        Before calling this function, no events
        or commands will ever fire.

        This function blocks the current thread **forever**.
        """
        asyncio.run(self._main())

    async def _main(self):
        await self._async_connect()
        await asyncio.Event().wait()

    async def _async_connect(self):
        """
        Not officially supported method to connect the bot
        in async. Bot.connect() is a sync wrapper
        of this method.

        When using, make sure to keep the thread alive after
        it finishes, or the connection will close itself.

        @public
        """
        self._loop = asyncio.get_running_loop()
        url = f"https://chat.wokki20.nl?bot_token={self.bot_token}"
        if self.server_id:
            url += f"&server_id={self.server_id}"

        max_attempts = 3 # 3 attempts to connect, for if the server is down
        for attempt in range(1, max_attempts + 1):
            try:
                await self._sio.connect(url, socketio_path='/socket.io', transports=['websocket'])
                self.connected = True
                break
            except (ConnectionError, OSError):
                if attempt < max_attempts:
                    logger.error(f"Connection failed, retrying ({attempt}/{max_attempts})...")
                    await asyncio.sleep(3)
                else:
                    logger.error("Server appears to be down. Checking again in 10 minutes.")
                    if not getattr(self, "_reconnect_scheduled", False):
                        self._reconnect_scheduled = True
                        self._loop.create_task(self._delayed_reconnect())
                    return

        if self._commands:
            class_types = {
                str: "string",
                int: "number",
                bool: "boolean"
            }

            commands_data = []
            for name, func in self._commands.items():
                sig = inspect.signature(func)
                options = []

                gotctx = False
                for pname, param in sig.parameters.items():
                    if not gotctx:
                        gotctx = True
                        continue

                    if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                        continue

                    options.append({
                        "option_name": pname,
                        "option_type": class_types.get(param.annotation, "string"),
                        "required": param.default == inspect._empty
                    })

                commands_data.append({
                    "command": f"/{name}" if not name.startswith("/") else name,
                    "options": options
                })

            await self._sio.emit('initialize_commands', {
                'commands': commands_data,
                'bot_token': self.bot_token
            })
        else:
            await self._sio.emit('initialize_commands', {
                'commands': [],  # clear up old commands
                'bot_token': self.bot_token
            })

    async def _delayed_reconnect(self):
        await asyncio.sleep(600)
        self._reconnect_scheduled = False
        await self._async_connect()

    async def disconnect(self):
        """
        Disconnects the current bot
        session from the server.
        """
        if self.connected:
            await self._sio.disconnect()
            self.connected = False

    async def get_user(self, user_id: types.UserId) -> User:
        """
        Low-level implementation to get the info of
        a user by their id.

        :param user_id: The id of the user you want to fetch.
        :raises RuntimeError: If the user couldn't be fetched.
        """
        payload = {
            'bot_token': self.bot_token,
            'user_id': user_id
        }

        data = await get_response(self, 'get_user_info', payload=payload)
        if data.get("info"):
            return User(self, data["info"])
        else:
            raise RuntimeError(f'Couldn\'t fetch user with id "{user_id}"')
        
    async def is_typing(self, user_id: types.UserId) -> Optional[TypingInfo]:
        """
        Low-level implementation to get the typing info of
        a user by their id.

        :param user_id: The id of the user you want info of.
        """
        result = None
        for server_id, channels in self._typing_cache.items():
            for channel_id, users in channels.items():
                if user_id in users:
                    result = TypingInfo(self, server_id, channel_id, user_id, users[user_id])
        return result

    async def send_message(
            self, server_id: str, channel_id: str, parent_message_id: Optional[str] = None,
            message: Optional[str] = "", view: Optional[ui.View] = None,
            command: Optional[str] = None, command_user_id: Optional[types.UserId] = None
            ) -> Optional[Message]:
        """
        Low-level implementation to send a message.

        :param message: The message text to send.
        :param view: The view to send.
        """
        if not message and not view:
            logger.error("Please pass either a message or a view in Bot.send_message()")
            return

        payload = {
            'message': message,
            'server_id': server_id,
            'channel_id': channel_id,
            'parent_message_id': parent_message_id,
            'bot_token': self.bot_token,
            'embed': view.to_list() if view else None,
            'command': command,
            'user_id': command_user_id
        }

        data = await get_response(self, 'send_message', payload=payload, is_special=True)
        if not data: return

        return Message(self, data)

    async def edit_message(self, message_id: str, message: Optional[str] = "", view: Optional[ui.View] = None):
        """
        Low-level implementation to edit a message.

        :param message: The message text to send.
        :param view: The view to send.
        """

        # TODO Fix server side and cast return to bool
        if not message and not view:
            logger.error("Please pass either a message or a view in Bot.edit_bot_message()")
            return

        payload = {
            'message_id': message_id,
            'message': message,
            'embed': view.to_list() if view else None,
            'bot_token': self.bot_token
        }

        return await get_response(self, 'edit_bot_message', payload=payload)
