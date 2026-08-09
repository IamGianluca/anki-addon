"""Entry point for: uv run python -m tests.evals.viewer"""

import uvicorn
from tests.evals.viewer import app

uvicorn.run(app, host="127.0.0.1", port=5000)
