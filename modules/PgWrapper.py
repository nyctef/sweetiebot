import psycopg2
import logging

log = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    pass

class PgWrapper(object):
    def __init__(self, pg_conn_str):
        self._pg_conn_str = pg_conn_str
        self._conn = psycopg2.connect(pg_conn_str)
    
    def query_one(self, query, vars=None):
        """returns a single value or None"""
        return self.__retry_on_fail(lambda: self.__query_one_inner(query, vars))
    
    def query_all(self, query, vars=None):
        """returns an array of values, possibly empty"""
        return self.__retry_on_fail(lambda: self.__query_all_inner(query, vars))
    
    def write(self, query, vars=None):
        """Executes query, then commits the transaction. Returns the count of affected rows"""
        return self.__retry_on_fail(lambda: self.__write_inner(query, vars))
        
    def __query_one_inner(self, query, vars=None):
        with self._conn.cursor() as cur:
            cur.execute(query, vars)
            result = cur.fetchone()
            return result[0] if result is not None else None

    def __query_all_inner(self, query, vars=None):
        with self._conn.cursor() as cur:
            cur.execute(query, vars)
            return cur.fetchall()
    
    def __write_inner(self, query, vars=None):
        with self._conn.cursor() as cur:
            cur.execute(query, vars)
            cur.connection.commit()
            return cur.rowcount
    
    def __retry_on_fail(self, action):
        try:
            return action()
        except psycopg2.errors.InFailedSqlTransaction as ifst:
            # if a previous action has failed then we need to roll back
            log.error("In failed transaction, rolling back")
            self._conn.rollback()
            # if this action fails then we'll raise the failure, and the next action will have to roll back
            return action()
        except psycopg2.InterfaceError as ie:
            log.warning("Connection to pg failed: attempting to reconnect")
            try:
                self._conn = psycopg2.connect(self._pg_conn_str)
                return action()
            except Exception as e:
                log.error("Reconnection to pg failed!")
                raise DatabaseConnectionError from e