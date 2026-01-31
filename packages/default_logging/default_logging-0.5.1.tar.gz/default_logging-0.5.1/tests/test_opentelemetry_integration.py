import os
import subprocess
import sys
import tempfile

CONFIG_YAML = """
version: 1
formatters:
  simple_with_trace_context:
    class: default_logging.millisecond_formatter.UtcTimezoneFormatter
    format: 'TRACE_ID=%(otelTraceID)s - %(message)s'
    datefmt: '%Y-%m-%dT%H:%M:%S.%f%z'
handlers:
  console:
    class: logging.StreamHandler
    formatter: simple_with_trace_context
    stream: ext://sys.stdout
root:
  level: INFO
  handlers: [console]
"""

SCRIPT_CODE = """
import logging
from default_logging import configure_logging
from opentelemetry import trace
import sys

# Configure with the temp yaml file passed as arg
configure_logging(config_path=sys.argv[1])

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("test-span"):
    logger.info("Test message")
"""

def test_auto_instrumentation_logging():
    """
    Verifies that running a script with opentelemetry-instrument and
    appropriate environment variables correctly injects trace IDs into logs.
    """

    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_config:
        tmp_config.write(CONFIG_YAML)
        tmp_config_path = tmp_config.name

    # Create a temporary python script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_script:
        tmp_script.write(SCRIPT_CODE)
        tmp_script_path = tmp_script.name

    try:
        # Run with opentelemetry-instrument
        env = os.environ.copy()
        # Disable metrics to reduce noise
        env['OTEL_METRICS_EXPORTER'] = 'none'
        # Disable logs exporter to prevent initialization crashes if OTLP is missing
        env['OTEL_LOGS_EXPORTER'] = 'none'
        env['OTEL_TRACES_EXPORTER'] = 'console'
        # Ensure PYTHONPATH includes current dir so default_logging is importable
        env['PYTHONPATH'] = os.getcwd() + os.pathsep + env.get('PYTHONPATH', '')

        cmd = [
            "opentelemetry-instrument",
            sys.executable,
            tmp_script_path,
            tmp_config_path
        ]

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )

        # Check for success
        assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"

        # Check output for TRACE_ID
        # The trace ID should be a 32-char hex string, not 0 or None if instrumentation worked
        # trace_id=0 means it didn't inject a real ID (or span wasn't created properly),
        # but KeyErr means field missing entirely.

        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")

        # Check if output contains "TRACE_ID=" followed by non-zero hex
        import re
        match = re.search(r"TRACE_ID=([a-f0-9]+) - Test message", result.stdout)

        assert match, "Log output did not contain expected format with TRACE_ID"
        trace_id = match.group(1)
        assert trace_id != "0", "Trace ID was 0, meaning context wasn't captured or span failed"
        assert len(trace_id) == 32, f"Trace ID length incorrect: {trace_id}"

    finally:
        if os.path.exists(tmp_config_path):
            os.remove(tmp_config_path)
        if os.path.exists(tmp_script_path):
            os.remove(tmp_script_path)
