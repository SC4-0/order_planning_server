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

    query1 = """
    select * from plans where selection_date = (select max(selection_date) from plans);
    """
    await cursor.execute(query1)
    result1 = await convert_to_dict(cursor)

    query2 = """
    select avg(daily_order_fulfilment_time) as daily_order_fulfilment_time, avg(unutilized_capacity) as unutilized_capacity,
    max(record_date) as record_date from factory_metrics where record_date = (select max(record_date) from factory_metrics);
    """
    await cursor.execute(query2)
    result2 = await convert_to_dict(cursor)

    result1[0].update(result2[0])
    await cursor.close()

    return result1


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
        SELECT pft.factory_id, p.selection_date, pft.planned_fulfilment_time, pft.planned_unutilized_capacity, pft.factory_id, pft.factory_name
        FROM plans AS p JOIN (SELECT pt.factory_id, f.factory_name,pt.plan_id, pt.planned_fulfilment_time, pt.planned_unutilized_capacity, pt.planned_date,
		pt.min_prod_hours from planned_factory_targets pt JOIN factories f ON pt.factory_id = f.factory_id) AS pft ON p.plan_id = pft.plan_id
        WHERE ((p.selected = 1) AND (pft.factory_id = '{factory_id}') AND (CAST(p.selection_date AS DATE) >= CAST('{after}' AS DATE))
        AND (CAST(p.selection_date AS DATE) <= CAST('{before}' AS DATE))) ORDER BY pft.factory_id, p.plan_generation_date;
        """

        query_measured = f"""
        SELECT f.factory_name, fm.factory_id, fm.record_date, fm.daily_order_fulfilment_time, fm.unutilized_capacity FROM factory_metrics AS fm JOIN factories AS f ON f.factory_id = fm.factory_id
        WHERE ((CAST(fm.record_date AS DATE) <= CAST('{before}' AS DATE)) AND (CAST(fm.record_date AS DATE) >= CAST('{after}' AS DATE)) AND (fm.factory_id = '{factory_id}'))
        ORDER BY fm.factory_id, fm.record_date;
        """
    else:
        query_planned = f"""
        SELECT pft.factory_id, p.selection_date, pft.planned_fulfilment_time, pft.planned_unutilized_capacity, pft.factory_id, pft.factory_name
        FROM plans AS p JOIN (SELECT pt.factory_id, f.factory_name,pt.plan_id, pt.planned_fulfilment_time, pt.planned_unutilized_capacity, pt.planned_date,
		pt.min_prod_hours from planned_factory_targets pt JOIN factories f ON pt.factory_id = f.factory_id) AS pft ON p.plan_id = pft.plan_id
         WHERE ((p.selected = 1) AND (CAST(p.selection_date AS DATE) >= CAST('{after}' AS DATE))
        AND (CAST(p.selection_date AS DATE) <= CAST('{before}' AS DATE))) ORDER BY pft.factory_id, p.plan_generation_date;
        """

        query_planned_2 = f"""
        SELECT factory_id, planned_fulfilment_time, planned_unutilized_capacity, factory_id FROM planned_factory_targets WHERE
        plan_id = (SELECT plan_id FROM plans WHERE selected = 1 AND selection_date = (SELECT MAX(selection_date) FROM plans
        WHERE selection_date <= CAST('{before}' AS DATE)));"""

        query_measured = f"""
        SELECT f.factory_name, fm.factory_id, fm.record_date, fm.daily_order_fulfilment_time, fm.unutilized_capacity FROM factory_metrics AS fm JOIN factories AS f ON f.factory_id = fm.factory_id
        WHERE ((CAST(fm.record_date AS DATE) <= CAST('{before}' AS DATE)) AND (CAST(fm.record_date AS DATE) >= CAST('{after}' AS DATE)))
        ORDER BY fm.factory_id, fm.record_date;
        """

    await cursor.execute(query_planned)
    res_planned = await convert_to_dict(cursor)

    await cursor.execute(query_measured)
    res_measured = await convert_to_dict(cursor)

    await cursor.execute(query_planned_2)
    res_planned_2 = await convert_to_dict(cursor)
    await cursor.close()

    return (res_planned, res_measured, res_planned_2)


async def get_orders_db(cursor: Cursor, after: datetime.date, before: datetime.date):
    query = f"""
    SELECT o.order_id, o.customer_id, o.customer_site_group_id, o.customer_site_group_name, o.order_date, o.assigned_factory_id, o.factory_name, oi.item_id, oi.quantity, oi.product_name FROM
    (SELECT order_id, orders.customer_id, order_date, assigned_factory_id, customer_site_groups.customer_site_group_id, customer_site_group_name, factory_name FROM orders
    INNER JOIN customers ON orders.customer_id = customers.customer_id INNER JOIN customer_site_groups ON customer_site_groups.customer_site_group_id = customers.customer_site_group_id
	INNER JOIN factories ON orders.assigned_factory_id = factories.factory_id) AS o
    INNER JOIN (SELECT order_items.order_id, order_items.item_id, order_items.quantity, products.product_name FROM order_items
	INNER JOIN products ON order_items.item_id = products.product_id) AS oi ON o.order_id = oi.order_id
	WHERE cast(order_date as date) >= '{after}' AND cast(order_date as date) <= '{before}';
    """
    await cursor.execute(query)
    result = await convert_to_dict(cursor)
    return result


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
    AND cast(o.order_date as date) >= '{after}'
    AND cast(o.order_date as date) <= '{before}'
    """
    if customer_group_id != None:
        query += f" AND csg.customer_site_group_id = {customer_group_id}"

    query += " ORDER BY o.order_date ASC"

    await cursor.execute(query)
    result = await convert_to_dict(cursor)
    if len(result) == 0:
        query = "SELECT * FROM customer_site_groups"
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


