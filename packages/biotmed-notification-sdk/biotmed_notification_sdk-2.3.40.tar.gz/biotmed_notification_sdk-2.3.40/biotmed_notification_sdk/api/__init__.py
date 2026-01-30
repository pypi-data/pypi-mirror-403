# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from biotmed_notification_sdk.api.configuration_api_api import ConfigurationAPIApi
    from biotmed_notification_sdk.api.email_api_api import EmailAPIApi
    from biotmed_notification_sdk.api.health_check_api_api import HealthCheckAPIApi
    from biotmed_notification_sdk.api.smsapi_api import SMSAPIApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from biotmed_notification_sdk.api.configuration_api_api import ConfigurationAPIApi
from biotmed_notification_sdk.api.email_api_api import EmailAPIApi
from biotmed_notification_sdk.api.health_check_api_api import HealthCheckAPIApi
from biotmed_notification_sdk.api.smsapi_api import SMSAPIApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
