from typing import Optional

from opentelemetry import trace
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from logweave.config import settings

# Ensure logging instrumentation happens only once
_logging_instrumented = False


def reset_telemetry():
    """
    Reset telemetry instrumentation state.

    CRITICAL for testing: Allows re-initialization of OpenTelemetry components.
    Must be called in test fixtures to prevent state leakage between tests.
    """
    global _logging_instrumented
    _logging_instrumented = False


def setup_telemetry(app: Optional[object] = None):
    """
    OpenTelemetry setup.

    - Trace/span IDs ALWAYS enabled
    - Exporting is OPTIONAL (like Sentry)
    - Safe to call even if exporters are missing
    - Safe to call without FastAPI
    """

    global _logging_instrumented

    # ---- Tracer provider ----
    resource = Resource.create(
        {
            "service.name": settings.SERVICE_NAME,
        }
    )

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # ---- Optional span exporter ----
    if settings.ENABLE_TRACING_EXPORT and settings.OTEL_EXPORTER_ENDPOINT:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT)))
        except Exception as e:
            # Fail SAFE: tracing export must never break app
            print(f"[LogWeave] Tracing export disabled due to error: {e}")

    # ---- Inject trace/span IDs into logging (ONCE) ----
    if not _logging_instrumented:
        LoggingInstrumentor().instrument(set_logging_format=False)
        _logging_instrumented = True

    # ---- Instrument FastAPI (optional) ----
    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
        except ImportError:
            pass
