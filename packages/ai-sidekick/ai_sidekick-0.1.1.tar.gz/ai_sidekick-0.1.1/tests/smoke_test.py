"""Smoke test to verify the package can be imported and basic functionality works."""

from ai_sidekick import main


def test_main_runs() -> None:
    """Test that the main function runs without error."""
    # Just verify it doesn't raise an exception
    main()
