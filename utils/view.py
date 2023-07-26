import discord
from discord.ext import commands


class LinkButtons(discord.ui.View):
    def __init__(
        self, ctx: commands.Context, buttons: dict, timeout: int | None = None
    ):
        """A View that displays buttons which link to URLs.

        Usage (setting message is unneccessary if you don't want to disable the link):
            view = LinkButton(ctx, timeout=None, buttons={"Discord": "https://discord.com", "GitHub": "https://github.com"})
            message = await ctx.respond("This is a button!", view=view)
            view.message = message

        Args:
            ctx (commands.Context)
            buttons (dict): A dictionary of {label: url} to display as buttons.
            timeout (int): The amount of time to wait before disabling the buttons. Defaults to None.
        """
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.message: discord.Message | None = None
        self.children: list[discord.ui.Button]
        for label in buttons:
            if buttons[label] is None:
                continue
            self.add_item(
                discord.ui.Button(
                    label=label, style=discord.ButtonStyle.link, url=buttons[label]
                )
            )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)
