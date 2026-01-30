# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from biotmed_generic_entity_sdk.api.generic_entity_api_api import GenericEntityAPIApi
    from biotmed_generic_entity_sdk.api.health_check_api_api import HealthCheckAPIApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from biotmed_generic_entity_sdk.api.generic_entity_api_api import GenericEntityAPIApi
from biotmed_generic_entity_sdk.api.health_check_api_api import HealthCheckAPIApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
