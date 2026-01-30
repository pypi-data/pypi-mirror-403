# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from biotmed_measurement_sdk.api.health_check_api_api import HealthCheckAPIApi
    from biotmed_measurement_sdk.api.measurements_api_api import MeasurementsAPIApi
    from biotmed_measurement_sdk.api.measurements_v2_api_api import MeasurementsV2APIApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from biotmed_measurement_sdk.api.health_check_api_api import HealthCheckAPIApi
from biotmed_measurement_sdk.api.measurements_api_api import MeasurementsAPIApi
from biotmed_measurement_sdk.api.measurements_v2_api_api import MeasurementsV2APIApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
