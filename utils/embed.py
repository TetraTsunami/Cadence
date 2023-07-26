import discord


class HelpEmbed(discord.Embed):
    def __init__(self, ctx, **kwargs):
        super().__init__(**kwargs)
        self.set_footer(
            text="Use help [command] or help [category] for more information | <> is required | [] is optional"
        )
        self.color = int(ctx.bot.config["color"][1:], 16)


def quick_embed(
    ctx,
    body,
):
    """Generates a simple embed with a title from the command name and a body

    Returns:
        discord.Embed: Embed with the given parameters
    """

    embed = discord.Embed(
        color=int(ctx.bot.config["color"][1:], 16),
        title=f"📝 /{ctx.command.name}",
        description=body,
    )
    embed.set_footer(
        text=f"Requested by {ctx.author.display_name}",
        icon_url=ctx.author.display_avatar.url,
    )
    return embed


def command_embed(
    ctx,
    title="Command Embed",
    icon="",
    body="",
    imageUrl="",
    imageFile: discord.File | None = None,
):
    """Generates a simple embed with a title, icon, body, and maybe an image

    Args:
        ctx (discord.ApplicationContext): Ctx of the command, used to populate a rich footer.
        title (str, optional): Title of the embed. Defaults to 'Command Embed'.
        icon (str, optional): Emoji to place before the title. Defaults to no icon.
        body (str, optional): The body of the embed.
        imageUrl (str, optional): Image URL to place in the embed. Defaults to ''.
        imageFile (discord.File, optional): Image file to place in the embed. Defaults to 'None'.


    Returns:
        discord.Embed: Embed with the given parameters
    """

    embed = discord.Embed(color=int(ctx.bot.config["color"][1:], 16))
    if icon:
        embed.title = f"{icon} {title}"
    else:
        embed.title = title
    embed.description = body
    if imageUrl:
        embed.set_image(url=imageUrl)
    elif imageFile:
        embed.set_image(url=f"attachment://{imageFile.filename}")
    if ctx:
        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url,
        )
    return embed
