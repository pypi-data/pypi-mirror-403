"""
Universal SQL Database Connection Module

This module provides database connection functionality and configuration loading
for the MCP server, supporting multiple database engines including MySQL, PostgreSQL, SQLite, and SQL Server.
"""

import os
import logging
import sqlite3
from typing import Dict, List, Any, Optional, Union
from contextlib import contextmanager
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Import database drivers
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    from psycopg2 import Error as PostgreSQLError
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import pyodbc
    SQLSERVER_AVAILABLE = True
except ImportError:
    SQLSERVER_AVAILABLE = False


# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Universal database configuration class"""

    def __init__(self):
        self.db_type = os.getenv('DB_TYPE', 'mysql').lower()
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = self._get_default_port()
        self.user = os.getenv('DB_USER', '')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', '')
        self.driver = os.getenv('DB_DRIVER', '')  # For SQL Server
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '5'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '10'))
        self.connect_timeout = int(os.getenv('DB_CONNECT_TIMEOUT', '10'))
        self.read_timeout = int(os.getenv('DB_READ_TIMEOUT', '30'))
        self.write_timeout = int(os.getenv('DB_WRITE_TIMEOUT', '30'))
        # 控制是否启用写操作工具的配置项
        self.enable_write_operations = os.getenv('ENABLE_WRITE_OPERATIONS', 'false').lower() in ('true', '1', 'yes', 'on')
    
    def _get_default_port(self) -> int:
        """Get default port based on database type"""
        port_str = os.getenv('DB_PORT', '')
        if port_str:
            return int(port_str)
        
        default_ports = {
            'mysql': 3306,
            'postgresql': 5432,
            'sqlserver': 1433,
            'sqlite': 0  # SQLite doesn't use ports
        }
        return default_ports.get(self.db_type, 3306)
    
    def validate(self) -> bool:
        """Validate required configuration parameters"""
        if self.db_type not in ['mysql', 'postgresql', 'sqlite', 'sqlserver']:
            logger.error(f"Unsupported database type: {self.db_type}")
            return False
        
        # SQLite only needs database file path
        if self.db_type == 'sqlite':
            if not self.database:
                logger.error("Missing required database file path for SQLite")
                return False
            return True
        
        # Other databases need connection parameters
        required_fields = ['host', 'user', 'database']
        for field in required_fields:
            if not getattr(self, field):
                logger.error(f"Missing required database configuration: {field}")
                return False
        
        # Check if required driver is available
        if self.db_type == 'mysql' and not MYSQL_AVAILABLE:
            logger.error("MySQL driver not available. Install mysql-connector-python")
            return False
        elif self.db_type == 'postgresql' and not POSTGRESQL_AVAILABLE:
            logger.error("PostgreSQL driver not available. Install psycopg2-binary")
            return False
        elif self.db_type == 'sqlserver' and not SQLSERVER_AVAILABLE:
            logger.error("SQL Server driver not available. Install pyodbc")
            return False
        
        return True



class DatabaseConnector(ABC):
    """Abstract base class for database connectors"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
    
    @abstractmethod
    def get_connection(self):
        """Get database connection"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test database connection"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query"""
        pass
    
    @abstractmethod
    def execute_write_operation(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Execute write operation"""
        pass
    
    @abstractmethod
    def get_table_descriptions(self) -> List[Dict[str, Any]]:
        """Get table descriptions"""
        pass


