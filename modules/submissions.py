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

from praw.models import Submission

from time import sleep
from threading import Thread
from asyncio import run_coroutine_threadsafe

from utils.classes import NumEmbed
from utils.wrappers import stream_wrapper
from utils.helpers import timestamp_to_datetime


class Submissions(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        # Watches the submissions on the subreddit.
        self.submissions_thread = Thread(target=self.watch_submissions)
        self.submissions_thread.start()

        print("SUBMISSIONS: Watching submissions.")

    async def send_submissions_feed_message(self, submission: Submission) -> None:
        """
        Sends a message to the submissions feed channel.
        :param submission: The submission to send a message for.
        """
        submissions_feed_channel = self.bot.get_channel(self.bot.settings.discord.ids["feed_channels"]["submissions_feed"])

        submission_embed = NumEmbed(
            title=submission.title,
            description=f"Posted by u/{submission.author.name}",
            url=f"https://reddit.com{submission.permalink}",
            colour=0x202225,
        )

        if submission.domain.lower() == "i.redd.it":
            submission_embed.set_thumbnail(url=submission.url)

        submission_embed.set_author(
            name=f"r/{self.bot.reddit.main_sub_name} - New Submission",
            icon_url="https://styles.redditmedia.com/t5_2z5lj/styles/communityIcon_nnjpwqb5ozb41.png"
        )

        submission_embed.timestamp = timestamp_to_datetime(submission.created_utc)

        await submissions_feed_channel.send("", embed=submission_embed)

    @stream_wrapper
    def watch_submissions(self) -> None:
        """
        Watches for submissions made on the main subreddit and then sends them to the submissions feed.
        """
        # Start a submissions stream.
        for submission in self.bot.reddit.main_subreddit.stream.submissions(skip_existing=True):
            # Attempt to send a message to the submissions feed.
            run_coroutine_threadsafe(
                self.send_submissions_feed_message(submission),
                self.bot.loop,
            )


def setup(bot) -> None:
    bot.add_cog(Submissions(bot))
