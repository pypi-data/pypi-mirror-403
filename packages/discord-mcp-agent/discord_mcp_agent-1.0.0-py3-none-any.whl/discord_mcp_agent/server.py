"""Discord MCP Agent - MCP server for Discord-based AI agent-user communication."""

import asyncio
import base64
import io
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiohttp
import discord
from discord import Intents, File
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent

# Optional: for screenshots
try:
    from PIL import ImageGrab
    HAS_SCREENSHOT = True
except ImportError:
    HAS_SCREENSHOT = False

# =============================================================================
# Constants
# =============================================================================

# Timeouts (in seconds)
DEFAULT_CONNECTION_TIMEOUT = 30.0
DEFAULT_ASK_TIMEOUT = 300.0  # 5 minutes
DEFAULT_HTTP_TIMEOUT = 30.0

# Discord colors
DISCORD_BLURPLE = 0x5865F2

# Reaction emojis
EMOJI_SCREENSHOT = "\U0001F4F7"  # 📷 Camera
EMOJI_CANCEL = "\u274C"          # ❌ Cancel
EMOJI_LOADING = "\u23F3"         # ⏳ Hourglass

# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("discord-mcp-agent")


# =============================================================================
# Configuration
# =============================================================================

def get_config() -> dict:
    """Load configuration from environment variables."""
    token = os.getenv("DISCORD_TOKEN")
    guild_id = os.getenv("DISCORD_GUILD_ID", "0")
    channel = os.getenv("DISCORD_CHANNEL", "general")
    
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable is required.")
    if not guild_id or guild_id == "0":
        raise ValueError("DISCORD_GUILD_ID environment variable is required.")
    
    return {
        "TOKEN": token,
        "GUILD_ID": int(guild_id),
        "CHANNEL_NAME": channel,
    }


# Configurable reminder - users can set their own via env var
DISCORD_REMINDER = os.getenv("DISCORD_REMINDER", "")

# Configurable timeouts via env vars
ASK_TIMEOUT = float(os.getenv("DISCORD_ASK_TIMEOUT", str(DEFAULT_ASK_TIMEOUT)))
HTTP_TIMEOUT = float(os.getenv("DISCORD_HTTP_TIMEOUT", str(DEFAULT_HTTP_TIMEOUT)))
CONNECTION_TIMEOUT = float(os.getenv("DISCORD_CONNECTION_TIMEOUT", str(DEFAULT_CONNECTION_TIMEOUT)))


# =============================================================================
# Discord Agent
# =============================================================================

# Global singleton for persistent connection
_discord_agent: Optional["DiscordAgent"] = None


