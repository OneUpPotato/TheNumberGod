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
from prawcore import PrawcoreException

from time import sleep
from functools import wraps

from utils.sentry import get_sentry


def stream_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            try:
                func(*args, **kwargs)
            except SystemExit:
                return
            except PrawcoreException as e:
                print(f"PRAW STREAM: {e} - PRAW error raised.")
                sleep(30)
            except Exception as e:
                sentry = get_sentry()
                if sentry:
                    sentry.capture_exception(e)
                print(f"PRAW STREAM: Error raised {e}.")
    return wrapper
