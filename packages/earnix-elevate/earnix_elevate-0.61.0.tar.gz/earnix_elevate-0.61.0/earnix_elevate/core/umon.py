from ..clients.umon import (
    ApiClient,
    Configuration,
    QuotaServiceApi,
    UsageMonitoringServiceApi,
)
from .common import BaseElevateClient, BaseElevateService


class UmonClient(BaseElevateClient, ApiClient):
    _route = "/api/umon"
    _conf_class = Configuration


class UsageMonitoringService(BaseElevateService, UsageMonitoringServiceApi):
    _client_class = UmonClient


class QuotaService(BaseElevateService, QuotaServiceApi):
    _client_class = UmonClient
