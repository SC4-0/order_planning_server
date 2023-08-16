import datetime
from pydantic import BaseModel
from enum import Enum
from typing import Optional


# request models
class IndexRequest(str, Enum):
    planned_fulfilment_time = "planned_fulfilment_time"
    planned_unutilised_capacity = "planned_unutilised_capacity"
    realised_fulfilment_time = "realised_fulfilment_time"
    realised_unutilised_capacity = "realised_unutilised_capacity"


class ProblemParametersRequest(BaseModel):
    order_mean: float
    order_std: float
    max_prod_capacity: int
    prod_rates: list[tuple[int, int]]


class PlanRequest(BaseModel):
    plan_id: int


# response models
class Indices(BaseModel):
    planned_fulfilment_time: int
    planned_unutilized_capacity: int
    plan_generation_date: datetime.date
    realised_fulfilment_time: int  # avg(select)
    realised_unutilized_capacity: int  # avg(select)

# return only one column and date of indices
class IndexResponse(BaseModel):
    value: str | None
    date: str | None


class IndicesResponse(BaseModel):
    data: Optional[Indices]


# using Single Factore - no need to use AVG() - using planned_factory_targets & factory_metrics - can use similar qurey of indices
class Factory(BaseModel):
    factory_id: int
    factory_name: str
    dates: list[datetime.date]
    planned_fulfilment_times: list[int]
    planned_unutilized_capacities: list[int]
    realised_fulfilment_time: list[int]
    realised_unutilized_capacity: list[int]


class FactoryResponse(BaseModel):
    data: Optional[Factory]


class FactoriesResponse(BaseModel):
    data: Optional[list[Factory]]


class Product(BaseModel):
    product_id: int
    product_name: str
    order_dates: list[datetime.date] #order-date
    quantities: list[int] #quantity


# need to join customer_site_gp & customers & ordres & order_items & products
class CustomerGroup(BaseModel):
    customer_group_id: int
    latitude: float
    longitude: float
    products: list[Product]


class CustomerGroupResponse(BaseModel):
    data: Optional[CustomerGroup]


class CustomerGroupsResponse(BaseModel):
    data: Optional[list[CustomerGroup]]


class Allocation(BaseModel):
    factory_id: int
    customer_site_group_id: int
    min_allocation_ratio: float
    max_allocation_ratio: float


class Allocations(BaseModel):
    plan_id: int
    allocations: list[Allocation]


class AllocationsResponse(BaseModel):
    data: Optional[Allocations]


class Plan(BaseModel):
    plan_id: int
    planned_fulfilment_time: int
    planned_unutilized_capacity: int
    plan_generation_date: datetime.date
    selected: int
    autoselected: int
    selection_date: datetime.date | None


class PlanResponse(BaseModel):
    data: Optional[Plan]


class PlansResponse(BaseModel):
    data: Optional[list[Plan]]
