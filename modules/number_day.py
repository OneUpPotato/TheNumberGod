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
from discord.ext.commands import Cog
from discord.ext.tasks import loop

from textwrap import dedent

from praw.models import TextArea

from asyncio import sleep
from datetime import timedelta

from utils.classes import NumEmbed
from utils.numbers import get_number_nation
from utils.helpers import get_time, get_date, get_num_day


class NumberDayHandler(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.widget_templates = self.bot.settings.templates.widgets

    @Cog.listener()
    async def on_ready(self) -> None:
        # Start the number day update timer.
        self.number_day_update.start()

        # Update the sidebar and widget.
        await self.update_widgets()

    async def update_widgets(self) -> None:
        """
        Updates the sidebar and widget with the points leaderboard and current num day.
        """
        current_num_day = get_num_day()
        points_leaderboard = self.bot.points_leaderboard

        # Update the sidebar widget.
        widget = self.bot.reddit.main_subreddit.widgets.sidebar[0]
        if isinstance(widget, TextArea):
            widget.mod.update(
                text=self.widget_templates["widget"].format(
                    num_day=current_num_day,
                    points_leaderboard=points_leaderboard,
                    subreddit=self.bot.settings.reddit.subreddit,
                    assignment_thread=self.bot.settings.reddit.assignment.id,
                )
            )

        # Update the main sidebar.
        self.bot.reddit.main_subreddit.wiki['config/sidebar'].edit(
            self.widget_templates["sidebar"].format(
                num_day=current_num_day,
                points_leaderboard=points_leaderboard,
                subreddit=self.bot.settings.reddit.subreddit,
                assignment_thread=self.bot.settings.reddit.assignment.id,
            )
        )

    @loop(count=1)
    async def number_day_update(self) -> None:
        """
        This updates the number day and assigns the daily points.
        """
        current_date = get_date()
        current_num_day = get_num_day()

        # Get a random user for Number of the Day.
        notd, notd_user = self.bot.numbers.generation.get_random_user()

        # Get the statistics for the currently assigned numbers.
        number_statistics = self.bot.numbers.statistics

        # Assign points for the top 3 submissions of the day.
        submissions = []
        for submission in self.bot.reddit.main_subreddit.top("day", limit=4):
            if submission.author.name != self.bot.reddit.username:
                submissions.append(submission)

        assigned_points_text = dedent("""
            |**Submission**|**Username**|**Nation**|**Points Awarded**|
            |:-|:-|:-|:-|
        """).strip()
        assigned_points_row = "|[{title}](https://reddit.com{permalink})|u/{author}|{nation}|{points_awarded}|"

        points_leaderboard = self.bot.points_leaderboard

        submissions = submissions[:3]
        for submission in submissions:
            try:
                username = submission.author.name
                user_number = self.bot.numbers.search.user_to_num(username)
                user_nation = "Numberless"
                if user_number is not None:
                    user_nation = get_number_nation(user_number)
                elif username == "OneUpPotato":
                    user_nation = "000s"

                # Increase the points for that nation.
                points_leaderboard.leaderboard[user_nation] += 1

                assigned_points_text += "\n" + assigned_points_row.format(
                    title=submission.title,
                    permalink=submission.permalink,
                    author=submission.author.name,
                    nation=user_nation,
                    points_awarded=1,
                )
            except Exception:
                pass

        if len(submissions) == 0:
            assigned_points_text = "No points have been assigned today."

        # Post the Num Day Update submission.
        submission_text = self.bot.settings.templates.num_day_update["submission_text"].format(
            num_day=current_num_day,
            notd=notd,
            notd_user=notd_user,

            # Statistics
            stats_assigned=number_statistics["numbers_given"],
            stats_odd=number_statistics["odds"],
            stats_even=number_statistics["evens"],
            stats_mean=number_statistics["mean"],
            stats_median=number_statistics["median"],
            stats_sum=number_statistics["sum"],

            points_leaderboard_text=points_leaderboard.leaderboard_table(header=False),
            new_assigned_points_text=assigned_points_text.strip(),

            subreddit=self.bot.settings.reddit.subreddit,
            assignment_thread=self.bot.settings.reddit.assignment.id,
        )

        submission = self.bot.reddit.main_subreddit.submit(f"Daily Update ({current_date}) - Day #{current_num_day}", selftext=submission_text)

        # Send a message to the Number of the Day feed on Discord.
        notd_channel = self.bot.get_channel(self.bot.settings.discord.ids["feed_channels"]["notd"])
        notd_ping = f"<@&{self.bot.settings.discord.role_ids.ping_notifications['Number of the Day']}>"
        await notd_channel.send(
            notd_ping,
            embed=NumEmbed(
                title=f"Num Day #{current_num_day} - {current_date}",
                fields={
                    "Number of the Day": f"#{notd} (u/{notd_user})",
                    "Awarded Points": "View the submission.",
                },
                colour=0x739AAF,
                url=f"https://reddit.com{submission.permalink}",
            ),
        )

        # Save the updated leaderboard and update the widgets.
        points_leaderboard.save()
        await self.update_widgets()

    @number_day_update.before_loop
    async def before_number_day_update(self) -> None:
        """
        Wait until midnight UTC before doing the number day update.
        """
        current_time = get_time()
        time_remaining = (timedelta(hours=24) - (current_time - current_time.replace(hour=0, minute=0, second=0, microsecond=0))).total_seconds() % (24 * 3600)
        await sleep(time_remaining)
        await self.bot.wait_until_ready()

    @number_day_update.after_loop
    async def after_number_day_update(self) -> None:
        print("NUMBER DAY: Updated. Starting the timer again.")
        self.number_day_update.restart()


def setup(bot) -> None:
    bot.add_cog(NumberDayHandler(bot))
