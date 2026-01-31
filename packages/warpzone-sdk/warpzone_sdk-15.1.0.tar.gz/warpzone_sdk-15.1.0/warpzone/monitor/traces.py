import logging
import os
import threading
from contextlib import contextmanager
from logging import StreamHandler

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry import context, trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)
logger.addHandler(StreamHandler())

tracer = trace.get_tracer(__name__)

_TRACING_LOCK = threading.Lock()
TRACING_IS_CONFIGURED = False


def configure_tracing():
    global TRACING_IS_CONFIGURED
    # Add thread locking to avoid race conditions during setup
    with _TRACING_LOCK:
        if TRACING_IS_CONFIGURED:
            # tracing should only be set up once
            # to avoid duplicated trace handling.
            # Global variables is the pattern used
            # by opentelemetry, so we use the same
            return

        # set up tracer provider based on the Azure Function resource
        # (this is make sure App Insights can track the trace source correctly)
        # (https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable?tabs=net#set-the-cloud-role-name-and-the-cloud-role-instance).
        # We use the ALWAYS ON sampler since otherwise spans will not be
        # recording upon creation
        # (https://anecdotes.dev/opentelemetry-on-google-cloud-unraveling-the-mystery-f61f044c18be)
        service_name = os.getenv("WEBSITE_SITE_NAME") or "unknown-service"
        resource = Resource.create({SERVICE_NAME: service_name})
        trace.set_tracer_provider(
            TracerProvider(
                sampler=ALWAYS_ON,
                resource=resource,
            )
        )

        # setup azure monitor trace exporter to send telemetry to App Insights
        try:
            trace_exporter = AzureMonitorTraceExporter()
        except ValueError:
            logger.warning(
                "Cant set up tracing to App Insights,"
                " as no connection string is set."
            )
        else:
            span_processor = BatchSpanProcessor(trace_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

        TRACING_IS_CONFIGURED = True


@contextmanager
def set_trace_context(trace_parent: str, trace_state: str = ""):
    """Context manager for setting the trace context

    Args:
        trace_parent (str): Trace parent ID
        trace_state (str, optional): Trace state. Defaults to "".
    """
    carrier = {"traceparent": trace_parent, "tracestate": trace_state}
    ctx = TraceContextTextMapPropagator().extract(carrier=carrier)

    token = context.attach(ctx)  # attach context before run
    try:
        yield
    finally:
        context.detach(token)  # detach context after run


def get_tracer(name: str):
    tracer = trace.get_tracer(name)
    return tracer


def get_current_diagnostic_id() -> str:
    """Gets diagnostic id from current span

    The diagnostic id is a concatenation of operation-id and parent-id

    Returns:
        str: diagnostic id
    """
    span = trace.get_current_span()

    if not span.is_recording():
        return ""

    operation_id = "{:016x}".format(span.context.trace_id)
    parent_id = "{:016x}".format(span.context.span_id)

    diagnostic_id = f"00-{operation_id}-{parent_id}-01"

    return diagnostic_id


# Service Bus trace constants (these were removed from azure-servicebus SDK)
_SB_TRACE_NAMESPACE = "Microsoft.ServiceBus"


@contextmanager
def servicebus_send_span(subject: str) -> trace.Span:
    """Start span for Service Bus message tracing.

    Args:
        subject: The message subject (used as span name for easy identification)

    Yields:
        trace.Span: the span
    """
    with tracer.start_as_current_span(
        subject, kind=trace.SpanKind.PRODUCER
    ) as msg_span:
        msg_span.set_attributes({"az.namespace": _SB_TRACE_NAMESPACE})

        yield msg_span
