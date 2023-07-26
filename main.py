import json
import logging
import os

import discord
from discord.ext import bridge, commands
from utils.help import FancyHelp

VERSION = "1.0.0"

# Import configuration
with open("configuration.json", "r") as data:
    config = json.load(data)
    token = config["token"]
    prefix = config["prefix"]
    owner_id = config["bot_owner_id"]
    activity = config["activity"]
    debug_guild = config["debug_guild_id"] if "debug_guild_id" in config else None


# Set up logging
class LoggingFormatter(logging.Formatter):
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        format = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) {message}"
        format = format.replace("(black)", self.black + self.bold)
        format = format.replace("(reset)", self.reset)
        format = format.replace("(levelcolor)", log_color)
        formatter = logging.Formatter(format, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

# File handler
fileHandler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
fileHandler.setFormatter(
    logging.Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
    )
)

# Console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(LoggingFormatter())

# Add handlers
logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)


# Create bot
intents = discord.Intents.default()
intents.message_content = True


class Bot(bridge.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.config = config


bot = Bot(
    command_prefix=commands.when_mentioned_or(prefix),
    intents=intents,
    owner_id=owner_id,
    # help_command=commands.DefaultHelpCommand(verify_checks=False),
    help_command=FancyHelp(verify_checks=False),
    case_insenitive=True,
)
if debug_guild:
    bot.debug_guilds = [debug_guild]
bot.version = VERSION

# Load cogs
COGS_DIRECTORY = "cogs"


def list_cogs(cogs_dir):
    return [
        extension
        for extension in [
            f.replace(".py", "")
            for f in os.listdir(cogs_dir)
            if os.path.isfile(os.path.join(cogs_dir, f))
        ]
    ]


if __name__ == "__main__":
    foundCogs = list_cogs(COGS_DIRECTORY)
    if not debug_guild and "dev" in foundCogs:
        foundCogs.remove("dev")
    logger.info(f"Loading cogs: {foundCogs}")
    for extension in foundCogs:
        try:
            bot.load_extension(COGS_DIRECTORY + "." + extension)
            logger.info(f"⤷ '{extension}' loaded")
        except Exception as e:
            logger.error(f"⤷ '{extension}' failed to load. {e}")
    logger.info("All modules loaded, logging in to Discord")


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} ({bot.user.id if bot.user else None})")
    if bot.debug_guilds:
        logger.warning(f"⤷ Using debug guild with ID {bot.debug_guilds}")

    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.playing, name=activity)
    )


bot.run(token)
