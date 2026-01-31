import sqlglot
from sqlglot import exp

class SchemaManager:
    def __init__(self):
        self.tables = {}

    def load_from_file(self, file_path):
        with open(file_path, 'r') as f:
            sql = f.read()
        self.parse_sql(sql)

    def parse_sql(self, sql):
        parsed = sqlglot.parse(sql)
        for expression in parsed:
            if isinstance(expression, exp.Create):
                self._handle_create_table(expression)

    def _handle_create_table(self, expression):
        # sqlglot Create expression structure:
        # this -> The Schema object (which contains the Table and the expressions/columns)
        # OR this -> The Table object, and expressions -> columns
        
        table_name = None
        columns = []

        if expression.kind == "TABLE":
            # In recent sqlglot, 'this' is often a Schema object for CREATE TABLE with columns
            # Schema(this=Table(this='test'), expressions=[ColumnDef(...)])
            if isinstance(expression.this, exp.Schema):
                schema_node = expression.this
                if isinstance(schema_node.this, exp.Table):
                    table_name = schema_node.this.name
                else:
                    table_name = schema_node.this.name if hasattr(schema_node.this, 'name') else str(schema_node.this)
                
                for col in schema_node.expressions:
                     if isinstance(col, exp.ColumnDef):
                        col_name = col.this.name
                        col_type = col.kind.this.name.upper() if col.kind else "TEXT"
                        columns.append({"name": col_name, "type": col_type})

            # Fallback/Alternative structure (e.g. if just CREATE TABLE x without columns or different dialect)
            elif isinstance(expression.this, exp.Table):
                table_name = expression.this.name
                # Check properties or expressions on Create node?
                # Usually if columns are present, it's a Schema node in 'this'
                pass

            if table_name:
                self.tables[table_name] = columns

    def get_table(self, table_name):
        return self.tables.get(table_name)
