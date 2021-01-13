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
import discord
from discord.ext import tasks, commands

import logging
from traceback import print_exc

from os import path
from glob import glob
from pygount import ProjectSummary, SourceAnalysis

from utils.numbers import Numbers
from utils.settings import init_settings
from utils.reddit import initiate_reddit, get_reddit
from utils.sentry import initiate_sentry, get_sentry
from utils.classes import NumEmbed, PointsLeaderboard


class TheNumberGod(commands.Bot):
    def __init__(self) -> None:
        # Load the configs.
        self.settings = init_settings()

        # Initiate sentry.
        initiate_sentry(self.settings.sentry_link)
        self.sentry = get_sentry()

        # Initiate the Reddit instance.
        initiate_reddit(auth_info=self.settings.reddit.auth_info, main_sub_name=self.settings.reddit.subreddit)
        self.reddit = get_reddit()
        self.settings.load_wiki_settings(self.reddit)

        # Load the numbers.
        self.numbers = Numbers(reddit=self.reddit, settings=self.settings)

        # Load the points leaderboard.
        self.points_leaderboard = PointsLeaderboard(self.reddit)

        # Calculate the number of lines of code used.
        self.calculate_loc()

        # Start the Discord bot logger.
        logger = logging.getLogger("discord")
        logger.setLevel(logging.WARNING)
        handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
        handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
        logger.addHandler(handler)

        # Initiate the Discord bot instance.
        super().__init__(
            command_prefix=commands.when_mentioned_or(self.settings.discord.prefix),
            description=f"The Number God (for r/{self.settings.reddit.subreddit})",
            case_insensitive=True,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"r/{self.settings.reddit.subreddit}",
            ),
        )

        # Load the modules.
        for module in [
            module.replace(".py", "")
            for module in map(path.basename, glob("modules/*.py"))
        ]:
            try:
                self.load_extension(f"modules.{module}")
                print(f"MODULES: Loaded '{module}'.")
            except Exception:
                print(f"MODULES: Failed to load '{module}'.")
                print_exc()
                pass

        # Run the bot.
        self.run(self.settings.discord.token)

    def calculate_loc(self) -> None:
        """
        Calculates the number of lines of code that are used by TNG.
        """
        project_summary = ProjectSummary()
        for source_path in (glob("*.py") + glob("modules/*.py") + glob("utils/*.py")):
            source_analysis = SourceAnalysis.from_file(source_path, "pygount", encoding="utf-8", fallback_encoding="cp850")
            project_summary.add(source_analysis)

        self.lines_of_code = 0
        for language_summary in project_summary.language_to_language_summary_map.values():
            self.lines_of_code += language_summary.code_count

    async def on_ready(self) -> None:
        print("Loaded Discord succesfully.")


if __name__ == "__main__":
    # Initiate the bot.
    TheNumberGod()
