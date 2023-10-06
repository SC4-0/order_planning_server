#! python3.10

import datetime
import uvicorn
import numpy as np
import aio_pika
from fastapi import FastAPI, Depends, Query
from itertools import groupby
from operator import itemgetter, attrgetter
from collections import defaultdict
from fastapi.middleware.cors import CORSMiddleware

from planning.orderPlanner import plan as plan_optimize
import order_planning_server.auth.schemas as schemas
import order_planning_server.db.db_conn as db
import order_planning_server.db.crud as crud
import order_planning_server.rabbit.publisher as publisher

app = FastAPI(title="Order planning server")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/indices", response_model=schemas.IndicesResponse)
async def get_indices(cursor: db.Cursor = Depends(db.get_cursor)):
    # untested due to lack of simultaneous factory metrics and planned targets data
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
                planned_fulfilment_time=row.get("planned_fulfilment_time"),
                planned_unutilized_capacity=row.get("planned_unutilized_capacity"),
                plan_generation_date=row.get("record_date"),
                realised_fulfilment_time=row.get("daily_order_fulfilment_time"),
                realised_unutilized_capacity=row.get("unutilized_capacity"),
            )

        result = schemas.IndicesResponse(data=indices)

    # TODO add error if more than 1 row

    # test = schemas.Indices(
    #             planned_fulfilment_time=1,
    #             planned_unutilized_capacity=1,
    #             plan_generation_date=1,
    #             realised_fulfilment_time=1,
    #             realised_unutilized_capacity=1,
    #         )
    # result = schemas.IndicesResponse(data=test)
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


@app.get("/factory_metrics", response_model=schemas.FactoriesResponse)
async def get_factory_metrics(
    after: datetime.date,
    before: datetime.date,
    cursor: db.Cursor = Depends(db.get_cursor),
):
    # Returns both planned factory targets and realised factory metrics.
    # untested due to db_records_planned being empty
    """
    Returns indices of all factories within the after and before date range, inclusive.
    The indices are:
    - planned fulfilment time
    - planned unutilized capacity
    - realised fulfilment time
    - realised unutilized capacity
    """
    db_records_planned, db_records_realised = await crud.get_factory_metrics_db(
        cursor, after, before
    )

    if (len(db_records_planned) > 0) and (len(db_records_realised) > 0):
        factory_dict = dict()
        factory_list = []
        sorted_rows_planned = sorted(db_records_planned, key=itemgetter("factory_id"))
        sorted_rows_realised = sorted(db_records_realised, key=itemgetter("factory_id"))
        for factory_id, factory_info in groupby(
            sorted_rows_planned, key=itemgetter("factory_id")
        ):
            factory_info = list(factory_info)
            factory_dict[factory_id] = dict()
            factory_dict[factory_id]["factory_name"] = factory_info[0]["factory_name"]
            factory_dict[factory_id]["planned_datetimes"] = [
                l["selection_date"] for l in factory_info if "selection_date" in l
            ]
            factory_dict[factory_id]["planned_unutilized_capacity"] = [
                l["planned_unutilized_capacity"]
                for l in factory_info
                if "planned_unutilized_capacity" in l
            ]
            factory_dict[factory_id]["planned_fulfilment_time"] = [
                l["planned_fulfilment_time"]
                for l in factory_info
                if "planned_fulfilment_time" in l
            ]
        for factory_id, factory_info in groupby(
            sorted_rows_realised, key=itemgetter("factory_id")
        ):
            factory_info = list(factory_info)
            factory_dict[factory_id]["realised_dates"] = [
                l["record_date"] for l in factory_info if "record_date" in l
            ]
            factory_dict[factory_id]["realised_unutilized_capacity"] = [
                l["unutilized_capacity"]
                for l in factory_info
                if "unutilized_capacity" in l
            ]
            factory_dict[factory_id]["realised_fulfilment_time"] = [
                l["daily_order_fulfilment_time"]
                for l in factory_info
                if "daily_order_fulfilment_time" in l
            ]

        for factory in factory_dict:
            factory_list.append(
                schemas.Factory(
                    factory_id=factory,
                    factory_name=factory_dict[factory]["factory_name"],
                    planned_datetimes=factory_dict[factory]["planned_datetimes"],
                    planned_unutilized_capacity=factory_dict[factory][
                        "planned_unutilized_capacity"
                    ],
                    planned_fulfilment_time=factory_dict[factory][
                        "planned_fulfilment_time"
                    ],
                    realised_dates=factory_dict[factory]["realised_dates"],
                    realised_unutilized_capacity=factory_dict[factory][
                        "realised_unutilized_capacity"
                    ],
                    realised_fulfilment_time=factory_dict[factory][
                        "realised_fulfilment_time"
                    ],
                )
            )

        result = schemas.FactoriesResponse(data=factory_list)
        return result

    return dict()


