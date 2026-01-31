# Mocks DB

![License](https://img.shields.io/github/license/pratyush/mocks-db)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

**Mocks DB** is a lightweight, mock MySQL server designed for testing and development. It accepts any standard MySQL connection and query, but instead of storing data, it generates realistic "junk" data on the fly based on your provided schema.

Perfect for performance testing, UI development, or any scenario where you need a database that acts like the real thing but populates itself.

## Features

- **MySQL Protocol Support**: Connect with any standard MySQL client (CLI, Workbench, generic libraries).
- **Dynamic Data Generation**: Uses [Faker](https://github.com/joke2k/faker) to generate realistic data based on column types.
- **Schema Awareness**: define your table structures via standard `CREATE TABLE` statements.
- **Configurable**: Control row counts, limits, and random seeds.
- **Zero Storage**: No disk I/O for data, everything is generated in memory on demand.

## Installation

```bash
pip install mocks-db
```

## Usage

Run the server with a file:
```bash
mocks-db --schema schema.sql --port 3306
```

Or pass the schema directly as a string:
```bash
mocks-db --schema-content "CREATE TABLE users (id INT, name VARCHAR(255));" --port 3306
```

Connect with your favorite client:

```bash
mysql -h 127.0.0.1 -P 3306 -u root
```

Run queries:

```sql
SELECT * FROM users LIMIT 10;
```

## Development

To develop and test locally without installing from a remote repository:

1.  Clone the repo (if you haven't already).
2.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies and the package in **editable mode**:
    ```bash
    pip install -e .
    ```
4.  Run the server:
    ```bash
    mocks-db --schema-content "CREATE TABLE test (id INT);"
    ```
    
    Or run efficiently via python module:
    ```bash
    python -m mocks_db.main --help
    ```

5.  Install development dependencies and run tests:
    
    This project uses `pyproject.toml` for dependency management. You can install the package along with development dependencies (like pytest) using the `[dev]` extra:
    
    ```bash
    pip install -e ".[dev]"
    ```
    
    Or use the legacy requirements style:
    ```bash
    pip install -r requirements-dev.txt
    ```

    Then run tests:
    ```bash
    pytest
    ```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)
