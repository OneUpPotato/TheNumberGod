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
from discord.ext.commands import Cog, command

from psutil import cpu_percent, virtual_memory

from utils.classes import NumEmbed


class General(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @command()
    async def info(self, ctx) -> None:
        """
        View some information about the bot.
        """
        await ctx.send(
            "",
            embed=NumEmbed(
                title="The Number God Bot",
                description=f"The bot that helps run r/{self.bot.settings.reddit.subreddit}",
                fields={
                    "CPU/Memory Usage": f"{cpu_percent()}%/{virtual_memory().percent}%",
                    "Lines of Code": self.bot.lines_of_code,
                    "Created by": "u/OneUpPotato for r/Num",
                },
                footer_text="TNG v2.1",
                user=ctx.author,
            ),
        )

    @command(alias=["staff"])
    async def contact(self, ctx, *, text: str) -> None:
        """
        Contact the Num moderators through Discord.
        """
        num_guild = self.bot.get_guild(self.bot.settings.discord.main_guild)
        guild_user = num_guild.get_member(ctx.author.id)

        # Check that the user is in the main guild.
        # This is to prevent misuse of the command.
        if guild_user is None:
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Contacting Staff",
                    description="To prevent misuse of this command, you are required to be in the main Discord guild in order to use it.",
                    colour="failure",
                    user=ctx.author,
                ),
            )
            return

        # Attempt to delete the user's contact message.
        try:
            await ctx.message.delete()
        except Exception:
            pass

        # Send the message to the staff contact channel
        contact_channel = self.bot.get_channel(self.bot.settings.discord.ids["contact_channel"])
        await contact_channel.send(
            "",
            embed=NumEmbed(
                title="Staff Contact",
                fields={
                    "Sent by": f"{ctx.author.mention}\n{guild_user.display_name}\n{ctx.author}",
                    "Message": text,
                },
                colour=0xFF5554,
            ),
        )

        # Let the user know that we've received their message.
        await ctx.author.send("We've received your message. We should get back to you shortly.")


def setup(bot) -> None:
    bot.add_cog(General(bot))
