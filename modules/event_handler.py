"""
Copyright 2020 OneUpPotato

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from discord.ext import commands

import utils.errors as errors
from utils.classes import NumEmbed


class EventHandler(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error) -> None:
        """
        Handles general command errors.
        :param ctx: The command context.
        :param error: The error encountered.
        """

        # Capture the error using Sentry.
        non_logged_errors = [
            commands.MissingRequiredArgument,
            commands.TooManyArguments,
            commands.DisabledCommand,
            commands.NoPrivateMessage,
            commands.CommandNotFound,
            commands.CheckFailure,
            commands.BadArgument,
            errors.AdminCheckFailure,
            errors.VerifiedCheckFailure,
            errors.MainGuildCheckFailure,
            errors.ModeratorCheckFailure,
            errors.DeveloperCheckFailure,
            errors.NotMainGuildCheckFailure,
            errors.AlreadyVerifiedCheckFailure,
        ]
        if not any([isinstance(error, non_log_error) for non_log_error in non_logged_errors]):
            self.bot.sentry.capture_exception(error)

        # Ignore if the command already has its own error handler.
        if hasattr(ctx.command, "on_error"):
            return

        # Since the error isn't handled elsewhere, prepare a message to send to the user.
        embed = NumEmbed(title="Error", description="Something went wrong.", colour=0x8B0000)

        if isinstance(error, commands.MissingRequiredArgument):
            missing_argument = error.param.name
            embed.description = f"You are missing the following argument: '{missing_argument}'."
        elif isinstance(error, commands.TooManyArguments):
            embed.description = "Too many arguments have been given."
        elif isinstance(error, errors.ModeratorCheckFailure):
            embed.description = "You are not able to run this command as you are not a Moderator."
        elif isinstance(error, errors.AdminCheckFailure):
            embed.description = "You are not authorised to run this command as you are not a bot admin."
        elif isinstance(error, errors.DeveloperCheckFailure):
            embed.description = "You are not authorised to use this command."
        elif isinstance(error, errors.VerifiedCheckFailure):
            embed.description = "You need to be verified in order to do this."
        elif isinstance(error, errors.AlreadyVerifiedCheckFailure):
            embed.description = "You are already verified meaning you cannot use this command."
        elif isinstance(error, errors.MainGuildCheckFailure):
            embed.description = "This command can only run on the main r/Num Discord guild."
        elif isinstance(error, errors.NotMainGuildCheckFailure):
            embed.description = "This command cannot run in this guild."
        elif isinstance(error, commands.DisabledCommand):
            embed.description = "This command is currently disabled.\nThis may be due to bug fixing or improvement."
        elif isinstance(error, commands.NoPrivateMessage):
            embed.description = "You cannot run this command in DMs, you need to be on a guild."
        elif isinstance(error, commands.CommandNotFound):
            embed.description = f"That command doesn't exist. You can view a list of cmds by using '{self.bot.settings.discord.prefix}help'."
        elif isinstance(error, commands.CheckFailure):
            embed.description = "You are not able to run this command currently.\nThis may be because you don't have the required role, or aren't running it from the main Discord guild."
        elif isinstance(error, commands.BadArgument):
            embed.description = "You've input something incorrectly (or not accepted)."
        else:
            embed.description = "Something went wrong. The error has been logged."

        print(f"{type(error)}: {error}")
        await ctx.send("", embed=embed)


def setup(bot) -> None:
    bot.add_cog(EventHandler(bot))
