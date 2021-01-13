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
from discord.ext.commands import Cog, command, check

from utils.classes import NumEmbed
from utils.checks import is_verified, is_in_main_guild


class Misc(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @check(is_verified)
    @check(is_in_main_guild)
    @command(aliases=["nickname", "setnick"])
    async def nick(self, ctx, *, nick: str = None):
        """
        Give yourself a nickname.
        """
        name_info = ctx.author.display_name.split(" | ")
        number = int(name_info[0])
        username = name_info[1]

        # Load the nickname log channel.
        nickname_log_channel = self.bot.get_channel(self.bot.settings.discord.ids["log_channels"]["nickname_log"])

        # Attempt to set the user's nickname.
        if nick is not None:
            # Check that their new nickname will be under the Discord 32 character nickname limit.
            new_nickname = f"{number} | {username} | {nick}"
            if len(new_nickname) > 32:
                # Send a message to the user.
                await ctx.send(
                    "",
                    embed=NumEmbed(
                        title="Nickname",
                        description="Failed to set your nickname as (in total) it would be over 32 characters (the Discord nickname limit).",
                        colour="failure",
                        fields={
                            "Input Nickname": nick,
                            "Attempted Nickname (Full)": new_nickname,
                            "Nickname (cut off at 32 chars)": new_nickname[:32],
                        },
                        user=ctx.author,
                    ),
                )

                # Send a message to the log channel.
                await nickname_log_channel.send(
                    "",
                    embed=NumEmbed(
                        title="Failed Nickname Set (Too Long)",
                        colour="failure",
                        fields={
                            "Current Nickname": " | ".join(name_info),
                            "Failed Nickname (Full)": new_nickname,
                            "Discord User": f"{ctx.author}\n{ctx.author.id}\n{ctx.author.mention}",
                        },
                    ),
                )
                return

            # Set the user's nickname.
            await ctx.author.edit(nick=new_nickname)

            # Send a message to the channel.
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Nickname",
                    description=f"Succesfully changed your nickname to '{new_nickname}'.",
                    user=ctx.author,
                )
            )

            # Send a message to the log channel that it was a success.
            await nickname_log_channel.send(
                "",
                embed=NumEmbed(
                    title="Successful Nickname Set",
                    colour="success",
                    fields={
                        "Old Nickname": " | ".join(name_info),
                        "New Nickname": new_nickname,
                        "Discord User": f"{ctx.author}\n{ctx.author.id}\n{ctx.author.mention}",
                    },
                ),
            )
        else:
            # Remove the user's custom nickname (if any).
            await ctx.author.edit(nick=f"{number} | {username}")

            # Send a message to the log channel that it was succesfully removed.
            await nickname_log_channel.send(
                "",
                embed=NumEmbed(
                    title="Successful Nickname Removal",
                    colour="success",
                    fields={
                        "New Nickname": ctx.author.display_name,
                        "Old Nickname": " | ".join(name_info),
                        "Discord User": f"{ctx.author}\n{ctx.author.id}\n{ctx.author.mention}",
                    },
                ),
            )

    @check(is_verified)
    @check(is_in_main_guild)
    @command(aliases=["idea"])
    async def suggest(self, ctx, *, suggestion: str):
        """
        Suggest an idea in the main r/Num guild.
        """
        # Load the suggestions channel.
        suggestions_channel = self.bot.get_channel(self.bot.settings.discord.ids["idea_channels"]["standard"])

        # Send a message to the suggestions channel.
        message = await suggestions_channel.send(
            "",
            embed=NumEmbed(
                title="Suggestion",
                colour=0x000080,
                fields={
                    "Added by": f"{ctx.author.mention}",
                    "User Nickname": f"{ctx.author.display_name}",
                    "User ID": f"{ctx.author.id}",
                    "Suggestion Text": f"{suggestion}"
                },
            ),
        )

        # Adds vote reactions to the suggestion message.
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        # Send a message to the user.
        await ctx.send(f"{ctx.author.mention} Your suggestion has been added to the suggestions channel.")


def setup(bot) -> None:
    bot.add_cog(Misc(bot))
