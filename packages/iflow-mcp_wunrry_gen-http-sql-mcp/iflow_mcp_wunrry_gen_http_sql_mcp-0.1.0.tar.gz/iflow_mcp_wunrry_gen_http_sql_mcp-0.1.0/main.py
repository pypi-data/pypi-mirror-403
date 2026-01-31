"""
Universal SQL MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with multiple SQL databases.
This server offers secure access to database schema information and query execution for various database engines.

Supported Databases:
- MySQL
- PostgreSQL
- SQLite
- SQL Server

Features:
- Get comprehensive database schema information (tables, columns, indexes)
- Execute SELECT queries safely
- Execute write operations (INSERT/UPDATE) with proper security controls
- Test database connectivity
- Environment-based configuration

Usage:
    python main.py

Environment Variables:
    DB_TYPE: Database type (mysql, postgresql, sqlite, sqlserver)
    DB_HOST: Database host (default: localhost, not needed for SQLite)
    DB_PORT: Database port (default varies by DB type, not needed for SQLite)
    DB_USER: Database username (not needed for SQLite)
    DB_PASSWORD: Database password (not needed for SQLite)
    DB_NAME: Database name or file path (for SQLite)
    DB_DRIVER: Database driver (for SQL Server, optional)
"""


import logging
import sys
import os
from tools import mcp

# Configure logging level from environment variable
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the MCP server"""
    try:
        logger.info("Starting Universal SQL MCP Server...")

        # Test database connection on startup
        from database import get_db_manager
        db_manager = get_db_manager()

        if not db_manager.test_connection():
            logger.error("Failed to connect to database. Please check your configuration.")
            sys.exit(1)

        logger.info(f"Successfully connected to {db_manager.config.db_type.upper()} database: {db_manager.config.database}")
        logger.info("Universal SQL MCP Server is ready to serve requests")


        # Run the MCP server
        # 从环境变量读取 transport 值，默认为 'stdio'
        transport = os.getenv("MCP_TRANSPORT", "stdio")
        if transport == "stdio":
            mcp.run(transport="stdio")
        else:
            mcp.run(transport=transport, host="0.0.0.0", port=8000)

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()