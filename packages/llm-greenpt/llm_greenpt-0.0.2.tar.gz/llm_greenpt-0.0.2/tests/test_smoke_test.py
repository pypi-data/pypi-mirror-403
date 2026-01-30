"""Smoke tests for llm-greenpt plugin."""

import subprocess
import sys
import pytest
import os
import tempfile
import json


def _get_api_key():
    """Get the API key from environment or file."""
    api_key = os.environ.get("GREENPT_API_KEY")
    if api_key:
        return api_key

    # Fallback to file if it exists
    key_file = "greenpt.api.key.txt"
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            return f.read().strip()

    return None


def _run_llm_command(cmd_args, timeout=30, use_api_key=True, database_file=None):
    """Helper to run LLM commands with proper environment setup."""
    env = os.environ.copy()
    if use_api_key:
        api_key = _get_api_key()
        if api_key:
            env["GREENPT_API_KEY"] = api_key

    cmd = [sys.executable, "-m", "llm", "prompt"] + cmd_args

    # Add database file option if specified
    if database_file:
        cmd.extend(["-d", database_file])

    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)


@pytest.mark.smoke_test
def test_llm_greenpt_basic_connectivity():
    """Basic API connectivity smoke test."""
    api_key = _get_api_key()
    if not api_key:
        pytest.skip("GREENPT_API_KEY not set - skipping live API test")

    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_file = tmp_db.name

        try:
            result = _run_llm_command(
                [
                    "Say hello world in one word",
                    "-m",
                    "greenpt-large",
                    "--no-stream",
                ],
                database_file=db_file,
            )

            # Check that the command executed successfully
            assert result.returncode == 0, (
                f"LLM command failed with return code {result.returncode}: {result.stderr}"
            )

            # Check that we got a response
            assert len(result.stdout.strip()) > 0, "No response received"

        finally:
            # Clean up the temporary database file
            if os.path.exists(db_file):
                os.unlink(db_file)

    except subprocess.TimeoutExpired:
        pytest.fail("LLM command timed out - GreenPT API may be unreachable")
    except Exception as e:
        pytest.fail(f"Unexpected error during basic connectivity test: {e}")


@pytest.mark.smoke_test
def test_llm_greenpt_streaming_functionality():
    """Streaming API functionality smoke test."""
    api_key = _get_api_key()
    if not api_key:
        pytest.skip("GREENPT_API_KEY not set - skipping live API test")

    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_file = tmp_db.name

        try:
            result = _run_llm_command(
                ["Say hello", "-m", "greenpt-large"],
                timeout=30,
                database_file=db_file,
            )

            # Check that the command executed successfully
            assert result.returncode == 0, (
                f"LLM streaming command failed with return code {result.returncode}: {result.stderr}"
            )

            # Check that we got a response
            response_text = result.stdout.strip()
            assert len(response_text) > 0, "No response received from streaming API"

            # Verify the response contains expected content
            assert "hello" in response_text.lower() or "Hello" in response_text, (
                "Response doesn't seem to contain expected content"
            )

        finally:
            # Clean up the temporary database file
            if os.path.exists(db_file):
                os.unlink(db_file)

    except subprocess.TimeoutExpired:
        pytest.fail("LLM streaming command timed out - GreenPT API may be unreachable")
    except Exception as e:
        pytest.fail(f"Unexpected error during streaming test: {e}")


@pytest.mark.smoke_test
def test_llm_greenpt_streaming_vs_non_streaming():
    """Compare streaming vs non-streaming responses."""
    api_key = _get_api_key()
    if not api_key:
        pytest.skip("GREENPT_API_KEY not set - skipping live API test")

    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_file = tmp_db.name

        try:
            # Test with streaming (default)
            streaming_result = _run_llm_command(
                ["What is the capital of France?", "-m", "greenpt-large"],
                database_file=db_file,
            )

            # Check that the streaming command executed successfully
            assert streaming_result.returncode == 0, (
                f"Streaming command failed with return code {streaming_result.returncode}: {streaming_result.stderr}"
            )

            # Test with explicit non-streaming
            non_streaming_result = _run_llm_command(
                [
                    "What is the capital of France?",
                    "-m",
                    "greenpt-large",
                    "--no-stream",
                ],
                database_file=db_file,
            )

            # Check that the non-streaming command executed successfully
            assert non_streaming_result.returncode == 0, (
                f"Non-streaming command failed with return code {non_streaming_result.returncode}: {non_streaming_result.stderr}"
            )

            # Both should return responses
            streaming_response = streaming_result.stdout.strip()
            non_streaming_response = non_streaming_result.stdout.strip()

            assert len(streaming_response) > 0, "No response from streaming API"
            assert len(non_streaming_response) > 0, "No response from non-streaming API"

            # Both responses should contain the expected answer
            assert (
                "Paris" in streaming_response or "paris" in streaming_response.lower()
            ), "Streaming response doesn't mention Paris"
            assert (
                "Paris" in non_streaming_response
                or "paris" in non_streaming_response.lower()
            ), "Non-streaming response doesn't mention Paris"

        finally:
            # Clean up the temporary database file
            if os.path.exists(db_file):
                os.unlink(db_file)

    except subprocess.TimeoutExpired:
        pytest.fail("LLM command timed out - GreenPT API may be unreachable")
    except Exception as e:
        pytest.fail(f"Unexpected error during streaming comparison test: {e}")


