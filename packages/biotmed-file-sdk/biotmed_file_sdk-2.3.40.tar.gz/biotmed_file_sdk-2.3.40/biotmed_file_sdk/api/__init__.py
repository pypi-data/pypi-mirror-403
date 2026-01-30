# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from biotmed_file_sdk.api.file_api_api import FileAPIApi
    from biotmed_file_sdk.api.health_check_api_api import HealthCheckAPIApi
    from biotmed_file_sdk.api.multiple_part_file_api_api import MultiplePartFileAPIApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from biotmed_file_sdk.api.file_api_api import FileAPIApi
from biotmed_file_sdk.api.health_check_api_api import HealthCheckAPIApi
from biotmed_file_sdk.api.multiple_part_file_api_api import MultiplePartFileAPIApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