@app.get("/factory_metrics/{factory_id}", response_model=schemas.FactoryResponse)
async def get_factory(
    factory_id: int,
    after: datetime.date,
    before: datetime.date,
    cursor: db.Cursor = Depends(db.get_cursor),
):
    # untested due to lack of simultaneous factory metrics and planned targets data
    """
    Returns indices of factory with specified factory_id within the before and after
    date range, inclusive. The indices are:
    - planned fulfilment time
    - planned unutilized capacity
    - realised fulfilment time
    - realised unutilized capacity
    """
    db_records_planned, db_records_realised = await crud.get_factory_metrics_db(
        cursor, after, before, factory_id
    )

    if (len(db_records_planned) > 0) and (len(db_records_realised) > 0):
        factory = schemas.Factory(
            factory_id=db_records_planned[0].get("factory_id"),
            factory_name=db_records_planned[0].get("factory_name"),
            planned_datetimes=[d["selection_date"] for d in db_records_planned],
            planned_unutilized_capacity=[
                d["planned_unutilized_capacity"] for d in db_records_planned
            ],
            planned_fulfilment_time=[
                d["planned_fulfilment_time"] for d in db_records_planned
            ],
            realised_dates=[d["record_date"] for d in db_records_realised],
            realised_unutilized_capacity=[
                d["unutilized_capacity"] for d in db_records_realised
            ],
            realised_fulfilment_time=[
                d["daily_order_fulfilment_time"] for d in db_records_realised
            ],
        )
        result = schemas.FactoryResponse(data=factory)
        return result

    return dict()


@app.get("/customer_groups_data", response_model=schemas.CustomerGroupsResponse)
async def get_customer_groups_data(
    after: datetime.date,
    before: datetime.date,
    cursor: db.Cursor = Depends(db.get_cursor),
):
    """
    Returns demand distribution for all customer groups within before and after
    date ranges, inclusive. Demand distribution of customer group is represented
    by their product orders.
    """
    db_records = await crud.get_customer_groups_data_db(cursor, after, before)
    result = dict()

    if len(db_records) > 0:
        customer_groups = []
        sorted_rows = sorted(db_records, key=itemgetter("customer_site_group_id"))

        for key, sites in groupby(
            sorted_rows, key=itemgetter("customer_site_group_id")
        ):
            sites = list(sites)

            product_list = []
            sorted_products = sorted(sites, key=itemgetter("product_id"))

            for k, products in groupby(sorted_products, key=itemgetter("product_id")):
                products = list(products)
                product_list.append(
                    schemas.Product(
                        product_id=products[0].get("product_id"),
                        product_name=products[0].get("product_name"),
                        order_dates=[
                            d["order_date"] for d in products if "order_date" in d
                        ],
                        quantities=[d["quantity"] for d in products if "quantity" in d],
                    )
                )

            customer_groups.append(
                schemas.CustomerGroup(
                    customer_group_id=sites[0].get("customer_site_group_id"),
                    customer_group_name=sites[0].get("customer_site_group_name"),
                    latitude=sites[0].get("latitude"),
                    longitude=sites[0].get("longitude"),
                    products=product_list,
                )
            )

        result = schemas.CustomerGroupsResponse(data=customer_groups)

    return result


