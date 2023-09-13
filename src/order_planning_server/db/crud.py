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
    await cursor.close()

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
        SELECT pft.factory_id, p.plan_generation_date, pft.planned_fulfilment_time, pft.planned_unutilized_capacity, pft.factory_id, pft.factory_name
        FROM plans AS p JOIN (SELECT pt.factory_id, f.factory_name,pt.plan_id, pt.planned_fulfilment_time, pt.planned_unutilized_capacity, pt.planned_date,
		pt.min_prod_hours from planned_factory_targets pt JOIN factories f ON pt.factory_id = f.factory_id) AS pft ON p.plan_id = pft.plan_id
        WHERE ((p.selected = 1) AND (pft.factory_id = '{factory_id}') AND (CAST(p.plan_generation_date AS DATE) >= CAST('{after}' AS DATE))
        AND (CAST(p.plan_generation_date AS DATE) <= CAST('{before}' AS DATE))) ORDER BY pft.factory_id, p.plan_generation_date;
        """

        query_measured = f"""
        SELECT fm.factory_id, fm.record_date, fm.daily_order_fulfilment_time, fm.unutilized_capacity FROM factory_metrics AS fm
        WHERE fm.factory_id = '{factory_id}' ORDER BY fm.factory_id, fm.record_date;
        """
    else:
        query_planned = f"""
        SELECT pft.factory_id, p.plan_generation_date, pft.planned_fulfilment_time, pft.planned_unutilized_capacity, pft.factory_id, pft.factory_name
        FROM plans AS p JOIN (SELECT pt.factory_id, f.factory_name,pt.plan_id, pt.planned_fulfilment_time, pt.planned_unutilized_capacity, pt.planned_date,
		pt.min_prod_hours from planned_factory_targets pt JOIN factories f ON pt.factory_id = f.factory_id) AS pft ON p.plan_id = pft.plan_id
         WHERE ((p.selected = 1) AND (CAST(p.plan_generation_date AS DATE) >= CAST('{after}' AS DATE))
        AND (CAST(p.plan_generation_date AS DATE) <= CAST('{before}' AS DATE))) ORDER BY pft.factory_id, p.plan_generation_date;
        """

        query_measured = f"""
        SELECT fm.factory_id, fm.record_date, fm.daily_order_fulfilment_time, fm.unutilized_capacity FROM factory_metrics AS fm
        ORDER BY fm.factory_id, fm.record_date;
        """

    await cursor.execute(query_planned)
    res_planned = await convert_to_dict(cursor)

    await cursor.execute(query_measured)
    res_measured = await convert_to_dict(cursor)
    await cursor.close()

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
    SELECT csg.customer_site_group_id, csg.customer_site_group_name, csg.latitude, csg.longitude, o.order_date, oi.quantity, p.product_id, p.product_name 
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
    await cursor.close()

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
    await cursor.close()

    return result


async def get_allocation_by_planids(
    cursor: Cursor, plan_ids: list[int], skip: int = 0, limit: int = 100
):
    query = f"""
    SELECT plan_id, factory_id, customer_site_group_id, min_allocation_ratio, max_allocation_ratio 
    FROM planned_allocations 
    WHERE plan_id IN ({",".join([str(i) for i in plan_ids])})"""

    await cursor.execute(query)
    result = await convert_to_dict(cursor)
    await cursor.close()

    return result


async def get_plans_db(
    cursor: Cursor, plan_id: int = None, skip: int = 0, limit: int = 100
):
    query = """
    SELECT plan_id, plan_category, planned_fulfilment_time, planned_unutilized_capacity, plan_generation_date, selected, autoselected, selection_date, plan_category 
    FROM plans"""
    if plan_id != None:
        query += f" WHERE plan_id = {plan_id}"

    await cursor.execute(query)
    result = await convert_to_dict(cursor)
    await cursor.close()

    return result


async def get_plans_from_plan_ids_db(cursor: Cursor, plan_ids: list[int]):
    query = f"""
    SELECT plan_id, plan_category, planned_fulfilment_time, planned_unutilized_capacity, plan_generation_date, selected, autoselected, selection_date, plan_category 
    FROM plans WHERE plan_id IN ({','.join([str(i) for i in plan_ids])})"""
    print(plan_ids)
    print(query)

    await cursor.execute(query)
    result = await convert_to_dict(cursor)
    await cursor.close()

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
    await cursor.close()

    return (res_1, res_2)


async def get_factory_targets_db(cursor: Cursor, plan_id: list[int]):
    if len(plan_id) == 0:
        return
    if len(plan_id) == 1:
        plan_id_str = str(plan_id[0])
    else:
        plan_id_str = ",".join([str(i) for i in plan_id])

    print(plan_id_str)
    query = f"""
    SELECT factory_id, plan_id, planned_fulfilment_time, planned_unutilized_capacity, planned_date, min_prod_hours
    FROM planned_factory_targets WHERE plan_id IN ({plan_id_str}) ORDER BY plan_id;
    """
    print(query)

    await cursor.execute(query)
    result = await convert_to_dict(cursor)
    await cursor.close()

    return result


async def insert_plans_db(
    cursor: Cursor, plans_str: list[str], planned_factory_targets, planned_allocations
):
    plans_str = ",".join(plans_str)
    query1 = f"""
    INSERT INTO plans OUTPUT INSERTED.plan_id VALUES {plans_str};
    """
    await cursor.execute(query1)
    result = await cursor.fetchall()  # plan_ids
    plan_ids = [i[0] for i in result]

    planned_factory_targets_full = []
    planned_factory_targets_plan_ids = plan_ids * 3
    for idx in range(len(planned_factory_targets_plan_ids)):
        planned_factory_targets_full.append(
            [
                planned_factory_targets[idx][0],
                planned_factory_targets_plan_ids[idx],
                *planned_factory_targets[idx][1:],
            ]
        )
    planned_factory_targets_str = []
    for pft in planned_factory_targets_full:
        planned_factory_targets_str.append(
            "({}, {}, {:.3f}, {:.3f}, '{}', {})".format(*pft)
        )
    planned_factory_targets_str = ",".join(planned_factory_targets_str)

    planned_allocations_full = []
    planned_allocations_plan_ids = plan_ids * 9
    for idx in range(len(planned_allocations_plan_ids)):
        planned_allocations_full.append(
            [planned_allocations_plan_ids[idx], *planned_allocations[idx]]
        )
    planned_allocations_str = []
    for pa in planned_allocations_full:
        planned_allocations_str.append("({},{},{},{:.9f},{:.9f})".format(*pa))
    planned_allocations_str = ",".join(planned_allocations_str)
    query2 = f"""
    INSERT INTO planned_factory_targets VALUES {planned_factory_targets_str};
    INSERT INTO planned_allocations VALUES {planned_allocations_str};
    """
    await cursor.execute(query2)
    await cursor.commit()
    await cursor.close()

    return plan_ids


async def select_plan_db(
    cursor: Cursor, plan_req: schemas.PlanRequest, skip: int = 0, limit: int = 100
):
    query = f"""UPDATE plans SET selected = 1, selection_date = GETDATE() WHERE plan_id = {plan_req.plan_id}"""

    await cursor.execute(query)
    await cursor.commit()
    await cursor.close()

    return {}
