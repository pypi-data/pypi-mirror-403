import psycopg2
from .repositories import ComponentRepository
from .util import Util

class DatabaseConnection:
    """
    Class to handle PostgreSQL database connections
    using AWS Secrets Manager credentials
    """
    
    def __init__(self):
        self.connection = None
        self._credentials = None

    def connect(self, credentials):
        """Establishes database connection using credentials"""
        try:
            self.connection = psycopg2.connect(
                host=credentials['host'],
                port=credentials['port'],
                database=credentials['dbname'],
                user=credentials['username'],
                password=credentials['password'],
                connect_timeout=30,
                sslmode='require',
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            self._credentials = credentials
        except Exception as e:
            raise Exception(f"Database connection error: {str(e)}")

    def close(self):
        """Closes the database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def commit_transaction(self):
        """Commits pending transactions"""
        if self.connection and not self.connection.closed:
            self.connection.commit()

    def rollback_transaction(self):
        """Rolls back pending transactions in case of error"""
        if self.connection and not self.connection.closed:
            self.connection.rollback()

    def ensure_connection(self):
        """Verifies connection is alive and reconnects if necessary"""
        try:
            if self.connection is None or self.connection.closed:
                if self._credentials:
                    print("⚠️ Reconnecting to database...")
                    self.connect(self._credentials)
                else:
                    raise Exception("Connection is closed and no credentials available for reconnection")
        except Exception as e:
            if self._credentials:
                print(f"⚠️ Connection lost, attempting reconnection: {str(e)}")
                self.connect(self._credentials)
            else:
                raise Exception(f"Cannot ensure connection: {str(e)}")

    def get_connection_database_from_secret(secret_name: str, logger: str, aws_region: str) -> ComponentRepository:
        """
        Retrieve connection database from AWS secrets manager
        """
        secret_json = Util.get_secret_aws(secret_name, logger, aws_region)
        db_connection = DatabaseConnection()
        db_connection.connect({
            'host': secret_json["host"],
            'port': secret_json["port"],
            'dbname': secret_json["dbname"],
            'username': secret_json["username"],
        'password': secret_json["password"]
        })
        return ComponentRepository(db_connection)