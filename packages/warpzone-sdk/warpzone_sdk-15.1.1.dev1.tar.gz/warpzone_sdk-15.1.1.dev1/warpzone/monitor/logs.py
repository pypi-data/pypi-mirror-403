# NOTE: OpenTelemetry logging to Azure is still in EXPERIMENTAL mode!
import logging
import os
import threading
from logging import StreamHandler

from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry import _logs as logs
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

logger = logging.getLogger(__name__)
logger.addHandler(StreamHandler())

# Suppress verbose logging from Azure SDK and infrastructure
_NOISY_LOGGERS = [
    "azure.core.pipeline.policies.http_logging_policy",
    "azure.data.tables",
    "azure.storage.blob",
    "azure.servicebus",
    "azure.identity",
    "azure.monitor.opentelemetry.exporter",
    "azure_functions_worker",
    "azure.functions",
    "uamqp",
]
for _logger_name in _NOISY_LOGGERS:
    logging.getLogger(_logger_name).setLevel(logging.WARNING)

_LOGGING_LOCK = threading.Lock()
LOGGING_IS_CONFIGURED = False


def configure_logging():
    global LOGGING_IS_CONFIGURED
    # Add thread locking to avoid race conditions during setup
    with _LOGGING_LOCK:
        if LOGGING_IS_CONFIGURED:
            # logging should only be set up once
            # to avoid duplicated log handling.
            # Global variables is the pattern used
            # by opentelemetry, so we use the same
            return

        # set up logger provider based on the Azure Function resource
        # (this is make sure App Insights can track the log source correctly)
        # (https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable?tabs=net#set-the-cloud-role-name-and-the-cloud-role-instance)
        service_name = os.getenv("WEBSITE_SITE_NAME") or "unknown-service"
        resource = Resource.create({SERVICE_NAME: service_name})
        logs.set_logger_provider(
            LoggerProvider(
                resource=resource,
            )
        )

        # setup azure monitor log exporter to send telemetry to App Insights
        try:
            log_exporter = AzureMonitorLogExporter()
        except ValueError:
            logger.warning(
                "Cant set up logging to App Insights,"
                " as no connection string is set."
            )
        else:
            log_record_processor = BatchLogRecordProcessor(log_exporter)
            logs.get_logger_provider().add_log_record_processor(log_record_processor)

        LOGGING_IS_CONFIGURED = True


def get_logger(name: str):
    # set up standard logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Check if OTEL handler is already added to this specific logger
    # (not using hasHandlers() as it also checks parent/root handlers)
    has_otel_handler = any(isinstance(h, LoggingHandler) for h in logger.handlers)
    if not has_otel_handler:
        # add OTEL handler for trace correlation
        handler = LoggingHandler()
        logger.addHandler(handler)
        # Don't propagate to root logger to avoid duplicate logs
        logger.propagate = False

    return logger
