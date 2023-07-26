from utils.track import ActiveTrack, QueuedTrack
import discord
import asyncio
from random import shuffle
import datetime


class Playlist(asyncio.Queue):
    def shuffle(self):
        shuffle(self._queue)

    def peek(self):
        return self._queue[0]


class GuildQueue:
    def __init__(self, ctx):
        self._bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self._cog = ctx.cog

        self.queue: Playlist = Playlist()
        self.readyForNext = asyncio.Event()
        self.nowPlaying: ActiveTrack | None = None
        self._startedTime: float | None = None
        self._progress: float | None = None
        self.history: Playlist = Playlist()

        self.loopMode = 0  # 0 = off, 1 = loop queue, 2 = loop track
        self.volume = 0.5

        self.task = ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """The player loop."""
        await self._bot.wait_until_ready()

        while not self._bot.is_closed():
            self.readyForNext.clear()
            queueItem = await self.get_next()
            source = queueItem

            if not isinstance(source, discord.PCMVolumeTransformer):
                try:
                    source = await source.to_active_track(loop=self._bot.loop)
                except Exception as e:
                    await self.channel.send(
                        # TODO: better embed (color?)
                        embed=discord.Embed(
                            title="Error",
                            description=f"```{e}```",
                            color=discord.Color.red(),
                        )
                    )
                    continue

            source.volume = self.volume
            self.nowPlaying = source

            def after(error):
                if error:
                    raise error
                self._bot.loop.call_soon_threadsafe(self.readyForNext.set)

            self.guild.voice_client.play(
                source,
                after=after,
            )
            self._startedTime = datetime.datetime.now().timestamp()
            self._progress = 0

            # if there's another queued track after this one, activate it so there's less delay.
            # TODO: this is nice but what happens when someone shuffles the queue? the stream could expire if the activated track's tossed too far back. implement a way to refresh the stream url?
            await self._activate_next_track()

            # wait until the player is ready for the next track
            await self.readyForNext.wait()
            await self.history.put(queueItem)

            # Clean up FFmpeg after the track has finished
            source.cleanup()
            self.nowPlaying = None

    def shuffle(self):
        """Shuffle the queue."""
        self.queue.shuffle()

    def repeat_off(self):
        """Turn off repeat."""
        self.loopMode = 0

    def repeat_queue(self):
        """Repeat the queue."""
        self.loopMode = 1

    def repeat_track(self):
        """Repeat the track."""
        self.loopMode = 2

    def set_volume(self, volume: float):
        """Set the volume."""
        if volume < 0 or volume > 1:
            raise ValueError("Volume must be between 0 and 1, inclusive")
        self.volume = volume

    def pause(self):
        self.guild.voice_client.pause()
        self._progress += datetime.datetime.now().timestamp() - self._startedTime

    def resume(self):
        self.guild.voice_client.resume()
        self._startedTime = datetime.datetime.now().timestamp()

    def progress(self):
        return self._progress + datetime.datetime.now().timestamp() - self._startedTime

    async def get_next(self):
        """Gets the next track while handling looped queues."""
        if self.loopMode == 2 and self.queue._queue[0] is not None:
            return self.queue._queue[0]
        elif self.loopMode == 1 and self.queue.empty() and not self.history.empty():
            # If the queue is empty, but there are items in the history, move the history to the queue
            self.queue = self.history
            self.history = Playlist()
        return await self.queue.get()

    def peek_next(self):
        """Returns the next track without removing it from the queue."""
        if self.loopMode == 2 and self.queue._queue[0] is not None:
            # if we're looping the track, return the first item in the queue
            return self.queue._queue[0]
        elif self.loopMode == 1 and self.queue.empty() and not self.history.empty():
            return self.history._queue[0]
        elif not self.queue.empty():
            return self.queue.peek()
        return None

    async def _activate_next_track(self):
        nextTrack = self.peek_next()
        if nextTrack is not None and isinstance(nextTrack, QueuedTrack):
            activated = await nextTrack.to_active_track(loop=self._bot.loop)
            self.queue._queue[0] = activated

    def _has_empty_next(self):
        """Will an added track be up next/play immediately or not?"""
        nextUp = self.peek_next()
        if nextUp is None:
            return True
        if self.loopMode == 1 and self.queue.empty():
            return True
        return False

    async def add(self, track: QueuedTrack):
        await self.queue.put(track)

    async def add_url(self, ctx, url: str):
        tracks = await QueuedTrack.from_url(
            ctx, url, self._has_empty_next(), loop=self._bot.loop
        )
        for track in tracks:
            await self.queue.put(track)
        return tracks

    def np_embed(self):
        return self.nowPlaying.to_embed(progress=self.progress(), playing=True)

    async def cleanup(self):
        await self.guild.voice_client.disconnect()
        self.task.cancel()
