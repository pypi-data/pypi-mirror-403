from wtwco_igloo.extensions.utils.authentication.authentication_base import _AuthenticationManagerBase
from wtwco_igloo.extensions.utils.retry_settings import RetrySettings


class _AuthenticationManagerWithoutRefresh(_AuthenticationManagerBase):
    def __init__(
        self,
        api_url: str,
        client_id: str,
        tenant_id: str,
        enable_broker_on_windows: bool,
        retry_settings: RetrySettings,
    ):
        super().__init__(
            api_url,
            client_id,
            tenant_id,
            enable_broker_on_windows,
            retry_settings,
        )
