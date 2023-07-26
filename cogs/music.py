import discord
from discord.ext import bridge, commands, pages
from discord.ext.bridge import BridgeContext
from utils.queue import GuildQueue
from utils.embed import quick_embed
from utils.checks import (
    has_active_queue,
    has_active_song,
    queue_not_empty,
    author_present,
)
from utils.utils import chunks


async def react_or_respond(ctx, message, reaction):
    if not ctx.is_app:
        await ctx.message.add_reaction(reaction)
    else:
        await ctx.respond(message)


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def get_queue(self, ctx) -> GuildQueue:
        """Get the guild queue object, or make a new one."""
        try:
            queue = self.queues[ctx.guild.id]
        except KeyError:
            queue = GuildQueue(ctx)
            self.queues[ctx.guild.id] = queue

        return queue

    @bridge.bridge_command()
    @bridge.guild_only()
    async def join(self, ctx: bridge.BridgeContext):
        """Joins the voice channel you are in!"""
        await ctx.respond(embed=quick_embed(ctx, f"Joined {ctx.author.voice.channel}"))

    @bridge.bridge_command(aliases=["p"])
    @bridge.guild_only()
    async def play(self, ctx: bridge.BridgeContext, url):
        """Add a song or playlist to queue"""
        await ctx.defer()
        queue = self.get_queue(ctx)

        tracks = await queue.add_url(ctx, url)
        await ctx.respond(
            f"Added {len(tracks)} track{'s' if len(tracks) > 1 else ''} to queue",
            embed=tracks[0].to_embed(),
        )

    @bridge.bridge_command()
    @has_active_queue()
    @has_active_song()
    @author_present()
    @bridge.guild_only()
    async def pause(self, ctx: BridgeContext):
        """Pause the currently playing song."""
        client = ctx.voice_client

        if client.is_paused():
            return

        client.pause()
        await react_or_respond(ctx, "Paused ⏸️", "⏸️")

    @bridge.bridge_command(aliases=["r", "res", "unpause", "unp"])
    @has_active_queue()
    @has_active_song()
    @author_present()
    @bridge.guild_only()
    async def resume(self, ctx):
        """Resume the currently paused song."""
        client = ctx.voice_client

        if not client.is_paused():
            return

        client.resume()
        await react_or_respond(ctx, "Resumed ▶️", "▶️")

    @bridge.bridge_command(aliases=["np"])
    @has_active_queue()
    @has_active_song()
    @bridge.guild_only()
    async def nowplaying(self, ctx):
        """Show the currently playing song."""
        queue = self.get_queue(ctx)
        await ctx.respond(embed=queue.np_embed())

    @bridge.bridge_command(aliases=["s"])
    @has_active_queue()
    @has_active_song()
    @queue_not_empty()
    @author_present()
    @bridge.guild_only()
    async def skip(self, ctx):
        """Skip the song."""
        client = ctx.voice_client
        client.stop()
        await react_or_respond(ctx, "Skipped ⏭️", "⏭️")

    @bridge.bridge_command(aliases=["dc", "l", "stop", "end"])
    @has_active_queue()
    @author_present()
    @bridge.guild_only()
    async def leave(self, ctx):
        """Stop the currently playing song and destroy the player."""

        await self.get_queue(ctx).cleanup()
        try:
            del self.queues[ctx.guild.id]
        except KeyError:
            pass

        await react_or_respond(ctx, "Left the voice channel 👋", "👋")

    @bridge.bridge_command(aliases=["q"])
    @has_active_queue()
    @queue_not_empty()
    @bridge.guild_only()
    async def queue(self, ctx):
        """View the queue."""
        queue = self.get_queue(ctx)

        queueList = list(queue.queue._queue)
        pageList = []
        for i, chunk in enumerate(chunks(queueList, 10)):
            pageContents = "\n".join(
                f"[{element.title}]({element.web_url}) {element.pretty_duration()}"
                for element in chunk
            )
            pageList.append(
                discord.Embed(
                    title=f"Queue page {i+1}",
                    description=pageContents,
                    color=0xC84268,
                )
            )
        paginator = pages.Paginator(pages=pageList)
        await paginator.respond(ctx, silent=True)

    @bridge.bridge_command(aliases=["vol", "v"])
    @has_active_queue()
    @author_present()
    @bridge.guild_only()
    async def volume(self, ctx, volume: float):
        """Pick a volume between 0% and 100%."""
        queue = self.get_queue(ctx)
        if volume < 0 or volume > 100:
            raise commands.UserInputError("Volume must be between 0 and 100%")
        if volume < 1:
            volume = volume * 100
        queue.set_volume(volume / 100)
        # TODO: take effect immediately if possible
        await ctx.respond(
            f"Set volume to {round(volume)}% (takes effect on next song)", silent=True
        )

    @bridge.bridge_command(aliases=["sh"])
    @has_active_queue()
    @queue_not_empty()
    @author_present()
    @bridge.guild_only()
    async def shuffle(self, ctx):
        """Shuffles the queue."""
        queue = self.get_queue(ctx)
        queue.shuffle()
        await react_or_respond(ctx, "Shuffled 🔀", "🔀")

    @bridge.bridge_group()
    @has_active_queue()
    @bridge.guild_only()
    @bridge.map_to("show")
    async def loop(self, ctx):
        """Show the current loop mode."""
        queue = self.get_queue(ctx)
        loopMode = queue.loopMode
        loopTypes = ["off", "queue", "track"]
        if loopMode >= 0 and loopMode < 3:
            await ctx.respond(f"Looping {loopTypes[loopMode]}")

    @loop.command()
    @has_active_queue()
    @queue_not_empty()
    @author_present()
    @bridge.guild_only()
    async def queue(self, ctx):
        """Loop the queue."""
        queue = self.get_queue(ctx)
        queue.repeat_queue()
        await react_or_respond(ctx, "Looping queue 🔁", "🔁")

    @loop.command()
    @has_active_queue()
    @author_present()
    @bridge.guild_only()
    async def track(self, ctx):
        """Loop the current track."""
        queue = self.get_queue(ctx)
        queue.repeat_track()
        await react_or_respond(ctx, "Looping just this track 🔂", "🔂")

    @loop.command()
    @has_active_queue()
    @author_present()
    @bridge.guild_only()
    async def off(self, ctx):
        """Turn off looping."""
        queue = self.get_queue(ctx)
        queue.repeat_off()
        await react_or_respond(ctx, "Looping off ➡️", "➡️")

    @play.before_invoke
    @join.before_invoke
    async def join_voice(self, ctx: BridgeContext):
        if not ctx.author.voice:
            raise commands.UserInputError("You're not in a voice channel!")

        channel = ctx.author.voice.channel
        client = ctx.guild.voice_client
        if client and client.channel == channel:
            return
        elif client and client.is_playing():
            client.stop()
            await client.move_to(channel)
        elif client:
            await client.move_to(channel)
        else:
            await channel.connect()


def setup(bot):
    bot.add_cog(MusicCog(bot))
