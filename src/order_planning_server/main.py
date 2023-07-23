#! python3.10

import datetime
import order_planning_server.auth.schemas as schemas
import order_planning_server.db.db_conn as db
import uvicorn
from fastapi import FastAPI, Depends


app = FastAPI(title="Order planning server")


@app.get("/indices")
async def get_indices(
    cursor: db.Cursor = Depends(db.get_cursor),
    # ) -> schemas.IndicesResponse:
):
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
    result = await db.get_indices_db(cursor)
    # process to ensure result is consistent with schemas.IndicesResponse
    return


@app.get("/indices/{index}")
async def get_index(index: schemas.IndexRequest) -> schemas.IndexResponse:
    """
    Returns value of the index and last updated date for index in indices:
    - planned fulfilment time
    - planned unutilized capacity
    - realised fulfilment time
    - realised unutilized capacity
    """
    return


@app.get("/factories")
async def get_factories(date: datetime.date) -> schemas.FactoriesResponse:
    """
    Returns indices of all factories since specified date. The indices are:
    - planned fulfilment time
    - planned unutilized capacity
    - realised fulfilment time
    - realised unutilized capacity
    """
    return


@app.get("/factories/{factory_id}")
async def get_factory(factory_id: int, date: datetime.date) -> schemas.FactoryResponse:
    """
    Returns indices of factory with specified factory_id since the
    specified date. The indices are:
    - planned fulfilment time
    - planned unutilized capacity
    - realised fulfilment time
    - realised unutilized capacity
    """
    return


@app.get("/customer_groups")
async def get_customer_groups(date: datetime.date) -> schemas.CustomerGroupsResponse:
    """
    Returns demand distribution for all customer groups since specified
    date. Demand distribution of customer group is represented by their
    product orders.
    """
    return


@app.get("/customer_groups/{customer_group_id}")
async def get_customer_group(
    customer_group_id: int, date: datetime.date
) -> schemas.CustomerGroupResponse:
    """
    Returns demand distribution for specified customer group since specified
    date. Demand distribution of customer group is represented by their
    product orders.
    """
    return


"""
@app.get("/allocations")
async def get_allocations() -> schemas.AllocationsResponse:
    return
"""


@app.get("/allocations/{plan_id}")
async def get_allocation(plan_id: int) -> schemas.AllocationsResponse:
    """
    Returns allocation ratios for given plan_id.
    """
    return


@app.get("/plans")
async def get_plans() -> schemas.PlansResponse:
    """
    Returns list of plans, each containing plan_id.
    """
    return


@app.get("/plans/{plan_id}")
async def get_plan(plan_id: int) -> schemas.PlanResponse:
    """
    Returns a plan, comprising: average planned fulfilment time,
    average planned unutilized capacity, plan generation date,
    whether the plan was selected, either by the user or auto-selected,
    and the date of selection.
    """
    return


# optimization
@app.post("plan")
async def plan(
    problem_parameters: schemas.ProblemParametersRequest,
) -> schemas.PlansResponse:  # body: max prod capacity, prod time, order qtymean + std
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


@app.post("select")
async def select(plan_id: schemas.PlanRequest):
    return


if __name__ == "__main__":
    uvicorn.run("order_planning_server.main:app", host="0.0.0.0", port=8000)
