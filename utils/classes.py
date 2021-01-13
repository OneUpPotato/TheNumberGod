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
from discord import Embed, Colour, User, Member

from json import loads, dumps
from jsonmerge import merge

from textwrap import dedent
from num2words import num2words

from time import sleep
from typing import Union
from threading import Thread


class NumEmbed(Embed):
    def __init__(
        self,

        title: str,
        description: str = "",

        colour: Union[str, int, Colour] = "standard",

        url: str = "",
        fields: dict = None,

        thumbnail: str = "",

        footer_text: str = "",

        user: Union[User, Member] = None,
    ):
        # Parse colours given.
        if isinstance(colour, str):
            colour = self.get_colour(colour)
        elif isinstance(colour, int):
            colour = Colour(colour)

        # Initiate the embed.
        super().__init__(
            title=title,
            description=description,
            colour=colour,
            url=url,
        )

        if thumbnail:
            self.set_thumbnail(url=thumbnail)

        # Add the fields (if any).
        if fields:
            for k, v in fields.items():
                self.add_field(name=k, value=v, inline=True)

        # Add the requested by text to footer.
        if user:
            footer_text_prefix = f"Requested by {user}"
            if footer_text != "":
                footer_text_prefix += " | "
            footer_text = footer_text_prefix + footer_text
        self.set_footer(text=footer_text)

    def get_colour(self, name: str) -> Colour:
        """
        Get a colour from the colour palette.
        :return: Colour
        """
        colour_palette = {
            "standard": Colour(0x00688B),
            "highlight": Colour(0x3286A2),

            "success": Colour(0x00B200),
            "failure": Colour(0xFF0000),
        }

        return colour_palette[name]


class PointsLeaderboard:
    def __init__(self, reddit) -> None:
        self.reddit = reddit
        self.leaderboard = {"Numberless": 0, "000s": 0, "100s": 0, "200s": 0, "300s": 0, "400s": 0, "500s": 0, "600s": 0, "700s": 0, "800s": 0, "900s": 0}

        self.load()

    def load(self) -> None:
        """
        Loads the leaderboard from the Reddit wiki page.
        """
        loaded_leaderboard = loads(self.reddit.main_subreddit.wiki["points_leaderboard"].content_md)
        self.leaderboard = merge(self.leaderboard, loaded_leaderboard)

    def save(self) -> None:
        """
        Saves the leaderboard to the wiki page.
        """
        self.reddit.main_subreddit.wiki["points_leaderboard"].edit(dumps(self.leaderboard), reason="Updated points leaderboard.")

    @property
    def field_representation(self) -> dict:
        """
        Represents the points leaderboard in a dictionary (used for embeds).
        :return: The represented points leaderboard.
        """
        fields = {}
        for i, faction_points in enumerate(sorted(self.leaderboard.items(), key=lambda x: x[1], reverse=True)):
            fields[num2words((i + 1), to="ordinal_num")] = f"{faction_points[0]} ({faction_points[1]} points)"
        return fields

    def leaderboard_table(self, header: bool = True) -> str:
        """
        Generate a leaderboard table.
        :param header: Whether the table should have a header.
        :return: The generated markdown table.
        """
        table_text = ""
        if header is True:
            table_text = dedent("""
                |**Place**|**Nation**|**Points**|
                |:-|:-|:-|
            """).strip()

        table_row_template = "|{place}|{nation}|{points}|"
        for i, nation_points in enumerate(sorted(self.leaderboard.items(), key=lambda x: x[1], reverse=True)):
            table_text += "\n" + table_row_template.format(
                place=num2words((i + 1), to="ordinal_num"),
                nation=nation_points[0],
                points=nation_points[1],
            )

        return table_text.strip()

    def __repr__(self) -> str:
        return self.leaderboard_table()


class SpamProtection:
    """
    Prevents spam on certain functions of the bot. This is currently just used for reaction roles.
    After a certain amount of events in a certain amount of time, a user will be placed on cooldown.
    """
    def __init__(self):
        self.on_cooldown = []
        self.cooldown_notified = []

        self.event_count = {}

    def add_cooldown(self, user: Union[User, Member]):
        """
        Put a user on cooldown.
        :param user: The user to put on cooldown.
        """
        self.on_cooldown.append(user)
        Thread(target=self.schedule_cooldown_removal, args=[user]).start()

    def remove_cooldown(self, user: Union[User, Member]):
        """
        Remove a user's cooldown.
        :param user: The user whose cooldown should be removed.
        """
        self.on_cooldown.remove(user)

        if user in self.cooldown_notified:
            self.cooldown_notified.remove(user)

    def schedule_cooldown_removal(self, user: Union[User, Member]):
        """
        Schedule for a cooldown to be removed.
        :param user: The user whose cooldown should be removed.
        """
        sleep(30)
        self.remove_cooldown(user)

    def mark_event(self, user: Union[User, Member]):
        """
        Mark an event occuring with a certain user.
        :param user: The user who did something.
        """
        # Do not mark the event if the user is on cooldown.
        if user in self.on_cooldown:
            return

        # Increase the user's event count.
        if user in self.event_count.keys():
            self.event_count[user] += 1
        else:
            self.event_count[user] = 1

        # Schedule for the event count to be decreased in 60 seconds.
        Thread(target=self.schedule_event_count, args=[user]).start()

        # If the user has done a certain amount of events in a certain amount of time, then place them on cooldown.
        if self.event_count[user] == 3:
            self.add_cooldown(user)

    def schedule_event_count(self, user: Union[User, Member]):
        """
        Decreases a user's event count after 30 seconds.
        :param user: The user who's event count to decrease.
        """
        sleep(30)
        self.event_count[user] -= 1
