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

from time import sleep
from random import choice
from textwrap import dedent
from threading import Thread
from asyncio import run_coroutine_threadsafe

from utils.classes import NumEmbed
from utils.wrappers import stream_wrapper
from utils.numbers import is_allowed_number


class Assignment(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        # These are the users who have already been told they're not eligible for a number.
        self.refused_already = []

        # Watches the comments on the assignment thread.
        self.comments_thread = Thread(target=self.watch_comments)
        self.comments_thread.start()

        print("ASSIGNMENT: Watching assignment thread comments.")

    async def send_assignment_feed_message(self, username: str, number: int) -> None:
        """
        Sends an assignment message to the feed.
        :param username: The username of the user who has just received a number.
        :param number: The number of the user who has just received a number.
        """
        number_feed_channel = self.bot.get_channel(self.bot.settings.discord.ids["feed_channels"]["number_feed"])
        await number_feed_channel.send(
            "",
            embed=NumEmbed(
                title="",
                colour=0x000080,
                fields={
                    "Reddit User": f"u/{username}",
                    "Number": number,
                },
            ),
        )

    def get_reply_message(self, number: int) -> str:
        """
        Generates a reply message to send after assigning a number.
        :param number: The number that has just been assigned.
        :return: The generated message.
        """
        number_parity = self.bot.numbers.checks.parity(number)
        nation_and_countries = self.bot.numbers.checks.nation_and_countries(number)
        reply_message_template = choice(self.bot.settings.reddit.assignment.reply_messages)

        main_reply_template = dedent("""
            This number is {parity} and belongs to the **'{nation}' Nation**

            **Number Countries(s)** **^(that you are eligible for):**
            {countries}

            [Learn more about groups here.](https://numbergod.fandom.com/wiki/List_of_Groups)
        """).strip()

        countries = "\n".join([f"* {country[0]} | {country[1]}" for country in nation_and_countries["countries"]])
        return reply_message_template.format(number) + "\n\n" + main_reply_template.format(
            parity=number_parity,
            nation=nation_and_countries['nation'][0],
            countries=countries,
        )

    @stream_wrapper
    def watch_comments(self) -> None:
        """
        Watches for comments made on the main subreddit. Then assigns numbers to comments in the assignment thread.
        """
        # Start a comments stream.
        for comment in self.bot.reddit.main_subreddit.stream.comments(skip_existing=True):
            # Check that the comment was made on the assignment thread.
            # If it wasn't then continue on to review the next comment.
            if comment.submission.id != self.bot.settings.reddit.assignment.id:
                continue

            # Ensure that the comment is a top-level comment.
            if comment.parent_id[:2] != "t3":
                continue

            # Ensure that the author isn't the bot and doesn't have a flair.
            user_flair = next(self.bot.reddit.main_subreddit.flair(comment.author.name))['flair_text']
            if (
                comment.author.name == self.bot.reddit.user.me().name or user_flair not in [None, ""]
            ):
                continue

            # Ensure that the comment author is eligible for a number.
            if not is_allowed_number(comment.author):
                if comment.author not in self.refused_already:
                    self.refused_already.append(comment.author)
                    comment.reply(self.bot.settings.reddit.assignment.not_eligible_msg)
                continue

            # Assign the user a number.
            number = self.bot.numbers.assignment.assign_number(comment.author.name)
            comment.reply(self.get_reply_message(number))

            # Attempt to send a message to the number feed.
            run_coroutine_threadsafe(
                self.send_assignment_feed_message(
                    comment.author.name,
                    number,
                ),
                self.bot.loop,
            )


def setup(bot) -> None:
    bot.add_cog(Assignment(bot))
