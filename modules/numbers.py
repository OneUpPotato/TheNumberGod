from discord.ext.commands import Cog, command

from utils.classes import NumEmbed
from utils.helpers import filter_username

class Numbers(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @command(aliases=["statistics", "numstats", "numberstats"])
    async def stats(self, ctx) -> None:
        """
        Gets some statistics on the assigned numbers.
        """
        stats = self.bot.numbers.statistics
        await ctx.send(
            "",
            embed=NumEmbed(
                title="Number Statistics",
                colour=0x007E80,
                fields={
                    "Numbers Given": stats["numbers_given"],
                    "Even Numbers": stats["evens"],
                    "Odd Numbers": stats["odds"],

                    "Highest Number": stats["highest_info"],
                    "Lowest Positive": stats["lowest_positive_info"],
                    "Lowest Number": stats["lowest_info"],

                    "Sum of Numbers": stats["sum"],
                    "Mean": stats["mean"],
                    "Median": stats["median"],

                    "Below 500": stats["below_500"],
                    "Below 1000": stats["below_1000"],
                    "Below 2500": stats["below_2500"],
                },
                user=ctx.author,
            ),
        )

    @command(aliases=["num", "check", "nation", "country", "countries", "search"])
    async def number(self, ctx, number: int) -> None:
        """
        Find which user has a number and which countries a number is eligible for.
        """
        number_user = self.bot.numbers.search.num_to_user(number)
        nation_and_countries = self.bot.numbers.checks.nation_and_countries(number)

        countries = "\n".join([f"• {country[0]}" for country in nation_and_countries["countries"]])
        await ctx.send(
            "",
            embed=NumEmbed(
                title="NGB - Number Search",
                colour=0x00C9CC,
                fields={
                    "Number": f"#{number}",
                    "Number User": f"u/{number_user}" if number_user != None else "No One" if number != 404 else "Error 404\nNot Found",
                    "Nation": nation_and_countries["nation"][0],
                    "Odd/Even": self.bot.numbers.checks.parity(number),
                    "Eligible Countries": countries,
                },
                user=ctx.author,
            ),
        )

    @command(aliases=["user", "find"])
    async def username(self, ctx, username: filter_username):
        """
        See what number a specified user has.
        """
        user_number = self.bot.numbers.search.user_to_num(username)

        # Ensure that the user has a number.
        if user_number == None:
            await ctx.send(
                "",
                embed=NumEmbed(
                    title="NGB - User Search",
                    description="That user doesn't have a number.",
                    colour=0x3CBD70,
                    user=ctx.author,
                ),
            )
            return

        # That user has a number, so send a message.
        await ctx.send(
            "",
            embed=NumEmbed(
                title="NGB - User Search",
                colour=0x3CBD70,
                fields={
                    "Number": f"#{user_number}",
                    "Username": f"u/{username}",
                },
                user=ctx.author,
            ),
        )

    @command(aliases=["lb", "points", "pointsleaderboard"])
    async def leaderboard(self, ctx) -> None:
        """
        View the current points leaderboard.
        """
        await ctx.send(
            "",
            embed=NumEmbed(
                title="Points Leaderboard",
                fields=self.bot.points_leaderboard.field_representation,
                user=ctx.author,
            ),
        )

def setup(bot) -> None:
    bot.add_cog(Numbers(bot))
