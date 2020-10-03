from discord import TextChannel
from discord.ext.commands import Cog, command, check

from typing import Optional

from asyncio import TimeoutError

from utils.classes import NumEmbed
from utils.numbers import is_allowed_number
from utils.checks import is_in_main_guild, is_moderator, is_admin
from utils.helpers import filter_username, upload_text, get_date_time

class Moderator(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @check(is_moderator)
    @command(aliases=["numbers", "numberlist"])
    async def list(self, ctx):
        """
        (MOD) Gets a list of all the currently assigned numbers.
        """
        # Generate the list.
        text = f"r/{self.bot.reddit.main_sub_name} Number List - {len(self.bot.numbers.numbers.keys())} Assigned - {get_date_time()} UTC"
        for number, user in self.bot.numbers.numbers.items():
            text += f"\n#{number} (u/{user})"

        # Attempt to upload the list and send a message if there was an error uploading it.
        link = upload_text(text)
        if link == None:
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Number List",
                    description="There was an error uploading the list.\nPlease try again later.",
                    colour="failure",
                    user=ctx.author,
                    footer_text="Restricted Cmd",
                ),
            )
            return

        # Uploading was a success. Send a message.
        await ctx.send(
            "",
            embed=NumEmbed(
                title="Click here to view the list.",
                description="Generated a list of the current assigned numbers.",
                url=link,
                user=ctx.author,
                footer_text="Restricted Cmd",
            ),
        )

    @check(is_moderator)
    @command(aliases=["randnumber"])
    async def randomnum(self, ctx):
        """
        (MOD) Generates a random avaliable number within the assignment range.
        """
        await ctx.send(
            "",
            embed=NumEmbed(
                title="Random Avaliable Number",
                description=self.bot.numbers.generation.get_random_number(),
                user=ctx.author,
                footer_text="Restricted Cmd",
            ),
        )

    @check(is_moderator)
    @command()
    async def rangeinfo(self, ctx):
        """
        (MOD) Get some info on the current number assignment range.
        """
        await ctx.send(
            "",
            embed=NumEmbed(
                title="Assignment Number Range",
                fields={
                    "Minimum": self.bot.settings.reddit.assignment.numbers["min"],
                    "Maximum": self.bot.numbers.current_max_number,
                },
                user=ctx.author,
                footer_text="Restricted Cmd",
            ),
        )

    @check(is_moderator)
    @command()
    async def checkeligiblity(self, ctx, username: filter_username):
        """
        (MOD) Check if a user meets the requirements to get a number.
        """
        if is_allowed_number(username):
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Eligibility Check",
                    description=f"u/{username} meets the karma and age requirements for a number.",
                    colour="success",
                    user=ctx.author,
                    footer_text="Restricted Cmd",
                ),
            )
        else:
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Eligibility Check",
                    description=f"u/{username} DOES NOT meet a karma/age requirement.",
                    colour="failure",
                    user=ctx.author,
                    footer_text="Restricted Cmd",
                ),
            )

    @check(is_moderator)
    @command(aliases=["moderatoridea"])
    async def modidea(self, ctx, *, idea: str):
        """
        (MOD) Send a message to the mod idea channel.
        """
        # Load the ideas channel channel and then send the idea to it.
        ideas_channel = self.bot.get_channel(self.bot.settings.discord.ids["idea_channels"]["mod"])
        message = await ideas_channel.send(
            "",
            embed=NumEmbed(
                title="Moderator Idea",
                colour=0x000080,
                fields={
                    "Added by": f"{ctx.author.mention}",
                    "Idea": idea,
                },
            ),
        )

        # Adds vote reactions to the idea message.
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        # React to the invoking message.
        await ctx.message.add_reaction("👍")

    @check(is_admin)
    @command()
    async def refresh(self, ctx):
        """
        (ADMIN) Refresh the Reddit wiki settings.
        """
        self.bot.settings.load_wiki_settings(self.bot.reddit)
        self.bot.numbers.set_max_number()
        await ctx.send(
            "",
            embed=NumEmbed(
                title="Settings",
                description="Succesfully refreshed the Reddit wiki settings.",
                colour="success",
                user=ctx.author,
                footer_text="Restricted Cmd",
            ),
        )

    @check(is_admin)
    @check(is_in_main_guild)
    @command()
    async def purge(self, ctx, amount: int = 100):
        """
        (ADMIN) Delete a specified amount of messages from the current channel.
        """
        messages_deleted = 0
        async for message in ctx.channel.history(limit=amount):
            # Ignore if the message is pinned.
            if not message.pinned:
                messages_deleted += 1
                await message.delete()

        await ctx.send(f"✅ Deleted {messages_deleted} messages!")

    @check(is_admin)
    @command(aliases=["msg", "message", "echo"])
    async def say(self, ctx, channel: Optional[TextChannel] = None, *, text: str):
        """
        (ADMIN) Make the bot send a message to a specified channel.
        """
        # If a channel wasn't specified then set it to the current channel.
        if not channel:
            channel = ctx.channel

        # Attempt to delete the invoking message and then send a message to that channel.
        try:
            await ctx.message.delete()
        except:
            pass
        finally:
            await channel.send(text)

    @check(is_admin)
    @command(aliases=["setnum", "setnumber"])
    async def assign(self, ctx, username: filter_username, number: int = None):
        """
        (ADMIN) Assigns a specific or random number to a user.
        """
        # Check that the user is valid.
        if not self.bot.reddit.is_valid_user(username):
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Number Assignment",
                    description=f"u/{username} is not a valid user.",
                    colour="failure",
                    user=ctx.author,
                    footer_text="Restricted Cmd",
                ),
            )
            return

        # Get a random avaliable number if one wasn't given.
        if number == None:
            number = self.bot.numbers.generation.get_random_number()

        # Send a confirmation message.
        confirmation_message = await ctx.send(
            "",
            embed=NumEmbed(
                title="Number Assignment (Pending Confirmation)",
                description="Please react with '✅' (in the next 30 seconds) to go through with the following assignment:",
                fields={
                    "User": f"u/{username}",
                    "Number": number,
                },
                user=ctx.author,
                footer_text="Restricted Cmd",
            ),
        )
        await confirmation_message.add_reaction("✅")

        # Handle the confirmation reaction.
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=lambda reaction, user: str(reaction.emoji) == "✅" and user == ctx.author)
        except TimeoutError:
            # No reaction was given in time.
            await confirmation_message.edit(
                embed=NumEmbed(
                    title="Number Assignment (Expired)",
                    description="A confirmation was not given in time.",
                    colour="failure",
                    user=ctx.author,
                    footer_text="Restricted Cmd",
                ),
            )
        else:
            # The assignment was confirmed.
            self.bot.numbers.assignment.assign_number(username, number)

            await confirmation_message.edit(
                embed=NumEmbed(
                    title="Number Assignment",
                    description="Succesfully assigned that user a number.",
                    fields={field.name: field.value for field in confirmation_message.embeds[0].fields},
                    colour="success",
                    user=ctx.author,
                    footer_text="Restricted Cmd",
                ),
            )

def setup(bot) -> None:
    bot.add_cog(Moderator(bot))