class DiscordAgent:
    """Discord communication handler with persistent connection.
    
    Features:
    - Singleton pattern for persistent Discord connection
    - Reaction-based interactions (📷 screenshot, ❌ cancel)
    - Configurable timeouts for all operations
    - Image attachment handling with base64 encoding
    """
    
    def __init__(self, config: dict):
        self.token = config["TOKEN"]
        self.guild_id = config["GUILD_ID"]
        self.channel_name = config["CHANNEL_NAME"]
        
        self._client: Optional[discord.Client] = None
        self._channel: Optional[discord.TextChannel] = None
        self._response_event = asyncio.Event()
        self._cancel_event = asyncio.Event()
        self._response: Optional[str] = None
        self._response_attachments: list[dict] = []
        self._ready_event = asyncio.Event()
        self._connection_error: Optional[Exception] = None
        self._bot_task: Optional[asyncio.Task] = None
        self._connected = False
        self._last_bot_message: Optional[discord.Message] = None
    
    @classmethod
    async def get_instance(cls) -> "DiscordAgent":
        """Get or create the singleton Discord agent instance."""
        global _discord_agent
        if _discord_agent is None:
            config = get_config()
            _discord_agent = cls(config)
            await _discord_agent.connect()
        elif not _discord_agent._connected:
            await _discord_agent.connect()
        return _discord_agent
    
    async def is_healthy(self) -> bool:
        """Check if the Discord connection is still alive."""
        if not self._client or self._client.is_closed():
            return False
        if not self._channel:
            return False
        return self._connected
    
    async def connect(self) -> None:
        """Establish connection to Discord with timeout."""
        intents = Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.reactions = True
        
        self._client = discord.Client(intents=intents)
        self._response_event = asyncio.Event()
        self._cancel_event = asyncio.Event()
        self._ready_event = asyncio.Event()
        self._connection_error = None
        
        @self._client.event
        async def on_ready():
            try:
                guild = self._client.get_guild(self.guild_id)
                if not guild:
                    self._connection_error = ValueError(f"Guild with ID {self.guild_id} not found.")
                    self._ready_event.set()
                    return
                
                self._channel = discord.utils.get(guild.text_channels, name=self.channel_name)
                if not self._channel:
                    self._connection_error = ValueError(f"Channel '{self.channel_name}' not found in guild.")
                    self._ready_event.set()
                    return
                
                logger.info(f"Connected to Discord: {guild.name} / #{self.channel_name}")
                self._connection_error = None
                self._ready_event.set()
            except Exception as e:
                self._connection_error = e
                self._ready_event.set()
        
        @self._client.event
        async def on_message(message: discord.Message):
            # Ignore bot's own messages
            if message.author == self._client.user:
                return
            # Only process messages from our channel
            if message.channel.name != self.channel_name:
                return
            if message.guild and message.guild.id != self.guild_id:
                return
            
            self._response = message.content
            self._response_attachments = [
                {
                    "filename": att.filename,
                    "url": att.url,
                    "content_type": att.content_type,
                    "size": att.size
                }
                for att in message.attachments
            ]
            self._response_event.set()
        
        @self._client.event
        async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
            # Ignore bot's own reactions
            if user == self._client.user:
                return
            
            # Only process reactions on our last message
            if not self._last_bot_message:
                return
            if reaction.message.id != self._last_bot_message.id:
                return
            
            emoji = str(reaction.emoji)
            
            # 📷 Screenshot reaction
            if emoji == EMOJI_SCREENSHOT:
                logger.info("Screenshot requested via reaction")
                await self.send_screenshot("📸 Screenshot (via reaction)")
            
            # ❌ Cancel reaction
            elif emoji == EMOJI_CANCEL:
                logger.info("Cancel requested via reaction")
                self._response = "[CANCELLED]"
                self._cancel_event.set()
                self._response_event.set()
        
        # Start the bot
        self._bot_task = asyncio.create_task(self._client.start(self.token))
        
        # Wait for ready with timeout
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=CONNECTION_TIMEOUT)
        except asyncio.TimeoutError:
            await self.disconnect()
            raise ConnectionError(f"Failed to connect to Discord within {CONNECTION_TIMEOUT} seconds")
        
        # Check for connection errors
        if self._connection_error:
            await self.disconnect()
            raise self._connection_error
        
        self._connected = True
    
    async def disconnect(self) -> None:
        """Gracefully disconnect from Discord."""
        self._connected = False
        if self._client and not self._client.is_closed():
            await self._client.close()
        if self._bot_task:
            self._bot_task.cancel()
            try:
                await self._bot_task
            except asyncio.CancelledError:
                pass
        logger.info("Disconnected from Discord")
    
    async def ask(self, question: str, timeout: Optional[float] = None) -> dict:
        """Ask a question and return response with any attachments.
        
        Args:
            question: The question to ask the user
            timeout: Maximum seconds to wait (default: ASK_TIMEOUT env var or 300s)
        
        Returns:
            Dict with 'text', 'attachments', and 'cancelled' keys
            
        Raises:
            asyncio.TimeoutError: If no response within timeout
        """
        timeout = timeout or ASK_TIMEOUT
        
        # Clear previous state
        self._response_event.clear()
        self._cancel_event.clear()
        self._response = None
        self._response_attachments = []
        
        # Send the question
        msg = await self._channel.send(question)
        self._last_bot_message = msg
        
        # Add reaction buttons
        await msg.add_reaction(EMOJI_SCREENSHOT)  # 📷 Screenshot
        await msg.add_reaction(EMOJI_CANCEL)      # ❌ Cancel
        
        # Wait for response or cancel with timeout
        try:
            await asyncio.wait_for(self._response_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            await msg.add_reaction(EMOJI_LOADING)  # ⏳ Show timeout indicator
            raise asyncio.TimeoutError(f"No response received within {timeout} seconds")
        
        # Check if cancelled
        if self._cancel_event.is_set():
            return {
                "text": "[User cancelled the request]",
                "attachments": [],
                "cancelled": True
            }
        
        return {
            "text": self._response,
            "attachments": self._response_attachments,
            "cancelled": False
        }
    
    async def notify(self, message: str) -> None:
        """Send a notification (no response expected)."""
        msg = await self._channel.send(message)
        self._last_bot_message = msg
        await msg.add_reaction(EMOJI_SCREENSHOT)  # 📷 Screenshot option
    
    async def download_attachment(self, url: str, timeout: Optional[float] = None) -> tuple[bytes, str]:
        """Download an attachment and return (data, content_type).
        
        Args:
            url: The attachment URL
            timeout: Maximum seconds for download (default: HTTP_TIMEOUT)
            
        Returns:
            Tuple of (bytes, content_type)
        """
        timeout = timeout or HTTP_TIMEOUT
        timeout_settings = aiohttp.ClientTimeout(total=timeout)
        
        async with aiohttp.ClientSession(timeout=timeout_settings) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    content_type = resp.headers.get('Content-Type', 'application/octet-stream')
                    return data, content_type
                raise ValueError(f"Failed to download attachment: HTTP {resp.status}")
    
    async def send_file(self, file_path: str, message: str = "") -> bool:
        """Send a file to Discord.
        
        Args:
            file_path: Absolute path to the file
            message: Optional message to accompany the file
            
        Returns:
            True if successful, False if file not found
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return False
        
        await self._channel.send(content=message if message else None, file=File(path))
        logger.info(f"File sent: {file_path}")
        return True
    
    async def send_screenshot(self, message: str = "") -> dict:
        """Take and send a screenshot to Discord.
        
        Args:
            message: Optional message to accompany the screenshot
            
        Returns:
            Dict with 'success', 'filename' or 'error' keys
        """
        if not HAS_SCREENSHOT:
            return {
                "success": False, 
                "error": "PIL not installed. Run: pip install discord-mcp-agent[screenshot]"
            }
        
        try:
            # Capture screen
            screenshot = ImageGrab.grab()
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            screenshot.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Generate filename
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            # Send to Discord
            await self._channel.send(
                content=message if message else None,
                file=File(img_bytes, filename=filename)
            )
            
            logger.info(f"Screenshot sent: {filename}")
            return {"success": True, "filename": filename}
            
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_embed(
        self,
        title: str = "",
        description: str = "",
        color: int = DISCORD_BLURPLE,
        fields: Optional[list[dict]] = None,
        footer: str = "",
        thumbnail_url: str = "",
        image_url: str = "",
        author_name: str = "",
        url: str = ""
    ) -> dict:
        """Send a rich embed to Discord.
        
        Args:
            title: Embed title
            description: Main description text
            color: Embed color (default: Discord blurple)
            fields: List of field dicts with 'name', 'value', 'inline' keys
            footer: Footer text
            thumbnail_url: Small image in top-right
            image_url: Large image at bottom
            author_name: Author name at top
            url: URL the title links to
            
        Returns:
            Dict with 'success' and optionally 'error' keys
        """
        try:
            embed = discord.Embed(
                title=title or None,
                description=description or None,
                color=color,
                url=url or None
            )
            
            # Add fields
            if fields:
                for field in fields:
                    embed.add_field(
                        name=field.get("name", "Field"),
                        value=field.get("value", ""),
                        inline=field.get("inline", True)
                    )
            
            # Optional components
            if footer:
                embed.set_footer(text=footer)
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            if image_url:
                embed.set_image(url=image_url)
            if author_name:
                embed.set_author(name=author_name)
            
            # Add timestamp
            embed.timestamp = datetime.now()
            
            # Send
            msg = await self._channel.send(embed=embed)
            self._last_bot_message = msg
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Embed failed: {e}")
            return {"success": False, "error": str(e)}


# =============================================================================
# MCP Server
# =============================================================================

server = Server("discord")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Discord tools."""
    return [
        Tool(
            name="discord_ask",
            description="Send a question to the user via Discord and wait for their response. User can react with ❌ to cancel or 📷 for screenshot.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask the user"
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="discord_notify",
            description="Send a notification to the user via Discord. Does not wait for a response.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to send"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="discord_send_file",
            description="Send a file to the user via Discord.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file to send"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional message to accompany the file"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="discord_screenshot",
            description="Take a screenshot of the entire desktop and send it to Discord.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Optional message to accompany the screenshot"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="discord_embed",
            description="Send a rich embed message to Discord with title, description, color, fields, and more.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The embed title"},
                    "description": {"type": "string", "description": "The main embed description/content"},
                    "color": {"type": "integer", "description": "Embed color as integer (e.g., 0xFF0000 for red). Default: Discord blurple"},
                    "fields": {
                        "type": "array",
                        "description": "Array of field objects with 'name', 'value', and optional 'inline' (boolean)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "string"},
                                "inline": {"type": "boolean"}
                            },
                            "required": ["name", "value"]
                        }
                    },
                    "footer": {"type": "string", "description": "Footer text"},
                    "thumbnail_url": {"type": "string", "description": "URL for thumbnail image (small, top-right)"},
                    "image_url": {"type": "string", "description": "URL for main embed image (large, bottom)"},
                    "author_name": {"type": "string", "description": "Author name shown at top of embed"},
                    "url": {"type": "string", "description": "URL that the title links to"}
                },
                "required": []
            }
        ),
    ]


