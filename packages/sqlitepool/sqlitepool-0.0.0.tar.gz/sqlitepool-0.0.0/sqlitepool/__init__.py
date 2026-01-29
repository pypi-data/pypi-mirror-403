# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Anggit Arfanto

import sqlite3

from .executors import MultiThreadExecutor

__version__ = '0.0.0'
__all__ = ['ConnectionPool']


class ConnectionPool(MultiThreadExecutor):
    def __init__(self, database, size=5, **kwargs):
        super().__init__(size=size)

        self.database = database
        self.kwargs = kwargs

    def connect(self):
        conn = sqlite3.connect(self.database, **self.kwargs)
        conn.row_factory = sqlite3.Row

        return conn

    async def start(self, loop=None, **kwargs):
        await super().start(prefix='ConnectionPool', loop=loop, **kwargs)

        for thread in self.threads:
            if 'connect' not in thread.__dict__:
                thread.connect = thread.submit(self.connect)

    async def shutdown(self):
        self.size = 0

        while self.threads:
            thread = self.threads.pop()

            if 'connect' in thread.__dict__:
                conn = await thread.connect

                if thread.is_alive():
                    await thread.submit(conn.close)

            await thread.shutdown()

    def prepare(self, query):
        return DatabaseStatement(self.thread, query)


class DatabaseStatement:
    def __init__(self, thread, query):
        self.thread = thread
        self.query = query
        self.cursor = None
        self.rows = []

    async def fetch(self):
        try:
            return self.rows.pop(0)
        except IndexError:
            if self.cursor:
                return await self.thread.submit(self.cursor.fetchone)

    async def execute(self, parameters=()):
        conn = None

        try:
            conn = await self.thread.connect
            self.cursor = await self.thread.submit(conn.execute, self.query,
                                                   parameters)

            if self.cursor.description:
                # SELECT
                row = await self.thread.submit(self.cursor.fetchone)

                if row:
                    self.rows.append(row)
                    return True

                return False

            # INSERT, UPDATE, etc.
            await self.thread.submit(conn.commit)

            # Read-only attribute that provides the number of modified rows
            # for INSERT, UPDATE, DELETE, and REPLACE statements;
            # is -1 for other statements, including CTE queries.
            return self.cursor.rowcount != 0
        except sqlite3.DatabaseError as exc:
            print('execute:', str(exc))

            if conn is not None:
                await self.thread.submit(conn.close)

            del self.thread.__dict__['connect']
            await self.thread.context.start()
        except RuntimeError:
            self.thread.context.threads.remove(self.thread)
            await self.thread.context.start()
            raise
