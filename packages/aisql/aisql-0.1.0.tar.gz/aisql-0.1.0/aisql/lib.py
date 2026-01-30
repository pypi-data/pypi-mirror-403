import re
from typing import Optional, Literal
from dataclasses import dataclass
from abc import ABC, abstractmethod

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

QueryType = Literal["sql", "mongodb"]


@dataclass
class QueryGenerationResult:
    """Data class to hold query generation results"""

    query: str
    explanation: str
    is_valid: bool
    query_type: QueryType
    error: Optional[str] = None


class QueryGenerator(ABC):
    """Abstract base class for query generators"""

    def __init__(
        self,
        schema: str,
        use_mock: bool = False,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0,
        chunk_size: int = 500,
        chunk_overlap: int = 0,
    ):
        self.schema = schema
        self.use_mock = use_mock
        self.embedding = None
        self.llm = None
        self.db = None
        self._num_docs = 1

        if self.use_mock:
            # Tests can instantiate generators without calling external APIs.
            return

        self.embedding = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)

        # Initialize vector store with schema
        documents = [Document(page_content=schema)]
        splitter = CharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        docs = splitter.split_documents(documents)
        self.db = Chroma.from_documents(docs, self.embedding)
        self._num_docs = len(docs)

        # Initialize chains
        self._init_chains()

    @abstractmethod
    def _init_chains(self):
        """Initialize the LLM chains for query generation"""
        pass

    def _get_relevant_schema(self, question: str) -> str:
        """Get relevant schema context based on the question"""
        if self.use_mock or not self.db:
            return self.schema

        k = min(3, self._num_docs)
        relevant_docs = self.db.similarity_search(question, k=k)
        return "\n".join([doc.page_content for doc in relevant_docs])

    @abstractmethod
    def _extract_query(self, text: str) -> str:
        """Extract query from model response"""
        pass

    @abstractmethod
    def generate(self, question: str) -> QueryGenerationResult:
        """Generate query from natural language question"""
        pass


