import itertools
import discord
from discord.ext.commands import DefaultHelpCommand, Context
from discord.ext import commands


class FancyHelp(DefaultHelpCommand):
    def __init__(self, **options):
        super().__init__(
            **options,
            command_attrs={
                "cooldown": commands.CooldownMapping.from_cooldown(
                    1, 3.0, commands.BucketType.user
                ),
                "aliases": ["commands"],
            },
        )

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_line(bot.description, empty=True)

        no_category = "\u200b{0.no_category}:".format(self)

        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name + ":" if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, commands in to_iterate:
            commands = (
                sorted(commands, key=lambda c: c.name)
                if self.sort_commands
                else list(commands)
            )
            self.add_indented_commands(commands, heading=category, max_size=max_size)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

    def add_indented_commands(self, commands, *, heading, max_size=None):
        if not commands:
            return

        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)

        get_width = discord.utils._string_width
        for command in commands:
            name = f"{command.name} {command.signature}"
            width = max_size - (get_width(name) - len(name))
            entry = "{0}{1:<{width}} {2}".format(
                self.indent * " ",
                name,
                command.short_doc,
                width=width,
            )
            self.paginator.add_line(self.shorten_text(entry))
