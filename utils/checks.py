from discord.ext import commands


def has_active_queue():
    """Make sure the guild has an active queue before running commands on it"""

    def predicate(ctx) -> bool:
        client = ctx.voice_client
        if not client or not client.is_connected():
            raise commands.UserInputError("I'm not connected to a voice channel")
        if not ctx.guild.id in ctx.cog.queues:
            raise commands.UserInputError("I'm not playing anything right now")

        return True

    return commands.check(predicate)


def has_active_song():
    """Make sure the bot is playing something before running commands on it"""

    def predicate(ctx) -> bool:
        if not ctx.guild.id in ctx.cog.queues:
            raise commands.UserInputError("I'm not playing anything right now")
        queue = ctx.cog.queues[ctx.guild.id]
        if not queue.nowPlaying:
            raise commands.UserInputError("I'm not playing anything right now")
        return True

    return commands.check(predicate)


def queue_not_empty():
    """Make sure there's music in the queue before running commands on it"""

    def predicate(ctx) -> bool:
        if not ctx.guild.id in ctx.cog.queues:
            raise commands.UserInputError("I'm not playing anything right now")
        queue = ctx.cog.queues[ctx.guild.id]
        if queue.queue.empty():
            raise commands.UserInputError("The queue is empty!")
        return True

    return commands.check(predicate)


def author_present():
    """Make sure the author is in the same voice channel as us before running commands on it"""

    def predicate(ctx) -> bool:
        client = ctx.voice_client
        if not ctx.author.voice:
            raise commands.UserInputError("You're not in a voice channel!")
        if not client or not client.is_connected():
            return True
        if client.channel != ctx.author.voice.channel:
            raise commands.UserInputError("You're not in the same voice channel as me!")
        return True

    return commands.check(predicate)