class SQLGenerator(QueryGenerator):
    """SQL query generator"""

    def _init_chains(self):
        if self.use_mock:
            return
        sql_template = """You are an expert SQL assistant. Based on the schema below and the user question, generate a valid SQL query.

Schema:
{schema}

Question:
{question}

Output only the SQL query, nothing else."""

        self.query_chain = (
            PromptTemplate(
                input_variables=["schema", "question"], template=sql_template
            )
            | self.llm
            | StrOutputParser()
        )

        explanation_template = """Explain what the following SQL query does in plain English and one sentence:

{sql}"""
        self.explain_chain = (
            PromptTemplate.from_template(explanation_template)
            | self.llm
            | StrOutputParser()
        )

        compare_template = """Does this SQL query match the user's request? Answer Yes or No.

Question:
{question}

Schema:
{schema}

SQL Query:
{sql}

Explanation:
{explanation}"""
        self.compare_chain = (
            PromptTemplate.from_template(compare_template)
            | self.llm
            | StrOutputParser()
        )

    def _extract_query(self, text: str) -> str:
        pattern = r"\`\`\`sql(.*?)\`\`\`"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        if "SELECT" in text.upper() or "WITH" in text.upper():
            return text.strip()
        raise ValueError(f"Failed to parse SQL from response: {text}")

    def generate(self, question: str) -> QueryGenerationResult:
        if question is None:
            raise ValueError("Question is required")

        if self.use_mock:
            return self._generate_mock(question)

        try:
            schema_context = self._get_relevant_schema(question)
            query_response = self.query_chain.invoke(
                {"schema": schema_context, "question": question}
            )
            query = self._extract_query(query_response)
            explanation = self.explain_chain.invoke({"sql": query})
            validation = self.compare_chain.invoke(
                {
                    "question": question,
                    "schema": self.schema,
                    "sql": query,
                    "explanation": explanation,
                }
            )
            is_valid = "yes" in validation.lower()

            return QueryGenerationResult(
                query=query,
                explanation=explanation,
                is_valid=is_valid,
                query_type="sql",
            )

        except Exception as e:
            return QueryGenerationResult(
                query="",
                explanation="",
                is_valid=False,
                query_type="sql",
                error=str(e),
            )

    def _generate_mock(self, question: str) -> QueryGenerationResult:
        trimmed = question.strip()
        if not trimmed:
            return QueryGenerationResult(
                query="",
                explanation="",
                is_valid=False,
                query_type="sql",
                error="Question cannot be empty",
            )

        question_lower = trimmed.lower()
        domain_keywords = ("customer", "order", "product", "email")
        if not any(keyword in question_lower for keyword in domain_keywords):
            return QueryGenerationResult(
                query="",
                explanation="",
                is_valid=False,
                query_type="sql",
                error="Question is outside the supported analytics domain",
            )

        explanation = ""

        if "30 day" in question_lower:
            query = (
                "SELECT DISTINCT c.id, c.name, c.email\n"
                "FROM customers c\n"
                "JOIN orders o ON c.id = o.customer_id\n"
                "WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days';"
            )
            explanation = (
                "Lists customers who have placed an order in the last 30 days."
            )
        elif "order count" in question_lower:
            query = (
                "SELECT c.id, c.name, COUNT(o.id) AS order_count\n"
                "FROM customers c\n"
                "JOIN orders o ON c.id = o.customer_id\n"
                "GROUP BY c.id, c.name;"
            )
            explanation = "Returns each customer with their total order count."
        elif "average order" in question_lower or "avg" in question_lower:
            query = (
                "SELECT c.id, c.name, AVG(o.total) AS average_order_value\n"
                "FROM customers c\n"
                "JOIN orders o ON c.id = o.customer_id\n"
                "GROUP BY c.id, c.name;"
            )
            explanation = "Calculates the average order value per customer."
        elif "spent" in question_lower or "$" in question_lower:
            query = (
                "SELECT c.id, c.name, SUM(o.total) AS total_spent\n"
                "FROM customers c\n"
                "JOIN orders o ON c.id = o.customer_id\n"
                "WHERE o.total IS NOT NULL\n"
                "GROUP BY c.id, c.name\n"
                "HAVING SUM(o.total) > 1000;"
            )
            explanation = (
                "Finds customers whose aggregated spend is greater than 1000 units."
            )
        elif "haven't" in question_lower or "no order" in question_lower:
            query = (
                "SELECT c.id, c.name, c.email\n"
                "FROM customers c\n"
                "LEFT JOIN orders o ON c.id = o.customer_id\n"
                "WHERE o.id IS NULL;"
            )
            explanation = "Shows customers who have not placed any orders."
        elif "email" in question_lower:
            query = "SELECT c.id, c.name, c.email FROM customers c;"
            explanation = "Retrieves customers with their email addresses."
        else:
            query = (
                "SELECT c.id, c.name, o.order_date, o.total\n"
                "FROM customers c\n"
                "JOIN orders o ON c.id = o.customer_id;"
            )
            explanation = "Joins customers with their orders for general reporting."

        return QueryGenerationResult(
            query=query,
            explanation=explanation,
            is_valid=True,
            query_type="sql",
        )


