#! python3.10

import datetime
import uvicorn
from fastapi import FastAPI, Depends
from itertools import groupby
from operator import itemgetter

import order_planning_server.auth.schemas as schemas
import order_planning_server.db.db_conn as db
import order_planning_server.db.crud as crud

app = FastAPI(title="Order planning server")


@app.get("/indices", response_model = schemas.IndicesResponse)
async def get_indices(cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns indices with values averaged across all factories. This
    provides a summary view of order fulfilment status. Since the
    planned indices update only after a change in demand distribution,
    the indices also reflect the stability of the demand distribution.

    The indices are:
    - planned fulfilment time
    - planned unutilized capacity
    - realised fulfilment time
    - realised unutilized capacity
    - date on which fulfilment time and unutilized capacity were planned
    """
    db_records = await crud.get_indices_db(cursor)
    result = dict()

    if len(db_records) > 0:
        for row in db_records:
            indices = schemas.Indices(
                planned_fulfilment_time= row.get("planned_fulfilment_time"),
                planned_unutilized_capacity= row.get("planned_unutilized_capacity"),
                plan_generation_date= row.get("record_date"),
                realised_fulfilment_time= row.get("daily_order_fulfilment_time"),
                realised_unutilized_capacity= row.get("unutilized_capacity")
            )
        
        result = schemas.IndicesResponse(
            data = indices
        )

    return result


# @app.get("/indices/{index}", response_model = schemas.IndexResponse)
# async def get_index(index: schemas.IndexRequest, cursor: db.Cursor = Depends(db.get_cursor)):
#     """
#     Returns value of the index and last updated date for index in indices:
#     - planned fulfilment time
#     - planned unutilized capacity
#     - realised fulfilment time
#     - realised unutilized capacity
#     """
#     return


@app.get("/factories", response_model = schemas.FactoriesResponse)
async def get_factories(date: datetime.date, cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns indices of all factories since specified date. The indices are:
    - planned fulfilment time
    - planned unutilized capacity
    - realised fulfilment time
    - realised unutilized capacity
    """
    db_records = await crud.get_factories(cursor, date)
    result = dict()

    if len(db_records) > 0:
        factory_list = []
        sorted_rows = sorted(db_records, key=itemgetter('factory_id'))

        for key, factories in groupby(sorted_rows, key=itemgetter('factory_id')):
            factories = list(factories)
            factory_list.append(schemas.Factory(
                factory_id= key,
                factory_name= factories[0].get("factory_name"),
                dates= [d['record_date'] for d in factories if 'record_date' in d],
                planned_fulfilment_times= [d['planned_fulfilment_time'] for d in factories if 'planned_fulfilment_time' in d],
                planned_unutilized_capacities= [d['planned_unutilized_capacity'] for d in factories if 'planned_unutilized_capacity' in d],
                realised_fulfilment_time= [d['daily_order_fulfilment_time'] for d in factories if 'daily_order_fulfilment_time' in d],
                realised_unutilized_capacity= [d['unutilized_capacity'] for d in factories if 'unutilized_capacity' in d]
            ))

        result= schemas.FactoriesResponse(
            data = factory_list
        )

    return result


@app.get("/factories/{factory_id}", response_model = schemas.FactoryResponse)
async def get_factory(factory_id: int, date: datetime.date, cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns indices of factory with specified factory_id since the
    specified date. The indices are:
    - planned fulfilment time
    - planned unutilized capacity
    - realised fulfilment time
    - realised unutilized capacity
    """
    db_records = await crud.get_factories(cursor, date, factory_id)
    result = dict()

    if len(db_records) > 0:
        factory = schemas.Factory(
            factory_id= db_records[0].get("factory_id"),
            factory_name= db_records[0].get("factory_name"),
            dates= [d['record_date'] for d in db_records if 'record_date' in d],
            planned_fulfilment_times= [d['planned_fulfilment_time'] for d in db_records if 'planned_fulfilment_time' in d],
            planned_unutilized_capacities= [d['planned_unutilized_capacity'] for d in db_records if 'planned_unutilized_capacity' in d],
            realised_fulfilment_time= [d['daily_order_fulfilment_time'] for d in db_records if 'daily_order_fulfilment_time' in d],
            realised_unutilized_capacity= [d['unutilized_capacity'] for d in db_records if 'unutilized_capacity' in d]
        )  

        result= schemas.FactoryResponse(
            data = factory
        )

    return result


@app.get("/customer_groups", response_model = schemas.CustomerGroupsResponse)
async def get_customer_groups(date: datetime.date, cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns demand distribution for all customer groups since specified
    date. Demand distribution of customer group is represented by their
    product orders.
    """
    db_records = await crud.get_customer_groups(cursor, date)
    result = dict()

    if len(db_records) > 0:
        customer_groups = []
        sorted_rows = sorted(db_records, key=itemgetter('customer_site_group_id'))

        for key, sites in groupby(sorted_rows, key=itemgetter('customer_site_group_id')):
            sites = list(sites)

            product_list = []
            sorted_products = sorted(sites, key=itemgetter('product_id'))

            for k, products in groupby(sorted_products, key=itemgetter('product_id')):
                products = list(products)
                product_list.append(schemas.Product(
                    product_id= products[0].get("product_id"),
                    product_name= products[0].get("product_name"),
                    order_dates= [d['order_date'] for d in products if 'order_date' in d],
                    quantities= [d['quantity'] for d in products if 'quantity' in d]
                ))
            
            customer_groups.append(schemas.CustomerGroup(
                customer_group_id= sites[0].get("customer_site_group_id"),
                latitude= sites[0].get("latitude"),
                longitude= sites[0].get("longitude"),
                products= product_list
            ))

        result= schemas.CustomerGroupsResponse(
            data = customer_groups
        )

    return result


@app.get("/customer_groups/{customer_group_id}", response_model = schemas.CustomerGroupResponse)
async def get_customer_group(customer_group_id: int, date: datetime.date, cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns demand distribution for specified customer group since specified
    date. Demand distribution of customer group is represented by their
    product orders.
    """
    db_records = await crud.get_customer_groups(cursor, date, customer_group_id)
    result = dict()

    if len(db_records) > 0:
        product_list = []
        sorted_products = sorted(db_records, key=itemgetter('product_id'))

        for k, products in groupby(sorted_products, key=itemgetter('product_id')):
            products = list(products)
            product_list.append(schemas.Product(
                product_id= products[0].get("product_id"),
                product_name= products[0].get("product_name"),
                order_dates= [d['order_date'] for d in products if 'order_date' in d],
                quantities= [d['quantity'] for d in products if 'quantity' in d]
            ))
            
        customer_group = schemas.CustomerGroup(
            customer_group_id= db_records[0].get("customer_site_group_id"),
            latitude= db_records[0].get("latitude"),
            longitude= db_records[0].get("longitude"),
            products= product_list
        )

        result= schemas.CustomerGroupResponse(
            data = customer_group
        )

    return result


"""
@app.get("/allocations")
async def get_allocations() -> schemas.AllocationsResponse:
    return
"""


@app.get("/allocations/{plan_id}", response_model = schemas.AllocationsResponse)
async def get_allocation(plan_id: int, cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns allocation ratios for given plan_id.
    """
    db_records = await crud.get_allocation_by_planid(cursor, plan_id)
    result = dict()

    if len(db_records) > 0:
        allocations = []
        for row in db_records:
            allocations.append(schemas.Allocation(
                factory_id= row.get("factory_id"),
                customer_site_group_id= row.get("customer_site_group_id"),
                min_allocation_ratio= row.get("min_allocation_ratio"),
                max_allocation_ratio= row.get("max_allocation_ratio")
            ))

        allocationResponse = schemas.Allocations(
            plan_id= db_records[0].get("plan_id"),
            allocations= allocations
        )

        result= schemas.AllocationsResponse(
            data = allocationResponse
        )
        
    return result


@app.get("/plans", response_model = schemas.PlansResponse)
async def get_plans(cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns list of plans, each containing plan_id.
    """
    db_records = await crud.get_plans(cursor)
    result = dict()

    if len(db_records) > 0:
        plans = []
        for row in db_records:
            plans.append(schemas.Plan(
                plan_id= row.get("plan_id"),
                planned_fulfilment_time= row.get("planned_fulfilment_time"),
                planned_unutilized_capacity= row.get("planned_unutilized_capacity"),
                plan_generation_date= row.get("plan_generation_date"),
                selected= row.get("selected"),
                autoselected= row.get("autoselected"),
                selection_date= row.get("selection_date")
            ))

        result= schemas.PlansResponse(
            data= plans
        )

    return result


@app.get("/plans/{plan_id}", response_model = schemas.PlanResponse)
async def get_plan(plan_id: int, cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns a plan, comprising: average planned fulfilment time,
    average planned unutilized capacity, plan generation date,
    whether the plan was selected, either by the user or auto-selected,
    and the date of selection.
    """
    db_records = await crud.get_plans(cursor, plan_id)
    result = dict()

    if len(db_records) > 0:
        plan = schemas.Plan(
            plan_id= db_records[0].get("plan_id"),
            planned_fulfilment_time= db_records[0].get("planned_fulfilment_time"),
            planned_unutilized_capacity= db_records[0].get("planned_unutilized_capacity"),
            plan_generation_date= db_records[0].get("plan_generation_date"),
            selected= db_records[0].get("selected"),
            autoselected= db_records[0].get("autoselected"),
            selection_date= db_records[0].get("selection_date")
        )

        result= schemas.PlanResponse(
            data= plan
        )

    return result


# optimization
@app.post("/plan", response_model = schemas.PlansResponse)
async def plan(problem_parameters: schemas.ProblemParametersRequest, cursor: db.Cursor = Depends(db.get_cursor)):  # body: max prod capacity, prod time, order qtymean + std
    """
    Executes multi-objective optimization with given problem parameters.

    - minimize: order fulfilment time and unutilized production capacity
    - decision variables: allocation of orders to factories, min production
    quantities to start production
    - problem parameters: demand distribution for each customer group,
    max production capacity available for each factory, production time
    for each factory, transportation time between factories and customer
    groups

    """
    return


@app.post("/select", response_model = schemas.PlanResponse)
async def select(plan_req: schemas.PlanRequest, cursor: db.Cursor = Depends(db.get_cursor)):

    db_records = await crud.select_plan(cursor, plan_req)
    result = dict()

    # if len(db_records) > 0:
    #     for row in db_records:
    #         plan = schemas.Plan(
    #             plan_id= row.plan_id,
    #             planned_fulfilment_time= row.planned_fulfilment_time,
    #             planned_unutilized_capacity= row.planned_unutilized_capacity,
    #             plan_generation_date= row.plan_generation_date,
    #             selected= row.selected,
    #             autoselected= row.autoselected,
    #             selection_date= row.selection_date
    #         )

    #     result= schemas.PlanResponse(
    #         data= plan
    #     )

    return result


if __name__ == "__main__":
    uvicorn.run("order_planning_server.main:app", host="0.0.0.0", port=8000)
