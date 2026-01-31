import inspect
import logging
import os
import threading
from contextlib import contextmanager
from functools import wraps
from logging import StreamHandler
from typing import Callable

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry import context, trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import Tracer, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)
logger.addHandler(StreamHandler())


class WarpzoneTracer:
    """Wrapper around OpenTelemetry tracer with additional trace decorator method"""

    def __init__(self, otel_tracer: Tracer):
        # Store the original tracer instead of calling super().__init__
        # because we want to wrap an existing tracer, not create a new one
        self._tracer = otel_tracer

    def __getattr__(self, name):
        """Delegate all attributes to the underlying tracer"""
        return getattr(self._tracer, name)

    def trace_function(
        self,
        name: str = None,
        set_args_as_attributes: bool = False,
        on_input: Callable = None,
        on_output: Callable = None,
    ):
        """
        Decorator to trace a function using this tracer object.

        This decorator wraps functions with OpenTelemetry tracing, allowing for:
        - Automatically create spans for function execution
        - Customize the span name
        - Add custom attributes to the span
        - Add custom logic for inputs and outputs

        Args:
            name: Optional name for the span. If not provided, uses the function name.
            set_args_as_attributes: If True, sets function arguments as attributes.
            on_input: Optional callback called with (span, *args, **kwargs) before.
            on_output: Optional callback called with (span, result) after.

        Example:
            # Simple tracing with function name
            tracer = get_tracer(__name__)

            @tracer.trace_function()
            def my_function():
                pass

            # Custom tracing with input/output callbacks
            @tracer.trace_function(
                on_input=lambda span, new_data, existing_data, now: (
                    span.set_attribute("new_records", len(new_data)),
                    span.set_attribute("existing_records", len(existing_data)),
                ),
                on_output=lambda span, result: (
                    span.set_attribute("merged_records", len(result))
                ),
            )
            def merge_new_and_existing(new_data, existing_data, now):
                pass
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                span_name = name or func.__name__
                with self._tracer.start_as_current_span(span_name) as span:
                    if set_args_as_attributes:
                        # Get parameter names from function signature
                        sig = inspect.signature(func)
                        param_names = list(sig.parameters.keys())

                        # Set positional arguments with their parameter names
                        for i, arg in enumerate(args):
                            if i < len(param_names):
                                span.set_attribute(param_names[i], str(arg))
                            else:
                                # Fallback for *args if there are more args than params
                                span.set_attribute(f"arg_{i}", str(arg))

                        # Set keyword arguments
                        for key, value in kwargs.items():
                            span.set_attribute(str(key), str(value))

                    # Call on_input callback if provided
                    if on_input:
                        on_input(span, *args, **kwargs)

                    result = func(*args, **kwargs)

                    # Call on_output callback if provided
                    if on_output:
                        on_output(span, result)

                    return result

            return wrapper

        return decorator


tracer = WarpzoneTracer(trace.get_tracer(__name__))


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
    otel_tracer = trace.get_tracer(name)
    return WarpzoneTracer(otel_tracer)


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
def servicebus_send_span(subject: str):
    """Start span for Service Bus message tracing.

    Args:
        subject: The message subject (used as span name for easy identification)

    Yields:
        Span: the span
    """
    with tracer.start_as_current_span(
        subject, kind=trace.SpanKind.PRODUCER
    ) as msg_span:
        msg_span.set_attributes({"az.namespace": _SB_TRACE_NAMESPACE})

        yield msg_span