class MongoDBGenerator(QueryGenerator):
    """MongoDB query generator"""

    def _init_chains(self):
        if self.use_mock:
            return
        mongodb_template = """You are an expert MongoDB query assistant. Based on the schema below and the user question, generate a valid MongoDB query.
Use proper MongoDB syntax and operators. Return the query as a Python dictionary that can be used with pymongo.

Schema:
{schema}

Question:
{question}

Output only the MongoDB query as a Python dict, nothing else. No code blocks, no backticks, no nothing."""

        self.query_chain = (
            PromptTemplate(
                input_variables=["schema", "question"], template=mongodb_template
            )
            | self.llm
            | StrOutputParser()
        )

        explanation_template = """Explain what the following MongoDB query does in plain English and one sentence:

{query}"""
        self.explain_chain = (
            PromptTemplate.from_template(explanation_template)
            | self.llm
            | StrOutputParser()
        )

        compare_template = """Does this MongoDB query match the user's request? Answer Yes or No.

Question:
{question}

Schema:
{schema}

MongoDB Query:
{query}

Explanation:
{explanation}"""
        self.compare_chain = (
            PromptTemplate.from_template(compare_template)
            | self.llm
            | StrOutputParser()
        )

    def _extract_query(self, text: str) -> str:
        pattern = r"\`\`\`python(.*?)\`\`\`"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        if "{" in text and "}" in text:
            return text.strip()
        raise ValueError(f"Failed to parse MongoDB query from response: {text}")

    def generate(self, question: str) -> QueryGenerationResult:
        if question is None:
            raise ValueError("Question is required")

        if self.use_mock:
            return self._generate_mock(question)

        try:
            schema_context = self._get_relevant_schema(question)
            query_response = self.query_chain.invoke(
                {"schema": schema_context, "question": question}
            )
            query = self._extract_query(query_response)
            explanation = self.explain_chain.invoke({"query": query})
            validation = self.compare_chain.invoke(
                {
                    "question": question,
                    "schema": self.schema,
                    "query": query,
                    "explanation": explanation,
                }
            )
            is_valid = "yes" in validation.lower()

            return QueryGenerationResult(
                query=query,
                explanation=explanation,
                is_valid=is_valid,
                query_type="mongodb",
            )

        except Exception as e:
            return QueryGenerationResult(
                query="",
                explanation="",
                is_valid=False,
                query_type="mongodb",
                error=str(e),
            )

    def _generate_mock(self, question: str) -> QueryGenerationResult:
        trimmed = question.strip()
        if not trimmed:
            return QueryGenerationResult(
                query="",
                explanation="",
                is_valid=False,
                query_type="mongodb",
                error="Question cannot be empty",
            )

        question_lower = trimmed.lower()
        domain_keywords = ("customer", "order", "product", "email")
        if not any(keyword in question_lower for keyword in domain_keywords):
            return QueryGenerationResult(
                query="",
                explanation="",
                is_valid=False,
                query_type="mongodb",
                error="Question is outside the supported analytics domain",
            )

        from pprint import pformat

        base_pipeline = {
            "$collection": "customers",
            "$lookup": {
                "from": "orders",
                "localField": "_id",
                "foreignField": "customer_id",
                "as": "orders",
            },
            "$metadata": {
                "example_customer_id": "ObjectId('000000000000000000000000')",
            },
        }

        explanation = ""

        if "30 day" in question_lower:
            query_dict = {
                **base_pipeline,
                "$unwind": {
                    "path": "$orders",
                    "preserveNullAndEmptyArrays": False,
                },
                "$match": {
                    "orders.order_date": {
                        "$gte": {
                            "$dateSubtract": {
                                "startDate": "$$NOW",
                                "unit": "day",
                                "amount": 30,
                            }
                        }
                    }
                },
                "$group": {
                    "_id": "$_id",
                    "name": {"$first": "$name"},
                    "email": {"$first": "$email"},
                },
            }
            explanation = "Returns customers who have orders within the last 30 days."
        elif "order count" in question_lower:
            query_dict = {
                **base_pipeline,
                "$group": {
                    "_id": "$_id",
                    "name": {"$first": "$name"},
                    "order_count": {"$sum": 1},
                },
                "$project": {
                    "name": 1,
                    "order_count": 1,
                },
            }
            explanation = "Counts the number of orders per customer."
        elif "average order" in question_lower or "avg" in question_lower:
            query_dict = {
                **base_pipeline,
                "$group": {
                    "_id": "$_id",
                    "name": {"$first": "$name"},
                    "average_order_value": {"$avg": "$orders.total"},
                },
            }
            explanation = "Calculates average order value for every customer."
        elif "spent" in question_lower or "$" in question_lower:
            query_dict = {
                **base_pipeline,
                "$group": {
                    "_id": "$_id",
                    "name": {"$first": "$name"},
                    "total_spent": {"$sum": "$orders.total"},
                    "last_order": {"$max": "$orders.order_date"},
                },
                "$match": {
                    "total_spent": {"$gt": 1000},
                },
            }
            explanation = "Filters for customers who spent more than 1000 overall."
        elif "email" in question_lower:
            query_dict = {
                **base_pipeline,
                "$project": {
                    "name": 1,
                    "email": 1,
                    "orders.customer_id": "ObjectId('dummy')",
                },
            }
            explanation = "Lists customer contact information."
        else:
            query_dict = {
                **base_pipeline,
                "$project": {
                    "name": 1,
                    "orders": 1,
                    "email": 1,
                },
            }
            explanation = "Provides a joined view of customers and their orders."

        query_str = pformat(query_dict, width=80)

        return QueryGenerationResult(
            query=query_str,
            explanation=explanation,
            is_valid=True,
            query_type="mongodb",
        )
