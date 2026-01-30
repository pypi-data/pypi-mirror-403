from dotenv import load_dotenv
from src.mcp_server_mariadb.server import get_connection, is_read_only_query

load_dotenv()


def test_db_connection():
    connection = get_connection()

    assert connection is not None


def test_is_read_only_query():
    assert is_read_only_query("SELECT * FROM users")
    assert is_read_only_query("SHOW TABLES")
    assert is_read_only_query("DESCRIBE users")
    assert is_read_only_query("DESC users")
    assert is_read_only_query("EXPLAIN SELECT * FROM users")


def test_is_not_read_only_query():
    assert not is_read_only_query(
        "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
    )
    assert not is_read_only_query(
        "UPDATE users SET email = 'john@example.com' WHERE id = 1"
    )
    assert not is_read_only_query("DELETE FROM users WHERE id = 1")
    assert not is_read_only_query(
        "CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255))"
    )
    assert not is_read_only_query("DROP TABLE users")
