from typing import Optional
from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(
        ...,
        description="Natural language question about the data",
        example="Show me all customers who ordered in the last 30 days",
    )


class PostgreSQLResponse(BaseModel):
    query: str = Field(
        ...,
        description="Generated PostgreSQL query",
        example="SELECT DISTINCT c.* FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days'",
    )
    explanation: str = Field(
        ...,
        description="Plain English explanation of what the SQL query does",
        example="This query retrieves all customers who have placed orders within the last 30 days.",
    )
    is_valid: bool = Field(
        ...,
        description="Whether the generated SQL query is valid and matches the question",
    )
    error: Optional[str] = Field(
        None, description="Error message if something went wrong during generation"
    )


class MongoDBResponse(BaseModel):
    query: str = Field(
        ...,
        description="Generated MongoDB query as a string",
        example="""
        {
            "$lookup": {
                "from": "orders",
                "localField": "_id",
                "foreignField": "customer_id",
                "as": "orders"
            },
            "$match": {
                "orders.order_date": {
                    "$gte": {
                        "$dateSubtract": {
                            "startDate": "$$NOW",
                            "unit": "day",
                            "amount": 30
                        }
                    }
                }
            }
        }
        """,
    )
    explanation: str = Field(
        ...,
        description="Plain English explanation of what the MongoDB query does",
        example="This query joins customers with their orders and filters for those who ordered in the last 30 days.",
    )
    is_valid: bool = Field(
        ...,
        description="Whether the generated MongoDB query is valid and matches the question",
    )
    error: Optional[str] = Field(
        None, description="Error message if something went wrong during generation"
    )
