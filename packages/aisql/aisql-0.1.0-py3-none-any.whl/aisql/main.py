import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .lib import SQLGenerator, MongoDBGenerator, QueryGenerationResult
from .models import QuestionRequest, PostgreSQLResponse, MongoDBResponse
from .schemas import POSTGRESQL_SCHEMA, MONGODB_SCHEMA

# Initialize FastAPI app
app = FastAPI(
    title="Query Generation API",
    description="API for converting natural language questions into SQL or MongoDB queries",
    version="1.0.0",
)

# Initialize templates from packaged data
templates_path = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# Lazy-initialized query generators
sql_generator: Optional[SQLGenerator] = None
mongodb_generator: Optional[MongoDBGenerator] = None


def _use_mock_mode() -> bool:
    return os.environ.get("AISQL_USE_MOCK", "").lower() in {"1", "true", "yes", "on"}


def _ensure_api_key():
    if _use_mock_mode():
        return
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Set it in the environment or "
            "export AISQL_USE_MOCK=true to run without external LLM calls."
        )


def _get_sql_generator() -> SQLGenerator:
    global sql_generator
    if sql_generator is None:
        _ensure_api_key()
        sql_generator = SQLGenerator(
            schema=POSTGRESQL_SCHEMA,
            use_mock=_use_mock_mode(),
        )
    return sql_generator


def _get_mongodb_generator() -> MongoDBGenerator:
    global mongodb_generator
    if mongodb_generator is None:
        _ensure_api_key()
        mongodb_generator = MongoDBGenerator(
            schema=MONGODB_SCHEMA,
            use_mock=_use_mock_mode(),
        )
    return mongodb_generator


@app.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    """Demo page for the query generator"""
    return templates.TemplateResponse("demo.html", {"request": request})


@app.get("/")
async def root():
    """Root endpoint returning API information"""
    return {
        "name": "Query Generation API",
        "version": "1.0.0",
        "description": "Convert natural language questions to SQL or MongoDB queries",
    }


@app.get("/schema/postgresql")
async def get_postgresql_schema():
    """Get the current PostgreSQL schema"""
    return {"schema": POSTGRESQL_SCHEMA}


@app.get("/schema/mongodb")
async def get_mongodb_schema():
    """Get the current MongoDB schema"""
    return {"schema": MONGODB_SCHEMA}


@app.post("/generate-postgresql", response_model=PostgreSQLResponse)
async def generate_postgresql(request: QuestionRequest) -> PostgreSQLResponse:
    """
    Generate a PostgreSQL query from a natural language question

    Args:
        request: QuestionRequest containing the natural language question

    Returns:
        PostgreSQLResponse containing the generated SQL query and metadata

    Raises:
        HTTPException: If generation fails or input is invalid
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        generator = _get_sql_generator()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        result: QueryGenerationResult = generator.generate(request.question)

        if result.error:
            raise HTTPException(status_code=400, detail=result.error)

        return PostgreSQLResponse(
            query=result.query,
            explanation=result.explanation,
            is_valid=result.is_valid,
            error=result.error,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate PostgreSQL query: {str(e)}"
        )


@app.post("/generate-mongodb", response_model=MongoDBResponse)
async def generate_mongodb(request: QuestionRequest) -> MongoDBResponse:
    """
    Generate a MongoDB query from a natural language question

    Args:
        request: QuestionRequest containing the natural language question

    Returns:
        MongoDBResponse containing the generated MongoDB query and metadata

    Raises:
        HTTPException: If generation fails or input is invalid
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        generator = _get_mongodb_generator()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        result: QueryGenerationResult = generator.generate(request.question)

        if result.error:
            raise HTTPException(status_code=400, detail=result.error)

        # Format the query string properly
        try:
            import json

            # First try to parse it as JSON
            if isinstance(result.query, str):
                # Handle the case where it might be a raw string with escaped chars
                clean_query = result.query.strip()
                try:
                    # Try to parse as is first
                    parsed_query = json.loads(clean_query)
                except json.JSONDecodeError:
                    # If that fails, try to evaluate it as a Python literal
                    import ast

                    parsed_query = ast.literal_eval(clean_query)

                # Convert back to a properly formatted JSON string
                formatted_query = json.dumps(parsed_query, indent=2)
            else:
                # If it's already a dict or other object, just format it
                formatted_query = json.dumps(result.query, indent=2)

        except (json.JSONDecodeError, SyntaxError, ValueError):
            # If all parsing fails, return the original query
            formatted_query = result.query

        return MongoDBResponse(
            query=formatted_query,
            explanation=result.explanation,
            is_valid=result.is_valid,
            error=result.error,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate MongoDB query: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
