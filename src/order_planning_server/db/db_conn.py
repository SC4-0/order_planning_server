from aioodbc import connect
from aioodbc.cursor import Cursor
from fastapi import HTTPException
from enum import Enum, auto
from asyncio import get_event_loop

loop = get_event_loop()


class Binary_Value(str, Enum):
    YES = "yes"
    NO = "no"


"""
SQL Server connection string syntax
- keywords are not case-sensitive, but values are
- keywords and values can contain whitespace characters
- keywords and unquoted values ignore leading and trailing whitespace 
"""


class SQL_Server_Connection_String:
    def __init__(
        self,
        database_driver: str,
        server: str,
        port: int,
        database: str,
        encrypt=Binary_Value.YES,
        trust_server_cert=Binary_Value.YES,
    ) -> None:
        self.database_driver = database_driver
        self.server = server
        self.port = port
        self.database = database
        self.encrypt = encrypt
        self.trust_server_cert = trust_server_cert
        self.uid = None
        self.pwd = None
        return

    def __repr__(self) -> str:
        if self.uid and self.pwd:
            conn_string = f"DRIVER={{{self.database_driver}}};SERVER={self.server},{self.port};DATABASE={self.database};ENCRYPT={self.encrypt};UID={self.uid};PWD={self.pwd};TrustServerCertificate={self.trust_server_cert}"
            return conn_string
        else:
            raise HTTPException(
                status_code=502,
                detail="No username and password set; database connection cannot be made.",
            )

    def set_uid_and_pwd(self, uid: str, pwd: str) -> None:
        self.uid = uid
        self.pwd = pwd
        return


async def get_cursor() -> Cursor:
    conn_string_obj = SQL_Server_Connection_String(
        "ODBC Driver 18 for SQL Server",
        "host.docker.internal",
        1433,
        "order_planning",
    )
    conn_string_obj.set_uid_and_pwd()
    conn_string = str(conn_string_obj)
    conn = await connect(dsn=conn_string, loop=loop)
    cursor = await conn.cursor()
    return cursor


async def get_indices_db(cursor: Cursor):
    query = "SELECT planned_fulfilment_time, planned_unutilized_capacity, daily_order_fulfilment_time, unutilized_capacity, record_date FROM order_planning..plans INNER JOIN (SELECT AVG(CAST(daily_order_fulfilment_time AS FLOAT)) AS daily_order_fulfilment_time, AVG(CAST(unutilized_capacity AS FLOAT)) AS unutilized_capacity, (SELECT MAX(record_date) FROM order_planning..factory_metrics) AS record_date FROM order_planning..factory_metrics WHERE record_date=(SELECT MAX(record_date) FROM order_planning..factory_metrics)) AS FM ON plans.plan_generation_date=fm.record_date;"
    await cursor.execute(query)
    records = await cursor.fetchall()
    return records
