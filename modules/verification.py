from discord.utils import get
from discord.ext.commands import Cog, command, check, bot_has_permissions
from discord.ext.commands.errors import MissingRequiredArgument, BotMissingPermissions

from random import randint

from textwrap import dedent

from utils.classes import NumEmbed
from utils.helpers import filter_username
from utils.numbers import get_number_nation
from utils.errors import AlreadyVerifiedCheckFailure
from utils.checks import is_in_main_guild, is_verified, is_not_verified

class VerificationHandler:
    def __init__(self, bot) -> None:
        self.bot = bot

    def generate_code(self) -> int:
        code = ""
        for _ in range(6):
            code += str(randint(0, 9))
        return int(code)

    def get_initial_roles(self, number) -> list:
        """
        Gets the initial roles that should be assigned to the user.
        :param number: The number to get the initial roles for.
        :return: A list of the role ids.
        """
        role_ids = []
        if number != None:
            role_ids = [
                self.bot.settings.discord.role_ids.nations[get_number_nation(number)],
                self.bot.settings.discord.role_ids.odd_and_even[self.bot.numbers.checks.parity(number)],
            ]
        else:
            role_ids = [
                self.bot.settings.discord.role_ids.other["Numberless"],
            ]
        role_ids.append(self.bot.settings.discord.role_ids.other["Verified"])
        return role_ids

    async def assign_roles(self, user, role_ids, guild) -> None:
        for role_id in role_ids:
            try:
                role = get(guild.roles, id=role_id)
                await user.add_roles(role)
            except Exception as e:
                print(f"VERIFICATION HANDER: Error fetching role: {role_id} - {e}")
                pass

    async def remove_roles(self, user) -> None:
        for role in user.roles:
            try:
                roles_to_remove = (
                    list(self.bot.settings.discord.role_ids.nations.values()) +
                    list(self.bot.settings.discord.role_ids.countries.values()) +
                    list(self.bot.settings.discord.role_ids.organizations.values()) +
                    list(self.bot.settings.discord.role_ids.odd_and_even.values()) +
                    [self.bot.settings.discord.role_ids.other["Numberless"]]
                )
                if role.id in roles_to_remove:
                    await user.remove_roles(role)
            except:
                pass

