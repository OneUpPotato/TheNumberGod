from discord.ext.commands import Cog, command

from requests import get
from random import randint, choice

from utils.classes import NumEmbed

class Fun(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @command(aliases=["die", "roll"])
    async def dice(self, ctx) -> None:
        """
        Roll a 6-sided die.
        """
        await ctx.send(
            "",
            embed=NumEmbed(
                title="Dice Roll",
                description=f"You rolled a {randint(1, 6)}.",
                user=ctx.author,
            ),
        )

    @command(aliases=["8ball", "8-ball", "eight-ball"])
    async def eightball(self, ctx) -> None:
        """
        Generate an 8-ball response to a question.
        """
        await ctx.send(
            "",
            embed=NumEmbed(
                title="8-Ball",
                description=choice(
                    [
                        "As I see it, yes.",
                        "Ask again later.",
                        "Better not tell you now.",
                        "Cannot predict now.",
                        "Concentrate and ask again.",
                        "Don’t count on it.",
                        "It is certain.",
                        "It is decidedly so.",
                        "Most likely.",
                        "My reply is no.",
                        "My sources say no.",
                        "Outlook not so good.",
                        "Outlook good.",
                        "Reply hazy, try again.",
                        "Signs point to yes.",
                        "Very doubtful.",
                        "Without a doubt.",
                        "Yes.",
                        "Yes – definitely.",
                        "You may rely on it.",
                    ]
                ),
                footer_text="Please do not take responses from this seriously.",
                user=ctx.author,
            ),
        )

    @command(aliases=["fact", "numfact"])
    async def numberfact(self, ctx, number: int = None) -> None:
        """
        Get a fact about a random (or a specific) number.
        """
        fetched_info = {}
        if number == None:
            fetched_info = get("http://numbersapi.com/random/math?default=No%20fact%20found.&json").json()
        else:
            fetched_info = get(f"http://numbersapi.com/{number}/math?default=No%20fact%20found.&json").json()

        await ctx.send(
            "",
            embed=NumEmbed(
                title="Number Fact",
                colour=0x4F2D4E,
                fields={
                    "Number": fetched_info["number"],
                    "Result": f"**{fetched_info['type'].capitalize()}**: {fetched_info['text']}",
                },
                user=ctx.author,
            ),
        )

def setup(bot) -> None:
    bot.add_cog(Fun(bot))
