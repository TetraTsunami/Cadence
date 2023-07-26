import aiohttp
import discord
from discord.ext import bridge, commands
from utils.embed import quick_embed
from discord import Webhook


class MetaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bridge.bridge_command()
    async def ping(self, ctx):
        """Returns the bot's ping"""
        await ctx.respond(
            embed=quick_embed(ctx, f"⚡ {round(self.bot.latency * 1000)} ms")
        )

    @bridge.bridge_command()
    async def about(self, ctx):
        """Returns info about the bot"""
        embed = discord.Embed(
            title=f"{self.bot.config['bot_name']} info",
            color=int(ctx.bot.config["color"][1:], 16),
            # **{self.bot.config['bot_name']}** is a bot owned by {await self.bot.get_or_fetch_user(self.bot.config['bot_owner_id'])} using [pycord](https://pycord.dev/)
            description=f"""Hiya! I'm {self.bot.config['bot_name']} ({self.bot.version}), a self-hosted music bot owned by {await self.bot.get_or_fetch_user(self.bot.config['bot_owner_id'])}.
            I use [pycord](https://pycord.dev/), [yt-dlp](https://github.com/yt-dlp/yt-dlp), and [ffmpeg](https://www.ffmpeg.org/).
            Type `{ctx.prefix}help` to get started, or `{ctx.prefix}invite` to invite me to your server.
            
            Source code available soon :)""",
        )
        embed.set_thumbnail(url=ctx.me.display_avatar)
        embed.add_field(
            name="Stats",
            value=f"**Ping:** {round(self.bot.latency * 1000)} ms\n**Guilds:** {len(self.bot.guilds)}\n**Users:** {len(self.bot.users)}",
        )
        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.respond(embed=embed)

    @bridge.bridge_command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def report(self, ctx, *, message):
        """Report a bug or request a feature"""
        if not self.bot.config["error_webhook_url"]:
            raise commands.UserInputError("This command is disabled, sorry")

        if len(message) > 2000:
            message = message[:2000]
        webhookUrl = self.bot.config["error_webhook_url"]

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(webhookUrl, session=session)

            e = (
                discord.Embed(
                    title="Cadence Bug Report",
                    description=message,
                    color=int(ctx.bot.config["color"][1:], 16),
                )
                .add_field(name="User", value=f"{ctx.author} ({ctx.author.id})")
                .add_field(name="Guild", value=f"{ctx.guild} ({ctx.guild.id})")
            )

            await webhook.send(embed=e)
        await ctx.respond(
            embed=quick_embed(
                ctx, "Report sent! Thank you for your feedback, it helps a lot!"
            ),
            ephemeral=True,
        )


def setup(bot):
    bot.add_cog(MetaCog(bot))
