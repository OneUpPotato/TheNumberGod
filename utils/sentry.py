import sentry_sdk

def initiate_sentry(url) -> None:
    sentry_sdk.init(url)

def get_sentry() -> sentry_sdk:
    return sentry_sdk