async def get_current_allocation(cursor: Cursor):
    query = f"""
    SELECT * FROM planned_allocations WHERE plan_id = 
    (SELECT plan_id FROM plans WHERE selection_date = (SELECT MAX(selection_date) FROM plans))
    ORDER BY factory_id, customer_site_group_id;
    """
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
    INSERT INTO plans OUTPUT INSERTED.* VALUES {plans_str};
    """
    await cursor.execute(query1)
    result = await cursor.fetchall()
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

    """
    message = [
        {
            "planned_fulfilment_time": 0,
            "planned_unutilized_capacity": 0,
            "plan_generation_date": "2023-07-21T02:21:57.767Z",
            "selected": 1,
            "autoselected": 1,
            "selection_date": "2023-07-21T02:21:57.767Z",
            "factory_id": 1,
            "customer_site_group_id": 1,
            "min_allocation_ratio": 0,
            "max_allocation_ratio": 0.5,
            "min_prod_hours": 4,
        },
        {
            "planned_fulfilment_time": 1,
            "planned_unutilized_capacity": 1,
            "plan_generation_date": "2023-09-21T02:21:57.767Z",
            "selected": 1,
            "autoselected": 1,
            "selection_date": "2023-09-21T02:21:57.767Z",
            "factory_id": 1,
            "customer_site_group_id": 1,
            "min_allocation_ratio": 1,
            "max_allocation_ratio": 2.5,
            "min_prod_hours": 3,
        },
    ]

    """
    return plan_ids


async def select_plan_db(
    cursor: Cursor, plan_req: schemas.PlanRequest, skip: int = 0, limit: int = 100
):
    query = f"""UPDATE plans SET selected = 1, selection_date = GETDATE() WHERE plan_id = {plan_req.plan_id};"""

    await cursor.execute(query)
    await cursor.commit()

    query2 = f"""SELECT factory_id, customer_site_group_id, min_allocation_ratio, max_allocation_ratio FROM planned_allocations WHERE plan_id = {plan_req.plan_id};"""
    await cursor.execute(query2)
    result = await convert_to_dict(cursor)
    await cursor.close()
    for row in result:
        row["min_allocation_ratio"] = float(row["min_allocation_ratio"])
        row["max_allocation_ratio"] = float(row["max_allocation_ratio"])

    return result
