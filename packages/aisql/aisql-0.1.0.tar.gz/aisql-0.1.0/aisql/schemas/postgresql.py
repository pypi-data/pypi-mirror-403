"""PostgreSQL database schema definition"""

SCHEMA = """
Table: customers
- id (int)
- name (varchar)
- email (varchar)

Table: orders
- id (int)
- customer_id (int)
- order_date (date)
- total (float)
"""
