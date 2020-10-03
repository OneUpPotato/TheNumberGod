from discord.utils import find

import utils.errors as errors

def has_role(author, role_id) -> bool:
    """
    Checks if a user has a certain role.
    :return: True or False depending on if that user has the role.
    """
    try:
        role = find(lambda role: role.id == role_id, author.roles)
        if role != None:
            return True
    except:
        pass
    return False

async def is_in_main_guild(ctx):
    """
    Checks if a message was sent in the main Num guild.
    :return: True if it is and an error is raised if it isn't.
    """
    try:
        if ctx.guild.id == ctx.bot.settings.discord.main_guild:
            return True
    except:
        pass
    raise errors.MainGuildCheckFailure

async def is_not_in_main_guild(ctx):
    """
    Checks if a message was not sent in the main Num guild.
    :return: True if wasn't or an error is raised if it isn't.
    """
    try:
        if ctx.guild.id != ctx.bot.settings.discord.main_guild:
            return True
    except:
        pass
    raise errors.NotMainGuildCheckFailure

async def is_developer(ctx):
    """
    Checks if the user is a bot developer.
    :return: True or an error is raised (depending on if the user is).
    """
    if ctx.author.id in ctx.bot.settings.discord.developers:
        return True
    raise errors.DeveloperCheckFailure

async def is_admin(ctx):
    """
    Checks if a user is an admin.
    :return: Either True or an error (depending on if the user is).
    """
    try:
        if ctx.author.id in ctx.bot.settings.discord.admins or await is_developer(ctx):
            return True
    except errors.DeveloperCheckFailure:
        pass
    raise errors.AdminCheckFailure

async def is_moderator(ctx):
    """
    Checks if a user has the moderator role (or is an admin).
    :return: True if they do, otherwise an error is raised.
    """
    try:
        if has_role(ctx.author, ctx.bot.settings.discord.role_ids.other["Moderator"]) or await is_admin(ctx):
            return True
    except errors.AdminCheckFailure:
        pass
    raise errors.ModeratorCheckFailure

async def is_verified(ctx):
    """
    Checks if a user is verified.
    :return: True or an error is raised depending on if they have the verified role.
    """
    if has_role(ctx.author, ctx.bot.settings.discord.role_ids.other["Verified"]):
        return True
    raise errors.VerifiedCheckFailure

async def is_not_verified(ctx):
    """
    Checks if a user isn't verified.
    :return: True or an error (depending on the result).
    """
    try:
        user_verified = await is_verified(ctx)
        if user_verified:
            raise errors.AlreadyVerifiedCheckFailure
    except errors.VerifiedCheckFailure:
        return True