class MySQLConnector(DatabaseConnector):
    """MySQL database connector"""
    
    @contextmanager
    def get_connection(self):
        """Context manager for MySQL connections"""
        connection = None
        try:
            connection_config = {
                'host': self.config.host,
                'port': self.config.port,
                'user': self.config.user,
                'password': self.config.password,
                'database': self.config.database,
                'connection_timeout': self.config.connect_timeout,
                'autocommit': True,
                'charset': 'utf8mb4',
                'use_unicode': True,
            }
            connection = mysql.connector.connect(**connection_config)
            logger.info("MySQL connection established")
            yield connection
        except MySQLError as e:
            logger.error(f"MySQL connection error: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
                logger.info("MySQL connection closed")
    
    def test_connection(self) -> bool:
        """Test MySQL connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result[0] == 1
        except Exception as e:
            logger.error(f"MySQL connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute MySQL SELECT query"""
        query_stripped = query.strip().upper()
        if not query_stripped.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params)
                results = cursor.fetchall()
                cursor.close()
                logger.info(f"MySQL query executed successfully, returned {len(results)} rows")
                return results
        except MySQLError as e:
            logger.error(f"MySQL query execution error: {e}")
            raise
    
    def execute_write_operation(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Execute MySQL write operation"""
        query_stripped = query.strip().upper()
        allowed_operations = ['INSERT', 'UPDATE']

        if not any(query_stripped.startswith(op) for op in allowed_operations):
            raise ValueError("Only INSERT and UPDATE operations are allowed")

        forbidden_keywords = ['DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE']
        for keyword in forbidden_keywords:
            if keyword in query_stripped:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                affected_rows = cursor.rowcount
                last_insert_id = cursor.lastrowid if query_stripped.startswith('INSERT') else None
                conn.commit()
                cursor.close()
                logger.info(f"MySQL write operation executed successfully, {affected_rows} rows affected")
                return {
                    "affected_rows": affected_rows,
                    "last_insert_id": last_insert_id
                }
        except MySQLError as e:
            logger.error(f"MySQL write operation execution error: {e}")
            raise
    
    def get_table_descriptions(self) -> List[Dict[str, Any]]:
        """Get MySQL table descriptions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # Get all tables with their comments
                cursor.execute("""
                    SELECT 
                        TABLE_NAME as table_name,
                        TABLE_COMMENT as table_comment,
                        ENGINE as engine,
                        TABLE_ROWS as estimated_rows,
                        DATA_LENGTH as data_length,
                        INDEX_LENGTH as index_length
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """, (self.config.database,))
                
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table['table_name']
                    
                    # Get column information
                    cursor.execute("""
                        SELECT 
                            COLUMN_NAME as column_name,
                            DATA_TYPE as data_type,
                            IS_NULLABLE as is_nullable,
                            COLUMN_DEFAULT as column_default,
                            COLUMN_COMMENT as column_comment,
                            COLUMN_KEY as column_key,
                            EXTRA as extra,
                            CHARACTER_MAXIMUM_LENGTH as max_length,
                            NUMERIC_PRECISION as numeric_precision,
                            NUMERIC_SCALE as numeric_scale
                        FROM information_schema.COLUMNS 
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION
                    """, (self.config.database, table_name))
                    
                    table['columns'] = cursor.fetchall()
                    
                    # Get index information
                    cursor.execute("""
                        SELECT 
                            INDEX_NAME as index_name,
                            COLUMN_NAME as column_name,
                            NON_UNIQUE as non_unique,
                            SEQ_IN_INDEX as sequence,
                            INDEX_TYPE as index_type,
                            INDEX_COMMENT as index_comment
                        FROM information_schema.STATISTICS 
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        ORDER BY INDEX_NAME, SEQ_IN_INDEX
                    """, (self.config.database, table_name))
                    
                    indexes = cursor.fetchall()
                    
                    # Group indexes by name
                    index_dict = {}
                    for idx in indexes:
                        idx_name = idx['index_name']
                        if idx_name not in index_dict:
                            index_dict[idx_name] = {
                                'index_name': idx_name,
                                'non_unique': idx['non_unique'],
                                'index_type': idx['index_type'],
                                'index_comment': idx['index_comment'],
                                'columns': []
                            }
                        index_dict[idx_name]['columns'].append({
                            'column_name': idx['column_name'],
                            'sequence': idx['sequence']
                        })
                    
                    table['indexes'] = list(index_dict.values())
                
                cursor.close()
                logger.info(f"Retrieved MySQL information for {len(tables)} tables")
                return tables
                
        except MySQLError as e:
            logger.error(f"Error getting MySQL table descriptions: {e}")
            raise


class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL database connector"""
    
    @contextmanager
    def get_connection(self):
        """Context manager for PostgreSQL connections"""
        connection = None
        try:
            connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                connect_timeout=self.config.connect_timeout
            )
            connection.autocommit = True
            logger.info("PostgreSQL connection established")
            yield connection
        except PostgreSQLError as e:
            logger.error(f"PostgreSQL connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()
                logger.info("PostgreSQL connection closed")
    
    def test_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result[0] == 1
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute PostgreSQL SELECT query"""
        query_stripped = query.strip().upper()
        if not query_stripped.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, params)
                results = [dict(row) for row in cursor.fetchall()]
                cursor.close()
                logger.info(f"PostgreSQL query executed successfully, returned {len(results)} rows")
                return results
        except PostgreSQLError as e:
            logger.error(f"PostgreSQL query execution error: {e}")
            raise
    
    def execute_write_operation(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Execute PostgreSQL write operation"""
        query_stripped = query.strip().upper()
        allowed_operations = ['INSERT', 'UPDATE']

        if not any(query_stripped.startswith(op) for op in allowed_operations):
            raise ValueError("Only INSERT and UPDATE operations are allowed")

        forbidden_keywords = ['DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE']
        for keyword in forbidden_keywords:
            if keyword in query_stripped:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                affected_rows = cursor.rowcount
                # PostgreSQL doesn't have lastrowid like MySQL, need to use RETURNING clause
                last_insert_id = None
                cursor.close()
                logger.info(f"PostgreSQL write operation executed successfully, {affected_rows} rows affected")
                return {
                    "affected_rows": affected_rows,
                    "last_insert_id": last_insert_id
                }
        except PostgreSQLError as e:
            logger.error(f"PostgreSQL write operation execution error: {e}")
            raise
    
    def get_table_descriptions(self) -> List[Dict[str, Any]]:
        """Get PostgreSQL table descriptions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Get all tables
                cursor.execute("""
                    SELECT 
                        t.table_name,
                        obj_description(c.oid) as table_comment,
                        'PostgreSQL' as engine,
                        s.n_tup_ins + s.n_tup_upd + s.n_tup_del as estimated_rows,
                        pg_total_relation_size(c.oid) as data_length,
                        pg_indexes_size(c.oid) as index_length
                    FROM information_schema.tables t
                    LEFT JOIN pg_class c ON c.relname = t.table_name
                    LEFT JOIN pg_stat_user_tables s ON s.relname = t.table_name
                    WHERE t.table_schema = 'public' 
                    AND t.table_type = 'BASE TABLE'
                    ORDER BY t.table_name
                """)
                
                tables = [dict(row) for row in cursor.fetchall()]
                
                for table in tables:
                    table_name = table['table_name']
                    
                    # Get column information
                    cursor.execute("""
                        SELECT 
                            c.column_name,
                            c.data_type,
                            c.is_nullable,
                            c.column_default,
                            col_description(pgc.oid, c.ordinal_position) as column_comment,
                            CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'PRI'
                                 WHEN tc.constraint_type = 'UNIQUE' THEN 'UNI'
                                 ELSE ''
                            END as column_key,
                            '' as extra,
                            c.character_maximum_length as max_length,
                            c.numeric_precision,
                            c.numeric_scale
                        FROM information_schema.columns c
                        LEFT JOIN pg_class pgc ON pgc.relname = c.table_name
                        LEFT JOIN information_schema.key_column_usage kcu 
                            ON kcu.table_name = c.table_name AND kcu.column_name = c.column_name
                        LEFT JOIN information_schema.table_constraints tc 
                            ON tc.constraint_name = kcu.constraint_name
                        WHERE c.table_schema = 'public' AND c.table_name = %s
                        ORDER BY c.ordinal_position
                    """, (table_name,))
                    
                    table['columns'] = [dict(row) for row in cursor.fetchall()]
                    
                    # Get index information (simplified for PostgreSQL)
                    cursor.execute("""
                        SELECT 
                            i.relname as index_name,
                            a.attname as column_name,
                            NOT ix.indisunique as non_unique,
                            a.attnum as sequence,
                            am.amname as index_type,
                            '' as index_comment
                        FROM pg_class t
                        JOIN pg_index ix ON t.oid = ix.indrelid
                        JOIN pg_class i ON i.oid = ix.indexrelid
                        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                        JOIN pg_am am ON i.relam = am.oid
                        WHERE t.relname = %s
                        ORDER BY i.relname, a.attnum
                    """, (table_name,))
                    
                    indexes = [dict(row) for row in cursor.fetchall()]
                    
                    # Group indexes by name
                    index_dict = {}
                    for idx in indexes:
                        idx_name = idx['index_name']
                        if idx_name not in index_dict:
                            index_dict[idx_name] = {
                                'index_name': idx_name,
                                'non_unique': idx['non_unique'],
                                'index_type': idx['index_type'],
                                'index_comment': idx['index_comment'],
                                'columns': []
                            }
                        index_dict[idx_name]['columns'].append({
                            'column_name': idx['column_name'],
                            'sequence': idx['sequence']
                        })
                    
                    table['indexes'] = list(index_dict.values())
                
                cursor.close()
                logger.info(f"Retrieved PostgreSQL information for {len(tables)} tables")
                return tables
                
        except PostgreSQLError as e:
            logger.error(f"Error getting PostgreSQL table descriptions: {e}")
            raise


class SQLiteConnector(DatabaseConnector):
    """SQLite database connector"""
    
    @contextmanager
    def get_connection(self):
        """Context manager for SQLite connections"""
        connection = None
        try:
            connection = sqlite3.connect(self.config.database, timeout=self.config.connect_timeout)
            connection.row_factory = sqlite3.Row  # Enable dict-like access
            logger.info("SQLite connection established")
            yield connection
        except sqlite3.Error as e:
            logger.error(f"SQLite connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()
                logger.info("SQLite connection closed")
    
    def test_connection(self) -> bool:
        """Test SQLite connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result[0] == 1
        except Exception as e:
            logger.error(f"SQLite connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute SQLite SELECT query"""
        query_stripped = query.strip().upper()
        if not query_stripped.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                results = [dict(row) for row in cursor.fetchall()]
                cursor.close()
                logger.info(f"SQLite query executed successfully, returned {len(results)} rows")
                return results
        except sqlite3.Error as e:
            logger.error(f"SQLite query execution error: {e}")
            raise
    
    def execute_write_operation(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Execute SQLite write operation"""
        query_stripped = query.strip().upper()
        allowed_operations = ['INSERT', 'UPDATE']

        if not any(query_stripped.startswith(op) for op in allowed_operations):
            raise ValueError("Only INSERT and UPDATE operations are allowed")

        forbidden_keywords = ['DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE']
        for keyword in forbidden_keywords:
            if keyword in query_stripped:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                affected_rows = cursor.rowcount
                last_insert_id = cursor.lastrowid if query_stripped.startswith('INSERT') else None
                conn.commit()
                cursor.close()
                logger.info(f"SQLite write operation executed successfully, {affected_rows} rows affected")
                return {
                    "affected_rows": affected_rows,
                    "last_insert_id": last_insert_id
                }
        except sqlite3.Error as e:
            logger.error(f"SQLite write operation execution error: {e}")
            raise
    
    def get_table_descriptions(self) -> List[Dict[str, Any]]:
        """Get SQLite table descriptions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("""
                    SELECT name as table_name 
                    FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                
                table_names = [row[0] for row in cursor.fetchall()]
                tables = []
                
                for table_name in table_names:
                    table = {
                        'table_name': table_name,
                        'table_comment': 'No comment',
                        'engine': 'SQLite',
                        'estimated_rows': 0,
                        'data_length': 0,
                        'index_length': 0,
                        'columns': [],
                        'indexes': []
                    }
                    
                    # Get column information
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    for col in columns:
                        column_info = {
                            'column_name': col[1],
                            'data_type': col[2],
                            'is_nullable': 'YES' if not col[3] else 'NO',
                            'column_default': col[4],
                            'column_comment': 'No comment',
                            'column_key': 'PRI' if col[5] else '',
                            'extra': '',
                            'max_length': None,
                            'numeric_precision': None,
                            'numeric_scale': None
                        }
                        table['columns'].append(column_info)
                    
                    # Get index information
                    cursor.execute(f"PRAGMA index_list({table_name})")
                    indexes = cursor.fetchall()
                    
                    for idx in indexes:
                        cursor.execute(f"PRAGMA index_info({idx[1]})")
                        index_columns = cursor.fetchall()
                        
                        index_info = {
                            'index_name': idx[1],
                            'non_unique': not idx[2],
                            'index_type': 'BTREE',
                            'index_comment': 'No comment',
                            'columns': [{'column_name': col[2], 'sequence': col[0]} for col in index_columns]
                        }
                        table['indexes'].append(index_info)
                    
                    tables.append(table)
                
                cursor.close()
                logger.info(f"Retrieved SQLite information for {len(tables)} tables")
                return tables
                
        except sqlite3.Error as e:
            logger.error(f"Error getting SQLite table descriptions: {e}")
            raise


class SQLServerConnector(DatabaseConnector):
    """SQL Server database connector"""
    
    @contextmanager
    def get_connection(self):
        """Context manager for SQL Server connections"""
        connection = None
        try:
            driver = self.config.driver or "ODBC Driver 17 for SQL Server"
            connection_string = (
                f"DRIVER={{{driver}}};"
                f"SERVER={self.config.host},{self.config.port};"
                f"DATABASE={self.config.database};"
                f"UID={self.config.user};"
                f"PWD={self.config.password};"
                f"Timeout={self.config.connect_timeout};"
            )
            connection = pyodbc.connect(connection_string)
            connection.autocommit = True
            logger.info("SQL Server connection established")
            yield connection
        except pyodbc.Error as e:
            logger.error(f"SQL Server connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()
                logger.info("SQL Server connection closed")
    
    def test_connection(self) -> bool:
        """Test SQL Server connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result[0] == 1
        except Exception as e:
            logger.error(f"SQL Server connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute SQL Server SELECT query"""
        query_stripped = query.strip().upper()
        if not query_stripped.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                cursor.close()
                logger.info(f"SQL Server query executed successfully, returned {len(results)} rows")
                return results
        except pyodbc.Error as e:
            logger.error(f"SQL Server query execution error: {e}")
            raise
    
    def execute_write_operation(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Execute SQL Server write operation"""
        query_stripped = query.strip().upper()
        allowed_operations = ['INSERT', 'UPDATE']

        if not any(query_stripped.startswith(op) for op in allowed_operations):
            raise ValueError("Only INSERT and UPDATE operations are allowed")

        forbidden_keywords = ['DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE']
        for keyword in forbidden_keywords:
            if keyword in query_stripped:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                affected_rows = cursor.rowcount
                # SQL Server doesn't have a direct equivalent to lastrowid
                last_insert_id = None
                cursor.close()
                logger.info(f"SQL Server write operation executed successfully, {affected_rows} rows affected")
                return {
                    "affected_rows": affected_rows,
                    "last_insert_id": last_insert_id
                }
        except pyodbc.Error as e:
            logger.error(f"SQL Server write operation execution error: {e}")
            raise
    
    def get_table_descriptions(self) -> List[Dict[str, Any]]:
        """Get SQL Server table descriptions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("""
                    SELECT 
                        t.TABLE_NAME as table_name,
                        ISNULL(ep.value, 'No comment') as table_comment,
                        'SQL Server' as engine,
                        0 as estimated_rows,
                        0 as data_length,
                        0 as index_length
                    FROM INFORMATION_SCHEMA.TABLES t
                    LEFT JOIN sys.tables st ON st.name = t.TABLE_NAME
                    LEFT JOIN sys.extended_properties ep ON ep.major_id = st.object_id AND ep.minor_id = 0
                    WHERE t.TABLE_TYPE = 'BASE TABLE'
                    ORDER BY t.TABLE_NAME
                """)
                
                columns = [column[0] for column in cursor.description]
                tables = []
                for row in cursor.fetchall():
                    table = dict(zip(columns, row))
                    table_name = table['table_name']
                    
                    # Get column information
                    cursor.execute("""
                        SELECT 
                            c.COLUMN_NAME as column_name,
                            c.DATA_TYPE as data_type,
                            c.IS_NULLABLE as is_nullable,
                            c.COLUMN_DEFAULT as column_default,
                            ISNULL(ep.value, 'No comment') as column_comment,
                            CASE WHEN tc.CONSTRAINT_TYPE = 'PRIMARY KEY' THEN 'PRI'
                                 WHEN tc.CONSTRAINT_TYPE = 'UNIQUE' THEN 'UNI'
                                 ELSE ''
                            END as column_key,
                            '' as extra,
                            c.CHARACTER_MAXIMUM_LENGTH as max_length,
                            c.NUMERIC_PRECISION as numeric_precision,
                            c.NUMERIC_SCALE as numeric_scale
                        FROM INFORMATION_SCHEMA.COLUMNS c
                        LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu 
                            ON kcu.TABLE_NAME = c.TABLE_NAME AND kcu.COLUMN_NAME = c.COLUMN_NAME
                        LEFT JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc 
                            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                        LEFT JOIN sys.columns sc ON sc.name = c.COLUMN_NAME
                        LEFT JOIN sys.tables st ON st.name = c.TABLE_NAME AND st.object_id = sc.object_id
                        LEFT JOIN sys.extended_properties ep ON ep.major_id = st.object_id AND ep.minor_id = sc.column_id
                        WHERE c.TABLE_NAME = ?
                        ORDER BY c.ORDINAL_POSITION
                    """, (table_name,))
                    
                    columns_info = [column[0] for column in cursor.description]
                    table['columns'] = []
                    for row in cursor.fetchall():
                        table['columns'].append(dict(zip(columns_info, row)))
                    
                    # Simplified index information for SQL Server
                    table['indexes'] = []
                    
                    tables.append(table)
                
                cursor.close()
                logger.info(f"Retrieved SQL Server information for {len(tables)} tables")
                return tables
                
        except pyodbc.Error as e:
            logger.error(f"Error getting SQL Server table descriptions: {e}")
            raise


class DatabaseManager:
    """Universal database manager class for handling multiple database types"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        if not self.config.validate():
            raise ValueError("Invalid database configuration")
        
        # Create appropriate connector based on database type
        self.connector = self._create_connector()
    
    def _create_connector(self) -> DatabaseConnector:
        """Create appropriate database connector"""
        connectors = {
            'mysql': MySQLConnector,
            'postgresql': PostgreSQLConnector,
            'sqlite': SQLiteConnector,
            'sqlserver': SQLServerConnector
        }
        
        connector_class = connectors.get(self.config.db_type)
        if not connector_class:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")
        
        return connector_class(self.config)

    
    def get_connection(self):
        """Get database connection through connector"""
        return self.connector.get_connection()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        return self.connector.test_connection()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query through connector"""
        return self.connector.execute_query(query, params)
    
    def execute_write_operation(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Execute write operation through connector"""
        return self.connector.execute_write_operation(query, params)
    
    def execute_batch_write_operation(self, query: str, params_list: List[tuple]) -> Dict[str, Any]:
        """
        Execute a batch write operation (INSERT/UPDATE) with multiple parameter sets
        Note: This method is currently only implemented for MySQL-like databases
        """
        if not params_list:
            return {"success": True, "affected_rows": 0, "message": "No data to insert"}

        # For now, we'll implement this as multiple single operations
        # In the future, this could be optimized per database type
        total_affected = 0
        try:
            for params in params_list:
                result = self.execute_write_operation(query, params)
                total_affected += result.get("affected_rows", 0)
            
            return {
                "success": True,
                "affected_rows": total_affected,
                "message": f"Batch operation completed successfully"
            }
        except Exception as e:
            logger.error(f"Batch write operation execution error: {e}")
            return {
                "success": False,
                "affected_rows": 0,
                "message": f"Batch operation failed: {str(e)}"
            }
    
    def get_table_descriptions(self) -> List[Dict[str, Any]]:
        """Get table descriptions through connector"""
        return self.connector.get_table_descriptions()



# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager
