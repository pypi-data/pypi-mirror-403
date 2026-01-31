import pytest
import asyncio
from mocks_db.schema import SchemaManager
from mocks_db.server import MockSession
from mocks_db.generator import DataGenerator

# Sample Schema
SCHEMA_SQL = """
CREATE TABLE users (
    id INT,
    name VARCHAR(255),
    email VARCHAR(255),
    created_at DATETIME
);
"""

@pytest.fixture
def schema_manager(tmp_path):
    f = tmp_path / "schema.sql"
    f.write_text(SCHEMA_SQL)
    sm = SchemaManager()
    sm.load_from_file(str(f))
    return sm

def test_schema_parsing_file(schema_manager):
    assert "users" in schema_manager.tables
    columns = schema_manager.tables["users"]
    assert len(columns) == 4
    assert columns[0]["name"] == "id"
    assert columns[0]["type"] == "INT"

def test_schema_parsing_string():
    sm = SchemaManager()
    sql = "CREATE TABLE products (id INT, price DECIMAL);"
    sm.parse_sql(sql)
    assert "products" in sm.tables
    assert len(sm.tables["products"]) == 2


def test_data_generation():
    dg = DataGenerator()
    columns = [
        {"name": "id", "type": "INT"},
        {"name": "name", "type": "VARCHAR"},
    ]
    row = dg.generate_row(columns)
    assert len(row) == 2
    assert isinstance(row[0], int)
    assert isinstance(row[1], str)

@pytest.mark.asyncio
async def test_server_query_select(schema_manager):
    session = MockSession(schema_manager)
    
    # Query with Limit
    sql = "SELECT id, name FROM users LIMIT 5"
    # mocking the expression object is hard, but we can rely on integration test 
    # OR we can just test the _handle_select if we can parse it first.
    # But MockSession.query cleans up the parsing.
    
    # We need to install sqlglot to run this test actually
    rows, cols = await session.query(None, sql) 
    
    assert len(rows) == 5
    assert len(cols) == 2 
    assert cols == ['id', 'name']
    # Wait, my implementation of _handle_select ignores the selected columns and returns all defined in schema?
    # Let's check server.py
    
    pass

@pytest.mark.asyncio
async def test_server_query_no_limit(schema_manager):
    session = MockSession(schema_manager, default_limit=3)
    sql = "SELECT * FROM users"
    rows, cols = await session.query(None, sql)
    assert len(rows) == 3
