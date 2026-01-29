from opentelemetry import trace


def get_trace_context() -> tuple[str, str]:
    """
    Get trace_id and span_id from OpenTelemetry context.

    Always returns valid strings.
    Never raises.
    """

    try:
        span = trace.get_current_span()
        ctx = span.get_span_context()

        if ctx and ctx.is_valid:
            trace_id = format(ctx.trace_id, "032x")
            span_id = format(ctx.span_id, "016x")
            return trace_id, span_id
    except Exception:
        pass

    # Fallback (safe, never breaks logging)
    return "-", "-"
