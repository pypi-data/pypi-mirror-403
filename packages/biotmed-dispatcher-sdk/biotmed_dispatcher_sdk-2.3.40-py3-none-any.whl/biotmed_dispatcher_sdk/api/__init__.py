# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from biotmed_dispatcher_sdk.api.health_check_api_api import HealthCheckAPIApi
    from biotmed_dispatcher_sdk.api.interception_api_api import InterceptionAPIApi
    from biotmed_dispatcher_sdk.api.subscription_api_api import SubscriptionAPIApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from biotmed_dispatcher_sdk.api.health_check_api_api import HealthCheckAPIApi
from biotmed_dispatcher_sdk.api.interception_api_api import InterceptionAPIApi
from biotmed_dispatcher_sdk.api.subscription_api_api import SubscriptionAPIApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
