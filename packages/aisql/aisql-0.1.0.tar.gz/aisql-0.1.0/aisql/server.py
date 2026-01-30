"""Console entry point for running the AISQL FastAPI server."""

import os
import uvicorn


def main() -> None:
    """Start the FastAPI server with configurable host/port."""
    host = os.environ.get("AISQL_HOST", "0.0.0.0")
    port = int(os.environ.get("AISQL_PORT", "8000"))
    uvicorn.run("aisql.main:app", host=host, port=port)


if __name__ == "__main__":
    main()
