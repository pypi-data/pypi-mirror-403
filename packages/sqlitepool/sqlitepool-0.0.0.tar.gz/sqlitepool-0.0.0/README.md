# SQLitePool
A thread-pooled [sqlite3](https://docs.python.org/3/library/sqlite3.html) for asyncio.

## Behavior
- `stmt.execute()` return `bool` instead of a cursor object:
- `True` if the query succeeds, or `False` otherwise
- Empty results on `INSERT`, `UPDATE`, `DELETE`, and `SELECT` are considered as `False`

## Usage
```python
import asyncio

from sqlitepool import ConnectionPool


async def main():
    pool = ConnectionPool('example.db', size=5)
    await pool.start()

    try:
        stmt = pool.prepare(
            'CREATE TABLE IF NOT EXISTS users ('
            '  id INTEGER PRIMARY KEY,'
            '  name TEXT NOT NULL,'
            '  age INTEGER NOT NULL'
            ');'
        )
        await stmt.execute()

        stmt = pool.prepare('INSERT INTO users (name, age) VALUES (?, ?)')
        await stmt.execute(['Alice', 30])

        stmt = pool.prepare('SELECT * FROM users LIMIT 10')
        await stmt.execute()
        row = await stmt.fetch()

        while row:
            print('*', row['name'], row['age'])
            row = await stmt.fetch()
    finally:
        await pool.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
```

## Install
```
python3 -m pip install --upgrade sqlitepool
```

## License
MIT License