@app.get(
    "/customer_groups_data/{customer_group_id}",
    response_model=schemas.CustomerGroupResponse,
)
async def get_customer_group_data(
    customer_group_id: int,
    after: datetime.date,
    before: datetime.date,
    cursor: db.Cursor = Depends(db.get_cursor),
):
    """
    Returns demand distribution for specified customer group within before
    and after date ranges. Demand distribution of customer group is
    represented by their
    product orders.
    """
    db_records = await crud.get_customer_groups_data_db(
        cursor, after, before, customer_group_id
    )
    result = dict()

    if len(db_records) > 0:
        product_list = []
        sorted_products = sorted(db_records, key=itemgetter("product_id"))

        for k, products in groupby(sorted_products, key=itemgetter("product_id")):
            products = list(products)
            product_list.append(
                schemas.Product(
                    product_id=products[0].get("product_id"),
                    product_name=products[0].get("product_name"),
                    order_dates=[
                        d["order_date"] for d in products if "order_date" in d
                    ],
                    quantities=[d["quantity"] for d in products if "quantity" in d],
                )
            )

        customer_group = schemas.CustomerGroup(
            customer_group_id=db_records[0].get("customer_site_group_id"),
            customer_group_name=db_records[0].get("customer_site_group_name"),
            latitude=db_records[0].get("latitude"),
            longitude=db_records[0].get("longitude"),
            products=product_list,
        )

        result = schemas.CustomerGroupResponse(data=customer_group)

    return result


@app.get("/allocations", response_model=schemas.MultipleAllocationsResponse)
async def get_allocation(
    plan_id: list[int] = Query(...), cursor: db.Cursor = Depends(db.get_cursor)
):
    """
    Returns allocation ratios for given plan_id.
    """
    db_records = await crud.get_allocation_by_planids(cursor, plan_id)
    result = dict()

    if len(db_records) > 0:
        plans = defaultdict(list)
        sorted_rows = sorted(db_records, key=itemgetter("plan_id"))
        for key, allocations in groupby(sorted_rows, key=itemgetter("plan_id")):
            allocations = list(allocations)
            for row in allocations:
                plans[key].append(
                    schemas.Allocation(
                        factory_id=row.get("factory_id"),
                        customer_site_group_id=row.get("customer_site_group_id"),
                        min_allocation_ratio=row.get("min_allocation_ratio"),
                        max_allocation_ratio=row.get("max_allocation_ratio"),
                    )
                )

        result = schemas.MultipleAllocationsResponse(
            data=[schemas.Allocations(plan_id=p, allocations=plans[p]) for p in plans]
        )

    return result


