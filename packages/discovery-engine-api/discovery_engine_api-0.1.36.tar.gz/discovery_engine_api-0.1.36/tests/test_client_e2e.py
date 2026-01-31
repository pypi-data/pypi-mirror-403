"""
End-to-end tests for the Discovery Engine Python SDK.

These tests call the real API and exercise the full flow including Modal.
They are skipped if API credentials are not available.

To run these tests locally:
    # Set required environment variables
    export DISCOVERY_API_KEY="your-api-key"

    # Optional: Set environment (defaults to staging)
    export ENVIRONMENT="staging"  # or "production"

    # Run e2e tests
    pytest engine/packages/client/tests/test_client_e2e.py -v

    # Or run all tests except e2e
    pytest -m "not e2e"

To run in CI (GitHub Actions):
    Set these secrets in GitHub:
    - DISCOVERY_API_KEY: Your API key
    - ENVIRONMENT: "staging" or "production" (optional, defaults to staging)

    The tests will:
    - Auto-detect environment from ENVIRONMENT or VERCEL_ENV
    - Use staging URL (https://staging.disco.leap-labs.com) by default
    - Use production URL (https://disco.leap-labs.com) if ENVIRONMENT=production
    - Skip gracefully if DISCOVERY_API_KEY is not set
"""

import io
import os

import pandas as pd
import pytest

# Test data - simple regression dataset
TEST_DATA_CSV = """age,income,experience,price
25,50000,2,150000
30,60000,5,180000
35,70000,8,220000
40,80000,12,250000
45,90000,15,280000
28,55000,3,160000
32,65000,6,190000
38,75000,10,230000
42,85000,13,260000
48,95000,18,300000
"""


# Hardcoded API URLs (these don't change)
STAGING_API_URL = "https://staging.disco.leap-labs.com"
PRODUCTION_API_URL = "https://disco.leap-labs.com"


def get_api_key() -> str | None:
    """Get API key from environment variable."""
    return os.getenv("DISCOVERY_API_KEY")


def get_environment() -> str:
    """
    Determine the current environment (staging or production).

    Checks environment variables in order:
    1. ENVIRONMENT (set in CI/GitHub Actions)
    2. VERCEL_ENV (set in Vercel deployments)
    3. Defaults to staging
    """
    env = os.getenv("ENVIRONMENT") or os.getenv("VERCEL_ENV")
    if env == "production":
        return "production"
    return "staging"


def get_api_url() -> str:
    """
    Get API URL based on environment.

    Returns:
        - Production URL if environment is production
        - Staging URL otherwise (default)
    """
    env = get_environment()
    if env == "production":
        return PRODUCTION_API_URL
    return STAGING_API_URL


@pytest.fixture
def api_key():
    """Get API key from environment, skip test if not available."""
    key = get_api_key()
    if not key:
        pytest.skip("DISCOVERY_API_KEY environment variable not set")
    return key


@pytest.fixture
def api_url():
    """Get API URL from environment (optional)."""
    return get_api_url()


@pytest.fixture
def test_dataframe():
    """Create test DataFrame from CSV string."""
    try:
        return pd.read_csv(io.StringIO(TEST_DATA_CSV))
    except ImportError:
        pytest.skip("pandas not available")


@pytest.fixture
def engine(api_key, api_url):
    """Create Engine instance with API key and optional URL."""
    from discovery import Engine

    engine = Engine(api_key=api_key)
    if api_url:
        engine.base_url = api_url.rstrip("/")
    return engine


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_client_e2e_full_flow(engine, test_dataframe):
    """
    Test the full end-to-end flow: upload, analyze, wait for completion.

    This test:
    1. Uploads a test dataset via the API
    2. Creates a run
    3. Waits for Modal to process the job
    4. Verifies results are returned

    This exercises the complete production flow including Modal.
    """
    # Run analysis with wait=True to exercise full flow including Modal
    result = await engine.run_async(
        file=test_dataframe,
        target_column="price",
        depth_iterations=1,
        description="E2E test dataset - house price prediction",
        column_descriptions={
            "age": "Age of the property owner",
            "income": "Annual income in USD",
            "experience": "Years of work experience",
            "price": "House price in USD",
        },
        auto_report_use_llm_evals=False,  # Disable LLMs for faster test
        wait=True,  # Wait for completion (exercises Modal)
        wait_timeout=600,  # 10 minute timeout
    )

    # Verify results
    assert result is not None, "Result should not be None"
    assert result.run_id is not None, "Run ID should be set"
    assert result.status == "completed", f"Run should be completed, got status: {result.status}"

    # Verify we got patterns (at least one pattern should be found)
    assert result.patterns is not None, "Patterns should not be None"
    assert len(result.patterns) > 0, f"Should find at least one pattern, got {len(result.patterns)}"

    # Verify summary exists
    assert result.summary is not None, "Summary should not be None"

    # Verify feature importance exists (if available)
    # Note: Feature importance might be None in some cases, so we don't assert it exists


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_client_e2e_async_workflow(engine, test_dataframe):
    """
    Test async workflow: start analysis, then wait for completion separately.

    This tests the async pattern where you start a run and check status later.
    """
    # Start analysis without waiting
    result = await engine.run_async(
        file=test_dataframe,
        target_column="price",
        depth_iterations=1,
        auto_report_use_llm_evals=False,
        wait=False,  # Don't wait immediately
    )

    assert result is not None, "Result should not be None"
    assert result.run_id is not None, "Run ID should be set"
    run_id = result.run_id

    # Now wait for completion separately
    completed_result = await engine.wait_for_completion(
        run_id=run_id,
        poll_interval=5.0,  # Check every 5 seconds
        timeout=600,  # 10 minute timeout
    )

    # Verify completion
    assert (
        completed_result.status == "completed"
    ), f"Run should be completed, got: {completed_result.status}"
    assert completed_result.patterns is not None, "Patterns should not be None"
    assert len(completed_result.patterns) > 0, "Should find at least one pattern"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_client_e2e_get_results(engine, test_dataframe):
    """
    Test getting results for an existing run.

    This tests the get_results method which can be used to check status
    of a run that was started elsewhere.
    """
    # Start a run
    result = await engine.run_async(
        file=test_dataframe,
        target_column="price",
        depth_iterations=1,
        auto_report_use_llm_evals=False,
        wait=False,
    )

    run_id = result.run_id

    # Get results immediately (might still be processing)
    initial_result = await engine.get_results(run_id)
    assert initial_result is not None, "Should get initial result"
    assert initial_result.run_id == run_id, "Run ID should match"

    # Wait for completion
    final_result = await engine.wait_for_completion(run_id, timeout=600)

    # Verify final results
    assert final_result.status == "completed", "Run should complete"
    assert final_result.patterns is not None, "Patterns should be available"
    assert len(final_result.patterns) > 0, "Should find patterns"
