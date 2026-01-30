"""MongoDB database schema definition"""

SCHEMA = """
Collection: customers
{
    _id: ObjectId,
    name: String,
    email: String
}

Collection: orders
{
    _id: ObjectId,
    customer_id: ObjectId,
    order_date: Date,
    total: Number
}
"""
