
from vikas_pg.config import access_env
from typing import Union, List, Literal, Optional, Any, Dict 
import asyncpg
import os
import sys

from vikas_pg.crud import (build_select,
                  build_insert,
                  build_update)


class Accelerate:
    """
    Manages Postgresql connection pooling and query executing
    pooling methods will hold the minimum no of DB Connection as a Idle
    when the api is trigger it will take over the Idle connection from the Pooling Object.
    
    *.aquire:  will retrive only the Idle or Free or un-used Idel Connection from the Pooling
    *.release: It will used to release the connection like Disconnet, but it will Idle in the pooliing they did not disconnet.
    
    Asyncpg will responsible for the Connection between Server - client
    ayncpg will used for Asyncronus Operation to the Database. Handle multiple User Request presistant
    """

    #Initailizing connection pool object.
    Connection_Pooling: asyncpg.Pool | None = None 


    def __init__(self, minimum_Connection=10, Maximum_Connection=20, max_query=50000) -> None:
        """
        Init function None as a Default.
        """
        self._min_size = minimum_Connection
        self._max_size = Maximum_Connection
        self._max_queryies = max_query

        if not self.Connection_Pooling:
            '''DB connection is not initialized'''
            ...


    async def open_connection(self) -> None:
        """
            Database Connection Pool Configuration:

            - max_size = 5:
                The pool can hold up to 5 active database connections simultaneously.
                This limits how many users or processes can interact with the database concurrently.

            - max_queries = 10:
                Each connection can handle a maximum of 10 queries before being closed or recycled.
                If a user exceeds this limit, the pool automatically opens a new connection.

            Example Scenario:
                If a user sends 14 queries:
                - The pool will allocate 2 connections:
                    - First connection handles 10 queries.
                    - Second connection handles the remaining 4 queries.
                - This leaves 3 available connections for other users (5 - 2 = 3).

            This ensures optimal resource usage, allowing multiple users to interact efficiently while maintaining connection limits.
            

            @classmethods : 
                used for to share the resource to all the instance of the class.Thread, Inheritance safe.    
        """

        if not self.Connection_Pooling:
            #DataBase Connection Pool initializing.......Making Connection Pool
            get_key = await access_env()
            try:
                DataSourceName= f"postgresql://{get_key.db_user}:{get_key.db_pass.get_secret_value()}@{get_key.db_host}:{get_key.db_port}/{get_key.db_name}"                        
                self.Connection_Pooling = await asyncpg.create_pool(
                    dsn=DataSourceName,
                    min_size=self._min_size,
                    max_size=self._max_size,
                    max_queries=self._max_queryies
                )
            
                print("New connection Created.")
            except Exception as E:
               raise Exception(E)




    async def shutdown(self):
        """
        ** Release Method**

        The release method is used to release a connection when it is unused or when the database is closed. 
        Instead of terminating the connection, it releases the connection from the API and stores it as an idle connection,
        in the connection pool. When another API request is made, this connection is reused through the acquire method.
        """
        
        try:
            if self.Connection_Pooling:
                await self.Connection_Pooling.close()
                self.Connection_Pooling = None
            print("Released cache connetion pool.")

        except Exception as E:
            raise Exception(str(E))
        

    async def to_ensure_connection(self):
        """
        Docstring for to_ensure_connection
        
        :param self: global var.
        
        function will check the pool manager is visible or not before creating connection /
        pool manager will initiated on the `.create_pool` method. `to_connect` function /
        took the responsible for connection manager task.

        function method will raise the exception connection_manager is not initiated.
        """


        if not self.Connection_Pooling:
             raise Exception("database pool is not intialized!")


    #----------------------------CRUD--------------------------------------------#
    async def select(
                    self,
                    table: str, schema: str,
                    columns: List[str],
                    where: Dict[str, Any] | None = None,
                    fetch_one: bool = False,
                ):
        
        await self.to_ensure_connection()
        sql, values = build_select(table, schema, columns, where)

        async with self.Connection_Pooling.acquire() as conn:
            try:
                print("Acquire connection from cache.")
                if fetch_one:
                    return await conn.fetch(sql, *values)
                return await conn.fetch(sql, *values)
            except Exception as e:
                raise Exception(str(e))


    async def insert(self,
                    table: str, schema: str,
                    values: List[Dict[str, Any]],
                ) -> int:
        
        await self.to_ensure_connection()
        sql, args = build_insert(table, schema, values)

        async with self.Connection_Pooling.acquire() as conn:
            try:
                result = await conn.execute(sql, *args)
                return int(result.split()[-1])
            except Exception as e:
                raise Exception(str(e))


    async def update(self,
                    table: str, schema: str,
                    values: Dict[str, Any],
                    where: Dict[str, Any],
                ) -> int:
        
        await self.to_ensure_connection()
        sql, args = build_update(table, schema, values, where)

        async with self.Connection_Pooling.acquire() as conn:
            try:
                result = await conn.execute(sql, *args)
                return int(result.split()[-1])
            except Exception as e:
                raise Exception(str(e))




