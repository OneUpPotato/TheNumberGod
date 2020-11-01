from yaml import safe_load
from jsonmerge import merge
from dotenv import load_dotenv

from sys import exit
from os import getenv

class Settings:
    def __init__(self) -> None:
        # Load the .env file.
        load_dotenv(verbose=True)

        # Define some hardcoded standard settings. (currently not used)
        self.settings = {}

        # Load the settings YAML file.
        try:
            with open("settings.yml", "r", encoding="utf8") as settings_text:
                self.settings = merge(self.settings, safe_load(settings_text.read()))
        except Exception as e:
            print(f"{e} - Error loading/reading the settings file.")
            exit()

        # Initiate the subclasses.
        self.reddit = self.reddit(self)
        self.discord = self.discord(self)
        self.templates = self.templates(self)

    def load_wiki_settings(self, reddit_instance) -> None:
        """
        Loads settings from the subreddit wiki page.
        """
        reddit_wiki_settings = safe_load(reddit_instance.main_subreddit.wiki["botsettings"].content_md)
        self.settings = merge(self.settings, reddit_wiki_settings)
        print("Loaded the Reddit wiki settings.")

    class reddit:
        def __init__(self, parent) -> None:
            self.parent = parent

            self.assignment = self.assignment(self.parent, self)

        @property
        def auth_info(self) -> dict:
            return dict({
                "client_id": getenv("REDDIT_CLIENT_ID"),
                "client_secret": getenv("REDDIT_CLIENT_SECRET"),
                "refresh_token": getenv("REDDIT_REFRESH_TOKEN"),
            })

        @property
        def subreddit(self) -> str:
            return self.parent.settings["subreddit"]

        class assignment:
            def __init__(self, main_parent, sub_parent) -> None:
                self.parent = main_parent
                self.sub_parent = sub_parent

            @property
            def id(self) -> str:
                return self.parent.settings["assignment"]["watch"]["submission_id"]

            @property
            def flair(self) -> dict:
                return self.parent.settings["assignment"]["flair"]

            @property
            def numbers(self) -> dict:
                return self.parent.settings["assignment"]["numbers"]

            @property
            def requirements(self) -> dict:
                return self.parent.settings["assignment"]["requirements"]

            @property
            def blacklisted_numbers(self) -> list:
                return self.parent.settings["assignment"]["numbers"]["blacklist"]

            @property
            def reply_messages(self) -> list:
                return self.parent.settings["assignment"]["watch"]["reply_messages"]

            @property
            def not_eligible_msg(self) -> str:
                return self.parent.settings["assignment"]["watch"]["not_eligible_msg"]

    class discord:
        def __init__(self, parent) -> None:
            self.parent = parent

            self.discord = self.parent.settings["discord"]

            self.role_ids = self.role_ids(self.parent, self)

        @property
        def prefix(self) -> str:
            return getenv("BOT_PREFIX")

        @property
        def token(self) -> str:
            return getenv("BOT_DISCORD_KEY")

        @property
        def main_guild(self) -> int:
            return self.discord["ids"]["main_guild"]

        @property
        def admins(self) -> list:
            return self.discord["admins"]

        @property
        def developers(self) -> list:
            return self.discord["developers"]

        @property
        def reaction_roles(self) -> dict:
            return self.discord["reaction_roles"]

        @property
        def ids(self) -> dict:
            return self.discord["ids"]

        class role_ids:
            def __init__(self, main_parent, sub_parent) -> None:
                self.main_parent = main_parent
                self.parent = sub_parent

                self.role_ids = self.parent.discord["role_ids"]

            @property
            def nations(self) -> dict:
                return self.role_ids["nations"]

            @property
            def countries(self) -> dict:
                return self.role_ids["countries"]

            @property
            def organizations(self) -> dict:
                return self.role_ids["organizations"]

            @property
            def odd_and_even(self) -> dict:
                return self.role_ids["odd_and_even"]

            @property
            def ping_notifications(self) -> dict:
                return self.role_ids["ping_notifications"]

            @property
            def other(self) -> dict:
                return self.role_ids["other"]

            def __repr__(self) -> dict:
                return self.role_ids

        def __repr__(self) -> dict:
            return self.discord

    class templates:
        def __init__(self, parent) -> None:
            self.parent = parent

            self.templates = self.parent.settings["templates"]

        @property
        def verification(self) -> dict:
            return self.templates["verification"]

        @property
        def num_day_update(self) -> dict:
            return self.templates["num_day_update"]

        @property
        def widgets(self) -> dict:
            return self.templates["widgets"]

        def __repr__(self) -> dict:
            return self.templates

    @property
    def sentry_link(self) -> str:
        return getenv("SENTRY_LINK")

    def __repr__(self) -> dict:
        return self.settings

def init_settings():
    global settings_instance
    settings_instance = Settings()
    return settings_instance

def get_settings():
    return settings_instance
