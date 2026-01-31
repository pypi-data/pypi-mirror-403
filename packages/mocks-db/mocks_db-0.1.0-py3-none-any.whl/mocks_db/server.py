import logging
from mysql_mimic import MysqlServer, IdentityProvider, Session
from mysql_mimic.errors import MysqlError
import sqlglot
from sqlglot import exp

from mocks_db.generator import DataGenerator

logger = logging.getLogger(__name__)

class MockIdentityProvider(IdentityProvider):
    def __init__(self, **kwargs):
        pass

    def get_password(self, username):
        # Allow everyone
        return None

class MockSession(Session):
    def __init__(self, schema_manager, default_limit=10):
        super().__init__()
        self.schema_manager = schema_manager
        self.generator = DataGenerator()
        self.default_limit = default_limit

    async def query(self, expression, sql):
        # Parse the SQL to understand what is being requested
        # We primarily support SELECT queries on known tables
        try:
            parsed = sqlglot.parse_one(sql)
        except Exception as e:
            logger.error(f"Failed to parse SQL: {e}")
            raise MysqlError(f"Syntax error: {e}")

        if isinstance(parsed, exp.Select):
            return self._handle_select(parsed)
        elif isinstance(parsed, exp.Use):
            # Just ignore USE database
            return None
        elif isinstance(parsed, exp.Set):
            # Ignore SET
            return None
        else:
            # For other queries, return empty result or error
            # For broad compatibility, maybe just return empty
            logger.info(f"Ignored query type: {type(parsed)}")
            return [], []

    def _handle_select(self, expression):
        # Find table name
        table_name = None
        for table in expression.find_all(exp.Table):
            table_name = table.name
            break
        
        if not table_name:
             raise MysqlError("No table specified")

        # Get schema
        table_schema = self.schema_manager.get_table(table_name)
        if not table_schema:
            if table_name.lower() == 'dual':
                return [], []
            raise MysqlError(f"Table '{table_name}' doesn't exist in mock schema")

        # Determine columns to return
        # expression.expressions contains the selected items
        selected_columns = []
        is_star = False
        
        for expr in expression.expressions:
            if isinstance(expr, exp.Star):
                is_star = True
                break
            # Logic to extract column name. Simplistic for now.
            if isinstance(expr, exp.Column):
                selected_columns.append(expr.this.this) # this.this is the identifier
            elif isinstance(expr, exp.Alias):
                selected_columns.append(expr.alias)
            else:
                # Fallback for literals or other expressions, currently not supported fully
                # so we just generate a random column name or skip
                # mocking data for function calls is hard without type info
                selected_columns.append(expr.alias_or_name)

        target_columns = []
        if is_star:
            target_columns = table_schema
        else:
            # Filter schema columns based on selection
            for col_name in selected_columns:
                # Find column in schema
                found = False
                for schema_col in table_schema:
                    if schema_col['name'] == col_name:
                        target_columns.append(schema_col)
                        found = True
                        break
                if not found:
                    # If requested column is not in schema, we should probably still return something
                    # to keep the client happy, maybe default to String type
                    target_columns.append({"name": col_name, "type": "VARCHAR"})

        # Determine limit
        limit = self.default_limit
        # expression.limit is a method, so check arguments
        limit_expr = expression.args.get('limit')
        if limit_expr:
            try:
                # limit_expr is a Limit object.
                # Debugging showed limit_expr.this is None.
                # limit_expr.expression is the Literal(5)
                # so limit_expr.expression.this is '5'
                val = limit_expr.expression.this
                limit = int(val)
            except Exception as e:
                logger.warning(f"Failed to parse limit: {e}")
                pass

        # Generate data
        rows = []
        for _ in range(limit):
            rows.append(self.generator.generate_row(target_columns))

        col_names = [c['name'] for c in target_columns]
        
        return rows, col_names

    async def schema(self):
        # mimic doesn't strictly require this if we handle queries manually
        return "mocks_db"
