from pytz import utc
from datetime import datetime, timedelta, date

from requests import post

def get_time() -> datetime:
    """
    Get the current time in UTC.
    :return: Datetime of current time in UTC.
    """
    return datetime.now(utc)

def get_date() -> str:
    """
    Gets the current date in a certain format.
    :return: The date (in UTC) formatted as day/month/year (in a string).
    """
    return get_time().strftime("%d/%m/%Y")

def get_date_time() -> str:
    """
    Gets the current date and time in a certain format.
    :return: The date and time (in UTC) formatted as day/month/year hour/minute/second.
    """
    return get_time().strftime('%d/%m/%Y at %H:%M:%S')

def get_num_day() -> int:
    """
    Gets the current Num day.
    :return: The number of days since the 14th January 2020.
    """
    return int(((get_time() + timedelta(minutes=1)).date() - date(2020, 1, 14)).days)

def filter_username(username) -> str:
    """
    Removes '/u/' and 'u/' from a username.
    :return: The filtered username.
    """
    return username.replace("/u/", "").replace("u/", "")

def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Converts a given timestamp into a datetime.
    """
    return datetime.fromtimestamp(timestamp, utc)

def upload_text(text: str):
    """
    Uploads some text to hastebin and then returns a link to it.
    """
    response = post("https://hasteb.in/documents", data=text.encode("utf-8"))
    if str(response.status_code)[0] == "2":
        try:
            return f"https://hasteb.in/{response.json()['key']}"
        except:
            pass
    return None
