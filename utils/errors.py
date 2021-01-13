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
from discord.ext.commands import CheckFailure


class ModeratorCheckFailure(CheckFailure):
    """
    Raised when a check to see if user is a Discord moderator returns false.
    """
    pass


class AdminCheckFailure(CheckFailure):
    """
    Raised when a user without admin perms attempts to use admin commands.
    """
    pass


class DeveloperCheckFailure(CheckFailure):
    """
    Raised when a non-developer attempts to use developer commands.
    """
    pass


class VerifiedCheckFailure(CheckFailure):
    """
    Raised when a user is not verified.
    """
    pass


class AlreadyVerifiedCheckFailure(CheckFailure):
    """
    Raised when a user is already verified.
    """
    pass


class MainGuildCheckFailure(CheckFailure):
    """
    Raised when a command is found not to be run inside the main guild in a check.
    """
    pass


class NotMainGuildCheckFailure(CheckFailure):
    """
    Raised when a not main guild check fails.
    """
    pass
