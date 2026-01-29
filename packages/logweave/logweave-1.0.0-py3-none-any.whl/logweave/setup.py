from typing import Optional

from logweave._internal import setup_logging
from logweave.config import settings
from logweave.telemetry import setup_telemetry


def init(app: Optional[object] = None):
    """
    Initialize LogWeave for the application.
    Call ONCE at startup.
    """

    # 1. Logging backend
    setup_logging()

    # 2. OpenTelemetry (trace/span)
    if app:
        setup_telemetry(app)

    # 3. Sentry (errors only)
    if settings.LOG_MODE != "dev" and settings.SENTRY_DSN:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=1.0,
        )


#         from typing import Optional

# from logweave._internal import setup_logging
# from logweave.config import LOG_MODE, SENTRY_DSN
# from logweave.telemetry import setup_telemetry


# def init(app: Optional[object] = None):
#     """
#     Initialize LogWeave for the application.
#     Call ONCE at startup.
#     """

#     # 1. Logging backend (always)
#     setup_logging()

#     # 2. OpenTelemetry (ALWAYS for trace/span IDs)
#     setup_telemetry(app)

#     # 3. Sentry (errors only, optional)
#     if LOG_MODE != "dev" and SENTRY_DSN:
#         import sentry_sdk

#         sentry_sdk.init(
#             dsn=SENTRY_DSN,
#             traces_sample_rate=1.0,
#         )
