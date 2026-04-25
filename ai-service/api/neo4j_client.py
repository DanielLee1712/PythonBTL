import os
from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

class Neo4jClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jClient, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not hasattr(self, 'driver'):
            self.driver = None

    def connect(self):
        if self.driver is None:
            uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
            user = os.environ.get("NEO4J_USER", "neo4j")
            password = os.environ.get("NEO4J_PASSWORD", "password")
            try:
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                logger.info("Connected to Neo4j successfully.")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None

    def execute_read(self, query, parameters=None):
        self.connect()
        try:
            with self.driver.session() as session:
                result = session.execute_read(lambda tx: tx.run(query, parameters).data())
                return result
        except Exception as e:
            logger.error(f"Failed to execute read query: {e}")
            return []

    def execute_write(self, query, parameters=None):
        self.connect()
        try:
            with self.driver.session() as session:
                result = session.execute_write(lambda tx: tx.run(query, parameters).data())
                return result
        except Exception as e:
            logger.error(f"Failed to execute write query: {e}")
            return []

    def execute_write_many(self, query, rows):
        self.connect()
        try:
            with self.driver.session() as session:
                result = session.execute_write(lambda tx: tx.run(query, {"rows": rows}).consume())
                return result
        except Exception as e:
            logger.error(f"Failed to execute batch write query: {e}")
            return None

neo4j_client = Neo4jClient()
