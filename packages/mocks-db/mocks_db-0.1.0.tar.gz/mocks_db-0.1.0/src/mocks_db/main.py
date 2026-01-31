import asyncio
import click
import logging
from mysql_mimic import MysqlServer, IdentityProvider

from mocks_db.server import MockIdentityProvider, MockSession
from mocks_db.schema import SchemaManager

logging.basicConfig(level=logging.INFO)

async def start_server(port, host, schema_manager, default_limit):
    def session_factory():
        return MockSession(schema_manager, default_limit=default_limit)

    server = MysqlServer(
        session_factory=session_factory,
        identity_provider=MockIdentityProvider(),
    )
    
    print(f"Server starting on {host}:{port}...")
    await server.serve_forever(port=port, host=host)

@click.command()
@click.option('--port', default=3306, help='Port to listen on')
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--schema', help='Path to schema SQL file')
@click.option('--schema-content', help='Raw schema SQL string')
@click.option('--default-limit', default=10, help='Default number of rows if NO LIMIT specified')
def cli(port, host, schema, schema_content, default_limit):
    """Start the mocks-db server.
    
    You must provide either --schema (path to file) or --schema-content (sql string).
    """
    schema_manager = SchemaManager()
    try:
        if schema:
            schema_manager.load_from_file(schema)
            click.echo(f"Loaded schema from file: {schema}")
        elif schema_content:
            schema_manager.parse_sql(schema_content)
            click.echo("Loaded schema from provided content string")
        else:
            click.echo("Error: You must provide either --schema or --schema-content", err=True)
            return
            
        click.echo(f"Known tables: {list(schema_manager.tables.keys())}")
    except Exception as e:
        click.echo(f"Error loading schema: {e}", err=True)
        return

    try:
        asyncio.run(start_server(port, host, schema_manager, default_limit))
    except KeyboardInterrupt:
        click.echo("Server stopped.")

if __name__ == '__main__':
    cli()