@app.get("/allocations/current", response_model=schemas.AllocationsResponse)
async def get_current_allocation(cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns allocation ratios for current plan_id, defined by plan_id with most
    recent selection_date.
    """
    db_records = await crud.get_current_allocation(cursor)
    result = dict()

    if len(db_records) > 0:
        allocations = []
        for row in db_records:
            allocations.append(
                schemas.Allocation(
                    factory_id=row.get("factory_id"),
                    customer_site_group_id=row.get("customer_site_group_id"),
                    min_allocation_ratio=row.get("min_allocation_ratio"),
                    max_allocation_ratio=row.get("max_allocation_ratio"),
                )
            )

        allocationResponse = schemas.Allocations(
            plan_id=db_records[0].get("plan_id"), allocations=allocations
        )

        result = schemas.AllocationsResponse(data=allocationResponse)

    return result


@app.get("/allocations/{plan_id}", response_model=schemas.AllocationsResponse)
async def get_allocation(plan_id: int, cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns allocation ratios for given plan_id.
    """
    db_records = await crud.get_allocation_by_planid(cursor, plan_id)
    result = dict()

    if len(db_records) > 0:
        allocations = []
        for row in db_records:
            allocations.append(
                schemas.Allocation(
                    factory_id=row.get("factory_id"),
                    customer_site_group_id=row.get("customer_site_group_id"),
                    min_allocation_ratio=row.get("min_allocation_ratio"),
                    max_allocation_ratio=row.get("max_allocation_ratio"),
                )
            )

        allocationResponse = schemas.Allocations(
            plan_id=db_records[0].get("plan_id"), allocations=allocations
        )

        result = schemas.AllocationsResponse(data=allocationResponse)

    return result


@app.get("/plans", response_model=schemas.PlansResponse)
async def get_plans_from_plan_ids(
    plan_id: list[int] = Query(...), cursor: db.Cursor = Depends(db.get_cursor)
):
    """
    Returns list of plans given plan_ids.
    """
    db_records = await crud.get_plans_from_plan_ids_db(cursor, plan_id)
    result = dict()

    if len(db_records) > 0:
        plans = []
        for row in db_records:
            plans.append(
                schemas.Plan(
                    plan_id=row.get("plan_id"),
                    plan_category=row.get("plan_category"),
                    planned_fulfilment_time=row.get("planned_fulfilment_time"),
                    planned_unutilized_capacity=row.get("planned_unutilized_capacity"),
                    plan_generation_date=row.get("plan_generation_date"),
                    selected=row.get("selected"),
                    autoselected=row.get("autoselected"),
                    selection_date=row.get("selection_date"),
                )
            )

        result = schemas.PlansResponse(data=plans)

    return result


@app.get("/plans/all", response_model=schemas.PlansResponse)
async def get_plans(cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns list of plans, each containing plan_id.
    """
    db_records = await crud.get_plans_db(cursor)
    result = dict()

    if len(db_records) > 0:
        plans = []
        for row in db_records:
            plans.append(
                schemas.Plan(
                    plan_id=row.get("plan_id"),
                    plan_category=row.get("plan_category"),
                    planned_fulfilment_time=row.get("planned_fulfilment_time"),
                    planned_unutilized_capacity=row.get("planned_unutilized_capacity"),
                    plan_generation_date=row.get("plan_generation_date"),
                    selected=row.get("selected"),
                    autoselected=row.get("autoselected"),
                    selection_date=row.get("selection_date"),
                )
            )

        result = schemas.PlansResponse(data=plans)

    return result


@app.get("/plans/{plan_id}")
async def get_plan(plan_id: int, cursor: db.Cursor = Depends(db.get_cursor)):
    """
    Returns a plan, comprising: average planned fulfilment time,
    average planned unutilized capacity, plan generation date,
    whether the plan was selected, either by the user or auto-selected,
    and the date of selection.
    """
    db_records = await crud.get_plans_db(cursor, plan_id)
    result = dict()

    if len(db_records) > 0:
        plan = schemas.Plan(
            plan_id=db_records[0].get("plan_id"),
            planned_fulfilment_time=db_records[0].get("planned_fulfilment_time"),
            planned_unutilized_capacity=db_records[0].get(
                "planned_unutilized_capacity"
            ),
            plan_generation_date=db_records[0].get("plan_generation_date"),
            selected=db_records[0].get("selected"),
            autoselected=db_records[0].get("autoselected"),
            selection_date=db_records[0].get("selection_date"),
        )

        result = schemas.PlanResponse(data=plan)

    return result


@app.post("/optimize", response_model=schemas.PlanIdsResponse)
async def optimize(
    factory_data1: list[schemas.FactoryData1],
    factory_data2: list[schemas.FactoryData2],
    customer_data: list[schemas.CustomerGroupData],
    cursor: db.Cursor = Depends(db.get_cursor),
):
    """
    Takes factory and customer data as input, stores planned solutions in database,
    and eturns generated plan ids.
    """
    nF, nC, nP, tLT = 3, 3, 2, np.array([[1, 2, 3], [2, 1, 2], [3, 2, 1]])
    maxHr = [
        f.production_hours for f in sorted(factory_data1, key=attrgetter("factory_id"))
    ]
    pRate = [
        [gg.production_rate for gg in list(g)]
        for k, g in groupby(
            sorted(factory_data2, key=attrgetter("product_id", "factory_id")),
            key=attrgetter("product_id"),
        )
    ]
    aveD = [
        [gg.mean_order_qty for gg in list(g)]
        for k, g in groupby(
            sorted(customer_data, key=attrgetter("product_id", "customer_group_id")),
            key=attrgetter("product_id"),
        )
    ]
    devD = [
        [gg.std_order_qty / gg.mean_order_qty for gg in list(g)]
        for k, g in groupby(
            sorted(customer_data, key=attrgetter("product_id", "customer_group_id")),
            key=attrgetter("product_id"),
        )
    ]
    param = {
        "nF": nF,
        "nC": nC,
        "nP": nP,
        "tLT": np.array(tLT),
        "maxHr": np.array(maxHr),
        "pRate": np.array(pRate),
        "aveD": np.array(aveD),
        "devD": np.array(devD),
    }
    (
        sol,
        sc_performance,
        factory_performance,
        unutilized_capacity_preference,
        plan_category,
    ) = plan_optimize(param)

    curr_datetime = str(datetime.datetime.now()).rsplit(".")[0]

    # planned_fulfilment_time, planned_unutilized_capacity, plan_generation_date,
    # plan_category, unutilized_capacity_preference, selected, autoselected, selection_date
    plans = []
    for row in zip(
        sc_performance[:, 0],
        sc_performance[:, 1],
        plan_category,
        unutilized_capacity_preference,
    ):
        plans.append([row[0], row[1], curr_datetime, row[2], row[3], 0, 0])

    plans_str = []
    for plan in plans:
        plans_str.append(
            "({:.3f}, {:.3f}, '{}', {}, {:.7f}, {}, {}, NULL)".format(*plan)
        )

    # factory_id, _, planned_fulfilment_time, planned_unutilized_capacity, planned_date, min_prod_hours
    planned_factory_targets = []  # missing second element, plan_id
    for row in zip(factory_performance[:, 0], factory_performance[:, 1], sol[:, -3]):
        planned_factory_targets.append([1, row[0], row[1], curr_datetime, row[2]])
    for row in zip(factory_performance[:, 2], factory_performance[:, 3], sol[:, -2]):
        planned_factory_targets.append([2, row[0], row[1], curr_datetime, row[2]])
    for row in zip(factory_performance[:, 4], factory_performance[:, 5], sol[:, -1]):
        planned_factory_targets.append([3, row[0], row[1], curr_datetime, row[2]])

    # _, factory_id, customer_site_group_id, min_allocation_ration, max_allocation_ratio
    planned_allocations = []

    for row in zip(sol[:, 0], sol[:, 1]):
        planned_allocations.append([1, 1, row[0], row[1]])
    for row in zip(sol[:, 2], sol[:, 3]):
        planned_allocations.append([2, 1, row[0], row[1]])
    for row in zip(sol[:, 4], sol[:, 5]):
        planned_allocations.append([3, 1, row[0], row[1]])
    for row in zip(sol[:, 6], sol[:, 7]):
        planned_allocations.append([1, 2, row[0], row[1]])
    for row in zip(sol[:, 8], sol[:, 9]):
        planned_allocations.append([2, 2, row[0], row[1]])
    for row in zip(sol[:, 10], sol[:, 11]):
        planned_allocations.append([3, 2, row[0], row[1]])
    for row in zip(sol[:, 12], sol[:, 13]):
        planned_allocations.append([1, 3, row[0], row[1]])
    for row in zip(sol[:, 14], sol[:, 15]):
        planned_allocations.append([2, 3, row[0], row[1]])
    for row in zip(sol[:, 16], sol[:, 17]):
        planned_allocations.append([3, 3, row[0], row[1]])

    db_records = await crud.insert_plans_db(
        cursor, plans_str, planned_factory_targets, planned_allocations
    )

    result = schemas.PlanIdsResponse(plan_ids=db_records)  # process db records

    """
    config = { 'host': 'localhost', 'port': 5672, 'exchange' : '' }
    rabbit = publisher.Publisher(config)
    for plan in db_records[1]:
        rabbit.publishMessage('order_allocation', plan)
    """

    return result


@app.get("/factory_parameters", response_model=schemas.FactoryParametersResponse)
async def get_factory_parameters(cursor: db.Cursor = Depends(db.get_cursor)):
    db_records = await crud.get_factory_parameters_db(cursor)
    result = dict()

    result = db_records
    if (len(db_records[0]) > 0) and (len(db_records[1]) > 0):
        result_information = []
        for row in db_records[0]:
            result_information.append(
                schemas.FactoryInformationParameter(
                    factory_id=row.get("factory_id"),
                    factory_name=row.get("factory_name"),
                    production_hours=row.get("production_hours"),
                    latitude=row.get("latitude"),
                    longitude=row.get("longitude"),
                )
            )

        result_production = []
        for row in db_records[1]:
            result_production.append(
                schemas.FactoryProductionParameter(
                    factory_id=row.get("factory_id"),
                    factory_name=row.get("factory_name"),
                    product_id=row.get("product_id"),
                    product_name=row.get("product_name"),
                    production_rate=row.get("production_rate"),
                )
            )

        result = schemas.FactoryParametersResponse(
            factory_information=result_information,
            factory_production_information=result_production,
        )

    return result


# get customer site groups demand distribution from /customer_groups_data


@app.post("/selected_plans")  # submit selected plan
async def post_selected_plan(
    plan_id: schemas.PlanRequest, cursor: db.Cursor = Depends(db.get_cursor)
):
    db_records = await crud.select_plan_db(cursor, plan_id)
    config = {"host": "localhost", "port": 5672, "exchange": ""}
    rabbit = publisher.Publisher(config)
    for planned_allocation in db_records:
        rabbit.publishMessage("order_allocation", planned_allocation)

    if len(db_records) != 0:
        return {"status": "success"}

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

    return {"status": "failed"}


# get allocation from /allocations


# @app.get("/factory_targets/{plan_id}", response_model=schemas.FactoryTargetsResponse)
@app.get("/factory_targets/")
async def get_factory_targets(
    plan_id: list[int] = Query(...),
    cursor: db.Cursor = Depends(db.get_cursor),
):
    """
    get planned factory targets for given plan_id for all factories
    """
    db_records = await crud.get_factory_targets_db(cursor, plan_id)
    result = dict()

    if len(db_records) > 0:
        # for each plan, each factory
        plans = defaultdict(list)
        sorted_rows = sorted(db_records, key=itemgetter("plan_id"))
        for key, factory_targets in groupby(sorted_rows, key=itemgetter("plan_id")):
            factory_targets = list(factory_targets)
            for factory_target in factory_targets:
                plans[key].append(
                    schemas.FactoryTarget(
                        factory_id=factory_target.get("factory_id"),
                        planned_fulfilment_time=factory_target.get(
                            "planned_fulfilment_time"
                        ),
                        planned_unutilized_capacity=factory_target.get(
                            "planned_unutilized_capacity"
                        ),
                        planned_date=factory_target.get("planned_date"),
                        min_prod_hours=factory_target.get("min_prod_hours"),
                    )
                )

        result = schemas.FactoryTargetResponse(
            data=[
                schemas.PlannedFactoryTargets(plan_id=p, factory_targets=plans[p])
                for p in plans
            ]
        )
    return result


# get overall planned metrics from /plans/{plan_id}

if __name__ == "__main__":
    uvicorn.run("order_planning_server.main:app", host="0.0.0.0", port=8000)