class Verification(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.pending_verification = {}
        self.verification_handler = VerificationHandler(self.bot)

    @check(is_in_main_guild)
    @check(is_not_verified)
    @command()
    async def verify(self, ctx, username: filter_username) -> None:
        """
        Verify yourself using your Reddit account.
        """
        # Make sure that the user isn't already pending verification.
        if ctx.author.id in self.pending_verification:
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Verification",
                    description="You are already pending verification.",
                    colour="failure",
                    user=ctx.author,
                ),
            )
            return

        # Make sure that the username is valid.
        if not self.bot.reddit.is_valid_user(username):
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Verification",
                    description="That is an invalid Reddit user.",
                    colour="failure",
                    user=ctx.author,
                ),
            )

        # Generate a random verification code.
        # Add the user to the pending verification dict.
        verification_code = self.verification_handler.generate_code()
        self.bot.reddit.redditor(username).message(
            "Discord Verification for r/Num",
            self.bot.settings.templates.verification["reddit_pm"].format(
                verification_code=verification_code,
                discord_user_str=str(ctx.author),
                discord_user_id=ctx.author.id,
            ),
        )
        self.pending_verification[ctx.author.id] = {"code": verification_code, "username": username}

        # Send a message to the user asking them to check their Reddit inbox.
        await ctx.send(
            ctx.author.mention,
            embed=NumEmbed(
                title="Verification",
                description="A code has been sent to your Reddit inbox.\nPlease reply with '$confirm (code)' here.",
                colour=0X007E80,
                user=ctx.author,
            ),
        )

        # Send a message to the (pending) verification log channel.
        verif_log_channel = self.bot.get_channel(self.bot.settings.discord.ids["log_channels"]["verification_log"])
        await verif_log_channel.send(
            "",
            embed=NumEmbed(
                title="Pending Verification",
                colour=0x000080,
                fields={
                    "Claimed Reddit Name": f"u/{username}",
                    "Discord User": f"{ctx.author}\n{ctx.author.mention}\n{ctx.author.id}",
                },
            ),
        )

    @verify.error
    async def verify_error(self, ctx, error) -> None:
        """
        Handles errors raised from the verify command.
        """
        print(f"{type(error)}: {error}")
        if isinstance(error, AlreadyVerifiedCheckFailure):
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Verification",
                    description="You are already verified.\nTo update your information use the '$update' command.",
                    colour="failure",
                    user=ctx.author,
                ),
            )
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Verification",
                    description="The correct usage is \"$verify (REDDIT USERNAME)\".",
                    colour="failure",
                    user=ctx.author,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Verification",
                    description="Something went wrong. Please try again later.",
                    colour="failure",
                    user=ctx.author,
                ),
            )

    @check(is_in_main_guild)
    @check(is_not_verified)
    @command()
    async def confirm(self, ctx, code: int) -> None:
        """
        Input your verification code. (use the verify command first)
        """
        # Ensure that the user is already pending verification.
        if ctx.author.id not in self.pending_verification.keys():
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Confirmation",
                    description=f"You are not currently pending verification.\nPlease use '{self.bot.settings.discord.prefix}verify (reddit username)' first.",
                    colour="failure",
                    user=ctx.author,
                ),
            )
            return

        # Check that the input code is correct.
        verification_info = self.pending_verification[ctx.author.id]
        if verification_info["code"] != code:
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Confirmation",
                    description="That is not the correct verification code.",
                    colour="failure",
                    user=ctx.author,
                ),
            )
            return

        # Ensure that the user is still valid.
        if not self.bot.reddit.is_valid_user(verification_info["username"]):
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Confirmation",
                    description=f"u/{verification_info['username']} is no longer a valid Reddit user.",
                    colour="failure",
                    user=ctx.author,
                ),
            )
            del self.pending_verification[ctx.author.id]
            return

        # Process the verification confirmation.
        # Try to delete the user's confirm message, then remove their old roles (if any).
        try:
            await ctx.message.delete()
        except:
            pass
        finally:
            await self.verification_handler.remove_roles(ctx.author)

        # Get the user's number then set their nickname.
        username = self.bot.reddit.get_username_casing(verification_info["username"])
        number = self.bot.numbers.search.user_to_num(verification_info["username"])
        await ctx.author.edit(nick=f"{number} | {username}")

        # Get the user's initial roles and then assign them.
        initial_roles = self.verification_handler.get_initial_roles(number)
        await self.verification_handler.assign_roles(ctx.author, initial_roles, ctx.guild)

        # Attempt to send a message to the user. Then send a message to the confirmation log.
        info_msg = self.bot.settings.templates.verification["verified_pm"]
        number_nation = "Numberless"
        number_parity = "N/A"
        if number != None:
            nation_and_countries = self.bot.numbers.checks.nation_and_countries(number)
            number_nation = nation_and_countries["nation"][0]
            number_parity = self.bot.numbers.checks.parity(number)

            countries = "\n".join([f"* {country_info[0]}" for country_info in nation_and_countries["countries"]])

            info_msg = info_msg.format(
                username=username,
                number_information=f"You are number #{number}. Your number nation is the {number_nation}.\nYou are eligible for the following countries:\n{countries}",
            )
        else:
            info_msg = info_msg.format(
                username=username,
                number_information=f"You currently do not have a number assigned. When/if you get a number, use the '{self.bot.settings.discord.prefix}update' command to update it on Discord."
            )

        try:
            await ctx.author.send(info_msg)
        except:
            pass
        finally:
            confirm_log_channel = self.bot.get_channel(self.bot.settings.discord.ids["log_channels"]["confirmation_log"])
            await confirm_log_channel.send(
                "",
                embed=NumEmbed(
                    title="Successful User Confirmation",
                    colour="success",
                    fields={
                        "Number": number,
                        "Reddit": f"u/{username}",
                        "Discord User": f"{ctx.author}\n{ctx.author.mention}\n{ctx.author.id}",
                        "Nation": number_nation,
                        "Odd/Even": number_parity,
                    },
                ),
            )

    @confirm.error
    async def confirm_error(self, ctx, error) -> None:
        """
        Handles errors raised from the confirm command.
        """
        print(f"{type(error)}: {error}")
        if isinstance(error, AlreadyVerifiedCheckFailure):
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Verification",
                    description="You are already verified.\nTo update your information use the '$update' command.",
                    colour="failure",
                    user=ctx.author,
                ),
            )
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Confirmation",
                    description="The correct usage is \"{self.bot.settings.discord.prefix}confirm (CONFIRMATION CODE)\".\nYou can find the confirmation code in your Reddit inbox after using the verify command.",
                    colour="failure",
                    user=ctx.author,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Confirmation",
                    description="Something went wrong. Please try again later.",
                    colour="failure",
                    user=ctx.author,
                ),
            )

    @check(is_in_main_guild)
    @check(is_verified)
    @command()
    async def update(self, ctx) -> None:
        """
        Update your number information on Discord (should your number change).
        """
        current_info = ctx.author.display_name.split(" | ")
        username = current_info[1]
        nick_number = int(current_info[0])

        # Check that the user is valid on Reddit. If not then remove their verification roles.
        if not self.bot.reddit.is_valid_user(username):
            try:
                await ctx.author.send(
                    "",
                    embed=NumEmbed(
                        title="Updating",
                        description="Your username was not found to be a valid Reddit user.\nYou've been unverified, but are free to verify again.",
                        colour="failure",
                        user=ctx.author,
                    ),
                )
            except:
                pass
            finally:
                await self.verification_handler.remove_roles(ctx.author)
            return

        # Check to see if the user's number has changed.
        number = self.bot.numbers.search.user_to_num(username)
        if number == nick_number:
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="Updating",
                    description="Your number has not changed.",
                    colour="failure",
                    user=ctx.author,
                ),
            )
            return

        # Process the update.
        await self.verification_handler.remove_roles(ctx.author)
        await ctx.author.edit(nick=f"{number} | {username}")

        # Get the initial roles and then assign them.
        initial_roles = self.verification_handler.get_initial_roles(number)
        await self.verification_handler.assign_roles(ctx.author, initial_roles, ctx.guild)

        # Send a message to the user.
        await ctx.send(
            "",
            embed=NumEmbed(
                title="Update",
                description="Succesfully updated your nickname and roles to your new number.",
                user=ctx.author,
            ),
        )

        # Send a message to the update log.
        update_log_channel = self.bot.get_channel(self.bot.settings.discord.ids["log_channels"]["update_log"])
        await update_log_channel.send(
            "",
            embed=NumEmbed(
                title="Successful Update",
                colour="success",
                fields={
                    "Old Number": nick_number,
                    "New Number": number,
                    "Username": f"u/{username}",
                    "Discord User": f"{ctx.author}\n{ctx.author.mention}\n{ctx.author.id}",
                },
            ),
        )

def setup(bot) -> None:
    bot.add_cog(Verification(bot))
