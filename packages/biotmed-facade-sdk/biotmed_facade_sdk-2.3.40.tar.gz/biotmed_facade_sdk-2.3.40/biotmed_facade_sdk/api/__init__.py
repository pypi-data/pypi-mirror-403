# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from biotmed_facade_sdk.api.health_check_api_api import HealthCheckAPIApi
    from biotmed_facade_sdk.api.patient_sign_up_api_api import PatientSignUpAPIApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from biotmed_facade_sdk.api.health_check_api_api import HealthCheckAPIApi
from biotmed_facade_sdk.api.patient_sign_up_api_api import PatientSignUpAPIApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
