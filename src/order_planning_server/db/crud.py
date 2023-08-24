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
    ON CAST(plans.plan_generation_date AS DATE) = fm.record_date
    WHERE plans.selected = 1 AND plans.plan_generation_date = (SELECT MAX(plans.plan_generation_date) from plans);"""
    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result


async def get_factory_metrics_db(
    cursor: Cursor,
    after: datetime.date,
    before: datetime.date,
    factory_id: int = None,
    skip: int = 0,
    limit: int = 100,
):
    if factory_id != None:
        query_planned = f"""
        SELECT pft.factory_id, p.plan_generation_date, pft.planned_fulfilment_time, pft.planned_unutilized_capacity, pft.factory_id
        FROM plans AS p JOIN planned_factory_targets AS pft ON p.plan_id = pft.plan_id
        WHERE ((p.selected = 1) AND (pft.factory_id = '{factory_id}') AND (CAST(p.plan_generation_date AS DATE) >= CAST('{before}' AS DATE))
        AND (CAST(p.plan_generation_date AS DATE) <= CAST('{after}' AS DATE))) ORDER BY pft.factory_id, p.plan_generation_date;
        """

        query_measured = f"""
        SELECT fm.factory_id, fm.record_date, fm.daily_order_fulfilment_time, fm.unutilized_capacity FROM factory_metrics AS fm
        WHERE fm.factory_id = '{factory_id}' ORDER BY fm.factory_id, fm.record_date;
        """
    else:
        query_planned = f"""
        SELECT pft.factory_id, p.plan_generation_date, pft.planned_fulfilment_time, pft.planned_unutilized_capacity, pft.factory_id
        FROM plans AS p JOIN planned_factory_targets AS pft ON p.plan_id = pft.plan_id
        WHERE ((p.selected = 1) AND (CAST(p.plan_generation_date AS DATE) >= CAST('{before}' AS DATE))
        AND (CAST(p.plan_generation_date AS DATE) <= CAST('{after}' AS DATE))) ORDER BY pft.factory_id, p.plan_generation_date;
        """

        query_measured = f"""
        SELECT fm.factory_id, fm.record_date, fm.daily_order_fulfilment_time, fm.unutilized_capacity FROM factory_metrics AS fm
        ORDER BY fm.factory_id, fm.record_date;
        """

    await cursor.execute(query_planned)
    res_planned = await convert_to_dict(cursor)

    await cursor.execute(query_measured)
    res_measured = await convert_to_dict(cursor)

    return (res_planned, res_measured)


async def get_customer_groups_data_db(
    cursor: Cursor,
    after: datetime.date,
    before: datetime.date,
    customer_group_id: int = None,
    skip: int = 0,
    limit: int = 100,
):
    query = f"""
    SELECT csg.customer_site_group_id, csg.latitude, csg.longitude, o.order_date, oi.quantity, p.product_id, p.product_name 
    FROM customer_site_groups csg, customers c, orders o, order_items oi, products p 
    WHERE csg.customer_site_group_id = c.customer_site_group_id 
    AND c.customer_id = o.customer_id 
    AND o.order_id = oi.order_id 
    AND oi.item_id = p.product_id 
    AND o.order_date >= '{after}'
    AND o.order_date <= '{before}'
    """
    if customer_group_id != None:
        query += f" AND csg.customer_site_group_id = {customer_group_id}"

    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result


async def get_allocation_by_planid(
    cursor: Cursor, plan_id: int, skip: int = 0, limit: int = 100
):
    query = f"""
    SELECT plan_id, factory_id, customer_site_group_id, min_allocation_ratio, max_allocation_ratio 
    FROM planned_allocations 
    WHERE plan_id = {plan_id}"""

    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result


async def get_plans(
    cursor: Cursor, plan_id: int = None, skip: int = 0, limit: int = 100
):
    query = """
    SELECT plan_id, planned_fulfilment_time, planned_unutilized_capacity, plan_generation_date, selected, autoselected, selection_date, plan_category 
    FROM plans"""
    if plan_id != None:
        query += f" WHERE plan_id = {plan_id}"

    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result


async def get_factory_parameters_db(cursor: Cursor):
    query_1 = """
    SELECT factory_id, factory_name, production_hours, latitude, longitude from factories;
    """
    query_2 = """
    SELECT fp.factory_id, fp.product_id, f.factory_name, p.product_name, fp.production_rate from factories as f, factory_production as fp, products as p where f.factory_id = fp.factory_id and fp.product_id = p.product_id;
    """
    await cursor.execute(query_1)
    res_1 = await convert_to_dict(cursor)

    await cursor.execute(query_2)
    res_2 = await convert_to_dict(cursor)

    return (res_1, res_2)


async def select_plan_db(
    cursor: Cursor, plan_req: schemas.PlanRequest, skip: int = 0, limit: int = 100
):
    query = f"""UPDATE plans SET selected = 1, selection_date = GETDATE() WHERE plan_id = {plan_id}"""

    await cursor.execute(query)
    result = await convert_to_dict(cursor)

    return result