@pytest.mark.smoke_test
def test_llm_greenpt_model_availability():
    """Verify that GreenPT models are available."""
    try:
        # List available models
        cmd = [sys.executable, "-m", "llm", "models", "list"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Check that the command executed successfully
        assert result.returncode == 0, (
            f"LLM models command failed with return code {result.returncode}: {result.stderr}"
        )

        # Check that GreenPT models are available
        output = result.stdout
        assert "greenpt/green-l" in output, "Expected model greenpt/green-l not found"
        assert "greenpt/green-r" in output, "Expected model greenpt/green-r not found"
        assert "greenpt/llama-3.3-70b-instruct" in output, (
            "Expected model greenpt/llama-3.3-70b-instruct not found"
        )

    except subprocess.TimeoutExpired:
        pytest.fail("LLM models command timed out")
    except Exception as e:
        pytest.fail(f"Unexpected error during models verification: {e}")


@pytest.mark.smoke_test
def test_llm_greenpt_impact_logging():
    """Test that impact data is properly logged and can be queried."""
    api_key = _get_api_key()
    if not api_key:
        pytest.skip("GREENPT_API_KEY not set - skipping live API test")

    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_file = tmp_db.name

        try:
            # Run a command to generate impact logs
            result = _run_llm_command(
                ["What is 2+2?", "-m", "greenpt-large", "--no-stream"],
                database_file=db_file,
            )

            # Check that the command executed successfully
            assert result.returncode == 0, (
                f"LLM command failed with return code {result.returncode}: {result.stderr}"
            )

            # Query the logs using the commands from the README
            log_cmd = [
                sys.executable,
                "-m",
                "llm",
                "logs",
                "--model",
                "greenpt-large",
                "--json",
                "-d",
                db_file,
            ]

            log_result = subprocess.run(
                log_cmd, capture_output=True, text=True, timeout=10
            )

            assert log_result.returncode == 0, (
                f"LLM logs command failed with return code {log_result.returncode}: {log_result.stderr}"
            )

            # Parse the log output
            logs_data = json.loads(log_result.stdout)

            # Verify we have logs with impact data
            assert len(logs_data) > 0, "No logs found"

            # Check that impact data is present in the logs
            impact_present = False
            for log_entry in logs_data:
                if (
                    "response_json" in log_entry
                    and "impact" in log_entry["response_json"]
                ):
                    impact_data = log_entry["response_json"]["impact"]
                    assert "version" in impact_data, "Missing version in impact data"
                    assert "inferenceTime" in impact_data, (
                        "Missing inferenceTime in impact data"
                    )
                    assert "energy" in impact_data, "Missing energy in impact data"
                    assert "emissions" in impact_data, (
                        "Missing emissions in impact data"
                    )
                    assert impact_data["energy"]["total"] >= 0, (
                        "Energy should be non-negative"
                    )
                    impact_present = True
                    break

            assert impact_present, "No impact data found in logs"

            # Test the jq commands from the README
            # First jq command: View recent logs with impact data
            jq_cmd1 = ["jq", ".[-1:].[].response_json.impact"]
            jq_process1 = subprocess.Popen(
                jq_cmd1,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            jq_output1, jq_error1 = jq_process1.communicate(input=log_result.stdout)

            # Note: We won't assert on jq success since it might not be installed
            # but we'll validate the data is there in our own parsing above

        finally:
            # Clean up the temporary database file
            if os.path.exists(db_file):
                os.unlink(db_file)

    except subprocess.TimeoutExpired:
        pytest.fail("Command timed out")
    except FileNotFoundError:
        pytest.skip("jq not found - skipping jq command tests")
    except Exception as e:
        pytest.fail(f"Unexpected error during impact logging test: {e}")
