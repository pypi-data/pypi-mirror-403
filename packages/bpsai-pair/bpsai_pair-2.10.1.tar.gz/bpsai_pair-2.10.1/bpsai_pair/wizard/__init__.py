"""PairCoder Setup Wizard.

A web-based setup wizard for configuring PairCoder.
Uses FastAPI with Jinja2 templates for the UI.

Usage:
    from bpsai_pair.wizard.app import create_app, DEFAULT_PORT

    # Create the app
    app = create_app()

    # Run with uvicorn
    import uvicorn
    uvicorn.run(app, host="localhost", port=DEFAULT_PORT)
"""

from bpsai_pair.wizard.app import DEFAULT_PORT, create_app, open_browser

__all__ = [
    "create_app",
    "DEFAULT_PORT",
    "open_browser",
]
