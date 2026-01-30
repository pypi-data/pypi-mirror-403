# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from biotmed_dms_sdk.api.analytics_dbapi_api import AnalyticsDBAPIApi
    from biotmed_dms_sdk.api.analytics_db_connection_api_api import AnalyticsDBConnectionAPIApi
    from biotmed_dms_sdk.api.analytics_db_state_api_api import AnalyticsDBStateAPIApi
    from biotmed_dms_sdk.api.bi_dashboard_api_api import BIDashboardAPIApi
    from biotmed_dms_sdk.api.health_check_api_api import HealthCheckAPIApi
    from biotmed_dms_sdk.api.report_api_api import ReportAPIApi
    from biotmed_dms_sdk.api.temporary_token_operation_api_api import TemporaryTokenOperationAPIApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from biotmed_dms_sdk.api.analytics_dbapi_api import AnalyticsDBAPIApi
from biotmed_dms_sdk.api.analytics_db_connection_api_api import AnalyticsDBConnectionAPIApi
from biotmed_dms_sdk.api.analytics_db_state_api_api import AnalyticsDBStateAPIApi
from biotmed_dms_sdk.api.bi_dashboard_api_api import BIDashboardAPIApi
from biotmed_dms_sdk.api.health_check_api_api import HealthCheckAPIApi
from biotmed_dms_sdk.api.report_api_api import ReportAPIApi
from biotmed_dms_sdk.api.temporary_token_operation_api_api import TemporaryTokenOperationAPIApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