def add_reminder(results: list[TextContent | ImageContent]) -> list[TextContent | ImageContent]:
    """Append the configurable reminder to results if set."""
    if DISCORD_REMINDER:
        results.append(TextContent(type="text", text=f"\n---\n{DISCORD_REMINDER}"))
    return results


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:
    """Handle tool calls from MCP clients."""
    agent = await DiscordAgent.get_instance()
    
    if name == "discord_ask":
        try:
            response = await agent.ask(arguments["question"])
        except asyncio.TimeoutError as e:
            return add_reminder([TextContent(type="text", text=f"⏳ {str(e)}")])
        
        result: list[TextContent | ImageContent] = []
        
        # Check if cancelled
        if response.get("cancelled"):
            return add_reminder([TextContent(type="text", text="❌ User cancelled the request")])
        
        # Add text response
        if response["text"]:
            result.append(TextContent(type="text", text=response["text"]))
        
        # Process attachments
        for att in response["attachments"]:
            content_type = att["content_type"] or ""
            if content_type.startswith("image/"):
                try:
                    image_data, mime_type = await agent.download_attachment(att["url"])
                    image_b64 = base64.b64encode(image_data).decode("utf-8")
                    result.append(ImageContent(
                        type="image",
                        data=image_b64,
                        mimeType=mime_type
                    ))
                except asyncio.TimeoutError:
                    result.append(TextContent(type="text", text=f"[⏳ Timeout downloading {att['filename']}]"))
                except Exception as e:
                    result.append(TextContent(type="text", text=f"[Failed to load image {att['filename']}: {e}]"))
            else:
                result.append(TextContent(type="text", text=f"[Attachment: {att['filename']} - {att['url']}]"))
        
        if not result:
            result.append(TextContent(type="text", text="(empty response)"))
        
        return add_reminder(result)
    
    elif name == "discord_notify":
        await agent.notify(arguments["message"])
        return add_reminder([TextContent(type="text", text="Notification sent")])
    
    elif name == "discord_send_file":
        file_path = arguments["file_path"]
        message = arguments.get("message", "")
        success = await agent.send_file(file_path, message)
        if success:
            return add_reminder([TextContent(type="text", text=f"File sent: {file_path}")])
        else:
            return add_reminder([TextContent(type="text", text=f"Failed to send file: {file_path} (not found)")])
    
    elif name == "discord_screenshot":
        message = arguments.get("message", "")
        result = await agent.send_screenshot(message)
        if result["success"]:
            return add_reminder([TextContent(type="text", text=f"Screenshot sent: {result['filename']}")])
        else:
            return add_reminder([TextContent(type="text", text=f"Screenshot failed: {result['error']}")])
    
    elif name == "discord_embed":
        result = await agent.send_embed(
            title=arguments.get("title", ""),
            description=arguments.get("description", ""),
            color=arguments.get("color", DISCORD_BLURPLE),
            fields=arguments.get("fields"),
            footer=arguments.get("footer", ""),
            thumbnail_url=arguments.get("thumbnail_url", ""),
            image_url=arguments.get("image_url", ""),
            author_name=arguments.get("author_name", ""),
            url=arguments.get("url", "")
        )
        if result["success"]:
            return add_reminder([TextContent(type="text", text="Embed sent successfully")])
        else:
            return add_reminder([TextContent(type="text", text=f"Embed failed: {result['error']}")])
    
    else:
        return add_reminder([TextContent(type="text", text=f"Unknown tool: {name}")])


# =============================================================================
# Entry Points
# =============================================================================

async def main():
    """Async entry point for MCP server."""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting Discord MCP Agent...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main_sync():
    """Synchronous entry point for console script (uvx discord-mcp-agent)."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
