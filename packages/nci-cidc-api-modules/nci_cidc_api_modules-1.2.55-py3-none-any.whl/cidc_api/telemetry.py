# standard modules
from functools import wraps

# external modules
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# local modules
from .config.settings import ENV, TESTING

# pylint: disable=import-outside-toplevel


def instrument_flask(app):
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.cloud_trace_propagator import CloudTraceFormatPropagator

    FlaskInstrumentor().instrument_app(app)

    # use the X-Cloud-Trace-Context header
    set_global_textmap(CloudTraceFormatPropagator())


def instrument_requests():
    from opentelemetry.instrumentation.requests import RequestsInstrumentor

    def _request_hook(span, request_obj):
        span.update_name(f"requests {request_obj.method}")

    RequestsInstrumentor().instrument(request_hook=_request_hook)


def instrument_sqlachemy(engine):
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(engine=engine)


resource = Resource(attributes={"service.name": f"CIDC-{ENV}"})
provider = TracerProvider(resource=resource)


# if ENV == "dev" and not TESTING:
#     from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

#     COLLECTOR_ENDPOINT = "127.0.0.1"
#     COLLECTOR_GRPC_PORT = 6004

#     # send spans to local exporter
#     # 1. download latest version from https://github.com/open-telemetry/opentelemetry-collector-releases/releases (otelcol-contrib_0.140.1_darwin_arm64)
#     # 2. start exporter from otel folder with `./otelcol-contrib --config=config.yaml`
#     # 3. download and start Jeager (all-in-one image)  - https://www.jaegertracing.io/download/
#     exporter = OTLPSpanExporter(endpoint=f"http://{COLLECTOR_ENDPOINT}:{COLLECTOR_GRPC_PORT}", insecure=True)
#     processor = BatchSpanProcessor(exporter)
#     provider.add_span_processor(processor)

if ENV == "dev-int":
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

    # send span to Cloud Trace service - https://console.cloud.google.com/traces/explorer
    exporter = CloudTraceSpanExporter()
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)


# NOTE: we don't run telemetry in upper tiers; no span processor is noop

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)


def trace_(*args):
    def decorator_factory(func):

        @wraps(func)
        def wrapper(*args_, **kwargs_):
            func_name = f"{func.__module__.split(".")[-1]}.{func.__name__}"

            with tracer.start_as_current_span(func_name) as span:
                for arg in args:
                    value = kwargs_.get(arg)

                    # track id of argument if exists
                    if hasattr(value, "id"):
                        value = getattr(value, "id")

                    span.set_attributes({arg: value})

                result = func(*args_, **kwargs_)

                if isinstance(result, (str, int, float, bool)):
                    span.set_attribute("result", result)

            return result

        return wrapper

    return decorator_factory
