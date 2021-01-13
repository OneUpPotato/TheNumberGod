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
import praw


class TNGReddit(praw.Reddit):
    def __init__(self, auth_info, main_sub_name):
        self.main_sub_name = main_sub_name

        super().__init__(
            **auth_info,
            user_agent="Number Assignment Bot v2.1 (by u/OneUpPotato for r/Num)",
        )

        self.validate_on_submit = True

    @property
    def username(self):
        return self.user.me().name

    @property
    def main_subreddit(self):
        return self.subreddit(self.main_sub_name)

    def get_username_casing(self, username):
        """
        Gets the exact casing of a person's username.
        :param username: The user to get the exact casing for.
        :return: The casing used on their Reddit account.
        """
        try:
            user = self.redditor(username)
            user.id
            return user.name
        except Exception:
            return None

    def is_valid_user(self, username):
        """
        Checks if a user exists and is valid.
        :param username: The username to check.
        :return: Whether or not they are.
        """
        try:
            self.redditor(username).id
        except Exception:
            return False
        return True


reddit_instance = None
def initiate_reddit(auth_info, main_sub_name):
    global reddit_instance
    reddit_instance = TNGReddit(auth_info, main_sub_name)
    print(f"Initiated Reddit as u/{reddit_instance.username} | Main Subreddit: r/{main_sub_name}")


def get_reddit():
    return reddit_instance
