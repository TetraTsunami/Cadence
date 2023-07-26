import json
import logging
from datetime import datetime, timedelta
import traceback

import aiohttp
import discord
from discord import Webhook
from discord.ext import commands
from discord.ext.commands import Context

from utils.embed import command_embed


class ErrorHandlerCog(commands.Cog, name="on command error"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        await self.handle_errors(ctx, error)

    @commands.Cog.listener()
    async def on_application_command_error(
        self, ctx: Context, error: commands.CommandError
    ):
        await self.handle_errors(ctx, error)

    async def handle_errors(self, ctx: Context, error: commands.CommandError):
        logger = self.bot.logger
        webhookUrl = self.bot.config["error_webhook_url"]
        supportUrl = self.bot.config["support_invite"]

        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.UserInputError):
            await ctx.respond(
                embed=command_embed(
                    ctx, title=ctx.command.name, icon="❌", body=f"{error}"
                ),
                ephemeral=True,
            )
            return

        elif isinstance(error, commands.CommandOnCooldown):
            expirationTime = datetime.now() + timedelta(seconds=error.retry_after)
            text = f"This command is on a cooldown that expires {discord.utils.format_dt(expirationTime, 'R')}"
            await ctx.respond(
                embed=command_embed(ctx, title=ctx.command.name, icon="⏳", body=text),
                ephemeral=True,
            )
            return

        elif isinstance(error, commands.MissingPermissions):
            text = f"You need the following permission{'s' if len(error.missing_permissions) > 1 else ''} to use this command: {', '.join(error.missing_permissions)}"
            await ctx.respond(
                embed=command_embed(ctx, title=ctx.command.name, icon="⛔", body=text),
                ephemeral=True,
            )
            return

        elif isinstance(error, commands.BotMissingPermissions):
            text = f"I need the following permission{'s' if len(error.missing_permissions) > 1 else ''} to use this command: {', '.join(error.missing_permissions)}"
            await ctx.respond(
                embed=command_embed(ctx, title=ctx.command.name, icon="⛔", body=text),
                ephemeral=True,
            )
            return

        elif isinstance(
            error, commands.BadArgument
        ):  # This is a catch-all for command errors
            await ctx.respond(
                embed=command_embed(
                    ctx, title=ctx.command.name, icon="❌", body=f"```{error}```"
                ),
                ephemeral=True,
            )
            return

        # If we can't handle this, log the error & give the user a response
        try:
            options = [
                f"{e['name']}={e['value']}" for e in ctx.interaction.data["options"]
            ]
        except Exception as e:
            options = []

        if webhookUrl:
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhookUrl, session=session)

                e = (
                    discord.Embed(
                        title="Cadence Command Error",
                        description=f"```{''.join(traceback.format_exception(type(error), error, error.__traceback__))}```",
                        color=0xFF0000,
                    )
                    .add_field(
                        name="Command",
                        value=f"/{ctx.command.name} {' '.join(options)}",
                    )
                    .add_field(name="User", value=f"{ctx.author} ({ctx.author.id})")
                    .add_field(name="Guild", value=f"{ctx.guild} ({ctx.guild.id})")
                )

                await webhook.send(embed=e)

        logger.error(
            f"Uncaught exception in command {ctx.command} invoked by {ctx.author}.",
            exc_info=(type(error), error, error.__traceback__),
        )
        supportMessage = (
            f", or join my [support server]({supportUrl}) in the meantime."
            if supportUrl
            else "."
        )
        await ctx.respond(
            embed=command_embed(
                ctx,
                title=ctx.command.name,
                icon="❌",
                body=f"Something went terribly wrong and the error has been logged. Give it another shot in a little while{supportMessage} ```{error}```",
            ),
            ephemeral=True,
        )


def setup(bot):
    bot.add_cog(ErrorHandlerCog(bot))
