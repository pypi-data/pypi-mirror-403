# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from biotmed_device_sdk.api.command_api_api import CommandAPIApi
    from biotmed_device_sdk.api.device_api_api import DeviceAPIApi
    from biotmed_device_sdk.api.device_alert_api_api import DeviceAlertAPIApi
    from biotmed_device_sdk.api.device_certificate_api_api import DeviceCertificateAPIApi
    from biotmed_device_sdk.api.endpoint_api_api import EndpointAPIApi
    from biotmed_device_sdk.api.health_check_api_api import HealthCheckAPIApi
    from biotmed_device_sdk.api.temporary_credentials_api_api import TemporaryCredentialsAPIApi
    from biotmed_device_sdk.api.temporary_token_operation_api_api import TemporaryTokenOperationAPIApi
    from biotmed_device_sdk.api.usage_session_api_api import UsageSessionAPIApi
    from biotmed_device_sdk.api.usage_session_remote_control_api_api import UsageSessionRemoteControlAPIApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from biotmed_device_sdk.api.command_api_api import CommandAPIApi
from biotmed_device_sdk.api.device_api_api import DeviceAPIApi
from biotmed_device_sdk.api.device_alert_api_api import DeviceAlertAPIApi
from biotmed_device_sdk.api.device_certificate_api_api import DeviceCertificateAPIApi
from biotmed_device_sdk.api.endpoint_api_api import EndpointAPIApi
from biotmed_device_sdk.api.health_check_api_api import HealthCheckAPIApi
from biotmed_device_sdk.api.temporary_credentials_api_api import TemporaryCredentialsAPIApi
from biotmed_device_sdk.api.temporary_token_operation_api_api import TemporaryTokenOperationAPIApi
from biotmed_device_sdk.api.usage_session_api_api import UsageSessionAPIApi
from biotmed_device_sdk.api.usage_session_remote_control_api_api import UsageSessionRemoteControlAPIApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
