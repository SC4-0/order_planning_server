from aioodbc.cursor import Cursor
from order_planning_server.auth import schemas
import datetime

async def convert_to_dict(cursor: Cursor):
    rows = await cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    result = [dict(zip(column_names, row)) for row in rows]
    return result


async def get_indices_db(cursor: Cursor):
    # query = "SELECT planned_fulfilment_time, planned_unutilized_capacity, daily_order_fulfilment_time, unutilized_capacity, record_date FROM order_planning..plans INNER JOIN (SELECT AVG(CAST(daily_order_fulfilment_time AS FLOAT)) AS daily_order_fulfilment_time, AVG(CAST(unutilized_capacity AS FLOAT)) AS unutilized_capacity, (SELECT MAX(record_date) FROM order_planning..factory_metrics) AS record_date FROM order_planning..factory_metrics WHERE record_date=(SELECT MAX(record_date) FROM order_planning..factory_metrics)) AS FM ON plans.plan_generation_date=fm.record_date;"
   
    query = """
    SELECT planned_fulfilment_time, planned_unutilized_capacity, daily_order_fulfilment_time, unutilized_capacity, record_date 
    FROM [plans] INNER JOIN 
    (SELECT AVG(CAST(daily_order_fulfilment_time AS FLOAT)) AS daily_order_fulfilment_time, 
    AVG(CAST(unutilized_capacity AS FLOAT)) AS unutilized_capacity, 
    MAX(record_date) AS record_date 
    FROM [factory_metrics] 
    WHERE record_date=(SELECT MAX(record_date) FROM [factory_metrics])) AS FM 
    ON plans.plan_generation_date = fm.record_date"""
    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result


async def get_factories(cursor: Cursor, date: datetime.date, factory_id: int = None, skip: int = 0, limit: int = 100):
    query = f"""
    SELECT f.factory_id, f.factory_name, fm.record_date, fm.daily_order_fulfilment_time, fm.unutilized_capacity,
    pf.planned_fulfilment_time, pf.planned_unutilized_capacity
    FROM factories f, factory_metrics fm, planned_factory_targets pf
    WHERE f.factory_id = fm.factory_id 
    AND f.factory_id = pf.factory_id
    AND fm.record_date = pf.planned_date 
    AND pf.planned_date >= '{date}'"""
    if factory_id != None:
        query += f" AND f.factory_id = {factory_id}"
    
    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result


async def get_customer_groups(cursor: Cursor, date: datetime.date, customer_group_id: int = None, skip: int = 0, limit: int = 100):
    query = f"""
    SELECT csg.customer_site_group_id, csg.latitude, csg.longitude, o.order_date, oi.quantity, p.product_id, p.product_name 
    FROM customer_site_groups csg, customers c, orders o, order_items oi, products p 
    WHERE csg.customer_site_group_id = c.customer_site_group_id 
    AND c.customer_id = o.customer_id 
    AND o.order_id = oi.order_id 
    AND oi.item_id = p.product_id 
    AND o.order_date >= '{date}'"""
    if customer_group_id != None:
        query += f" AND csg.customer_site_group_id = {customer_group_id}"
    
    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result


async def get_allocation_by_planid(cursor: Cursor, plan_id: int, skip: int = 0, limit: int = 100):
    query = f"""
    SELECT plan_id, factory_id, customer_site_group_id, min_allocation_ratio, max_allocation_ratio 
    FROM planned_allocations 
    WHERE plan_id = {plan_id}"""

    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result


async def get_plans(cursor: Cursor, plan_id: int = None, skip: int = 0, limit: int = 100):
    query = """
    SELECT plan_id, planned_fulfilment_time, planned_unutilized_capacity, plan_generation_date, selected, autoselected, selection_date 
    FROM plans"""
    if plan_id != None:
        query += f" WHERE plan_id = {plan_id}"
    
    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result


async def select_plan(cursor: Cursor, plan_req: schemas.PlanRequest, skip: int = 0, limit: int = 100):
    query = f"""UPDATE plans SET selected = 1, selection_date = GETDATE() WHERE plan_id = {plan_id}"""

    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result
