from discord import User, Member, Message
from discord.utils import get
from discord.ext.commands import Cog, command, check

from typing import Union
from textwrap import dedent

from utils.classes import NumEmbed, SpamProtection
from utils.checks import is_in_main_guild, is_developer

class Reactions(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.singular_names = {
            "countries": "Country",
            "organizations": "Organization",
            "ping_notifications": "Ping Notification",
        }

        self.role_ids = self.bot.settings.discord.role_ids.role_ids
        self.selection_ids = self.bot.settings.discord.ids["selection"]
        self.reaction_to_role = self.bot.settings.discord.reaction_roles

        self.spam_protection = SpamProtection()

    @check(is_developer)
    @check(is_in_main_guild)
    @command()
    async def update_reactions(self, ctx):
        """
        (DEVELOPER) Adds the base reactions to the reaction role messages.
        """
        # Fetch the reaction role messages.
        countries_msg = await self.bot.get_channel(self.selection_ids["channel"]["countries"]).fetch_message(self.selection_ids["message"]["countries"])
        organizations_msg = await self.bot.get_channel(self.selection_ids["channel"]["organizations"]).fetch_message(self.selection_ids["message"]["organizations"])
        ping_notifications_msg = await self.bot.get_channel(self.selection_ids["channel"]["ping_notifications"]).fetch_message(self.selection_ids["message"]["ping_notifications"])

        # Iterate each category.
        for name, items in self.reaction_to_role.items():
            # Get the message for each category.
            message = locals()[name + "_msg"]

            # Add the reactions to the message.
            for emoji in items.keys():
                await message.add_reaction(emoji)

        # React to the command message when finished.
        await ctx.message.add_reaction("👍")

    async def reaction_role_add(self, user: Union[User, Member], role_name: str, category: str, message: Message, emoji: str):
        """
        Handles adding a reaction role after being called from the reaction event.
        :param user: The user who to remove a role from.
        :param role_name: The role (name) to validate eligiblity for (and possibly add to the user).
        :param category: The specific category of reaction role (e.g ping notifications).
        :param message: The reaction role category message.
        :param emoji: The emoji reacted with (used if the reaction needs to be removed).
        """
        name_info = user.display_name.split(" | ")
        number = int(name_info[0])

        # Load the log channel.
        log_channel = self.bot.get_channel(self.bot.settings.discord.ids["log_channels"]["selection_logs"][category])

        # If the role category is a country then check if they are eligible.
        if category == "countries":
            if not self.bot.numbers.checks.is_eligible_for(number, role_name):
                # The user is not eligible. Attempt to send a message to them and then the log channel.
                try:
                    await user.send(f"Your number is not eligible for the '{role_name}' role.")
                except:
                    pass
                finally:
                    await log_channel.send(
                        "",
                        embed=NumEmbed(
                            title=f"(Failed) {self.singular_names[category]} Join",
                            description="That user is not eligible for this role.",
                            colour=0xFFFF00,
                            fields={
                                "Number": number,
                                "Username": f"u/{name_info[1]}",
                                "Discord User": f"@{user}\n{user.mention}\nID: {user.id}",
                                "Role": role_name,
                            },
                        ),
                    )

                # Remove their reaction.
                await message.remove_reaction(emoji, user)

                return

        # If the role is a country then ensure they are not at the country limit.
        if category == "countries":
            current_countries = [role.id for role in user.roles if role.id in self.role_ids[category].values()]
            if len(current_countries) >= 2:
                # The user is already at the maximum amount of countries.
                try:
                    await user.send(f"Failed to join '{role_name}'. You are already in two countries, leave one and try again.")
                except:
                    pass
                finally:
                    await log_channel.send(
                        "",
                        embed=NumEmbed(
                            title=f"(Failed) {self.singular_names[category]} Join",
                            description="That user is already at the maximum amount of countries.",
                            colour=0xFFFF00,
                            fields={
                                "Number": number,
                                "Username": f"u/{name_info[1]}",
                                "Discord User": f"@{user}\n{user.mention}\nID: {user.id}",
                                "Role": role_name,
                            },
                        ),
                    )

                # Remove their reaction.
                await message.remove_reaction(emoji, user)

                return

        # Fetch the role and then assign it to the user.
        role = get(message.guild.roles, id=self.role_ids[category][role_name])
        await user.add_roles(role)

        # Attempt to send a message to the user, then send a message to the log channel.
        try:
            await user.send(f"Succesfully added the '{role_name}' role.")
        except:
            pass
        finally:
            await log_channel.send(
                "",
                embed=NumEmbed(
                    title=f"{self.singular_names[category]} Join",
                    colour="success",
                    fields={
                        "Number": number,
                        "Username": f"u/{name_info[1]}",
                        "Discord User": f"@{user}\n{user.mention}\nID: {user.id}",
                        "Role": role_name,
                    },
                ),
            )

    async def reaction_role_remove(self, user: Union[User, Member], role_name: str, category: str, message: Message):
        """
        Handles removing a role upon a reaction being removed.
        :param user: The user who to remove a role from.
        :param role_name: The role (name) to remove.
        :param category: The specific category of reaction role (e.g ping notifications).
        :param message: The reaction role category message.
        """
        name_info = user.display_name.split(" | ")
        number = int(name_info[0])

        # Ignore the reaction removal if the user was never eligible for the role.
        if category == "countries":
            if not self.bot.numbers.checks.is_eligible_for(number, role_name):
                return

        # Fetch the role.
        role = get(message.guild.roles, id=self.role_ids[category][role_name])

        # Ignore if the user never had the role.
        if role not in user.roles:
            return

        # Remove the role from the user.
        await user.remove_roles(role)

        # Attempt to send a message to the user, then send a message to the log channel.
        try:
            await user.send(f"Removed the '{role_name}' role from you.")
        except:
            pass
        finally:
            log_channel = self.bot.get_channel(self.bot.settings.discord.ids["log_channels"]["selection_logs"][category])
            await log_channel.send(
                "",
                embed=NumEmbed(
                    title=f"{self.singular_names[category]} Left",
                    colour="failure",
                    fields={
                        "Number": number,
                        "Username": f"u/{name_info[1]}",
                        "Discord User": f"@{user}\n{user.mention}\nID: {user.id}",
                        "Role": role_name,
                    },
                ),
            )

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Watches for when reactions are added to handle reaction roles.
        """
        # Ensure that the reacter isn't the bot.
        if payload.user_id == self.bot.user.id:
            return

        # Check that the message is one of the reaction messages.
        category = next((name for name, id in self.selection_ids["message"].items() if id == payload.message_id), None)
        if not category:
            return

        # Fetch some info from the payload.
        user = payload.member
        emoji = str(payload.emoji)
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

        # Check if the user is on cooldown.
        if user in self.spam_protection.on_cooldown:
            try:
                # Attempt to send them a message (if they haven't been sent one already)
                if user not in self.spam_protection.cooldown_notified:
                    self.spam_protection.cooldown_notified.append(user)
                    await user.send(dedent("""
                        **You are currently on cooldown.**
                        Please wait around 30 seconds before trying to select roles again.
                        We have a cooldown to prevent spam of the reaction roles.
                    """))
            except:
                pass
            finally:
                # Remove their reaction.
                await message.remove_reaction(emoji, user)
            return

        # Check that the reaction added is valid.
        if emoji in self.reaction_to_role[category].keys():
            # Mark an event.
            self.spam_protection.mark_event(user)

            # Handle checking eligibility and adding the requested role.
            await self.reaction_role_add(
                user,
                self.reaction_to_role[category][emoji],
                category,
                message,
                emoji,
            )
        else:
            # The reaction added isn't an accepted one, so remove it.
            await message.remove_reaction(emoji, user)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Watches for when reactions are removed (in order to handle reaction roles).
        """
        # Ensure that the reaction user isn't the bot.
        if payload.user_id == self.bot.user.id:
            return

        # Check that the message is one of the reaction messages.
        category = next((name for name, id in self.selection_ids["message"].items() if id == payload.message_id), None)
        if not category:
            return

        # Fetch some info from the payload.
        emoji = str(payload.emoji)
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        user = message.guild.get_member(payload.user_id)

        # Check that the reaction removed was a valid one.
        if emoji in self.reaction_to_role[category].keys():
            # Handle removing the reaction role.
            await self.reaction_role_remove(
                user,
                self.reaction_to_role[category][emoji],
                category,
                message,
            )

def setup(bot) -> None:
    bot.add_cog(Reactions(bot))
