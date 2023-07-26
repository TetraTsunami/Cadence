import discord
from yt_dlp import YoutubeDL
import asyncio


YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # ipv6 addresses cause issues sometimes
}

FFMPEG_OPTIONS = {
    "before_options": "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdlp = YoutubeDL(YTDL_OPTIONS)


class QueuedTrack:
    def __init__(
        self,
        *,
        data,
        requester,
        web_url=None,
    ):
        self.data = data

        self.title = data.get("title")
        self.web_url = web_url or data.get(
            "webpage_url"
        )  # NOT a streaming url. link to the video page
        self.duration = data.get("duration")  # in seconds
        self.thumbnail = data.get("thumbnail")
        self.requester = requester

    @classmethod
    async def from_url(
        cls,
        ctx: discord.ApplicationContext,
        url: str,
        active: bool = False,
        *,
        loop=None,
    ):
        """Return an array of QueuedTracks from the given URL (with the first being Active if active is true)."""
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: ytdlp.extract_info(url, process=False, download=False),
        )

        if "entries" in data:
            tracks = []
            for entry in data["entries"]:
                # each entry has only its video page url, thumbnail + other info you'd get from the playlist overview- no streaming url.
                tracks.append(
                    cls(data=entry, requester=ctx.author, web_url=entry["url"])
                )

            if active:
                tracks[0] = await tracks[0].to_active_track(loop=loop)

            return tracks

        track = cls(data=data, requester=ctx.author, web_url=data["webpage_url"])

        if active:
            return [await track.to_active_track(loop=loop)]
        else:
            return [track]

    async def to_active_track(self, loop=None):
        # TODO: if we queued an individual song + are activating it 6+ hours later, does that mean we need to refresh the streaming urls?
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdlp.process_ie_result(self.data, download=False)
        )
        return ActiveTrack(
            discord.FFmpegPCMAudio(data["url"], **FFMPEG_OPTIONS),
            data=data,
            requester=self.requester,
            web_url=self.web_url,
        )

    def pretty_duration(self, time=None):
        if time is None:
            time = self.duration
        else:
            time = int(time)
        hours = time // 3600
        minutes = (time % 3600) // 60
        seconds = time % 60
        return f"{hours}:{minutes :02}:{seconds :02}"

    def to_embed(self, progress: int = -1, playing: bool = False):
        trackType = "Playing track" if playing else "Queued track"
        trackProgress = self.pretty_duration()
        if progress >= 0:
            trackProgress = f"{self.pretty_duration(progress)} / {trackProgress}"
        return (
            discord.Embed(
                title=self.title,
                url=self.web_url,
                description=trackProgress,
                color=0xC84268,
            )
            .set_author(
                name=trackType,
            )
            .set_thumbnail(url=self.thumbnail)
            .set_footer(
                text=f"Requested by {self.requester.display_name}",
                icon_url=self.requester.display_avatar.url,
            )
        )


class ActiveTrack(discord.PCMVolumeTransformer, QueuedTrack):
    def __init__(
        self,
        source,
        *,
        data,
        requester,
        volume=1.0,
        web_url=None,
    ):
        super().__init__(source, volume)
        QueuedTrack.__init__(self, data=data, requester=requester)
