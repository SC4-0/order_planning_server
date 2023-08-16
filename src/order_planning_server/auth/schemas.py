import datetime
from pydantic import BaseModel
from enum import Enum


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
class IndicesResponse(BaseModel):
    planned_fulfilment_time: int
    planned_unutilized_capacity: int
    plan_generation_date: datetime.date
    realised_fulfilment_time: int  # avg(select)
    realised_unutilized_capacity: int  # avg(select)


class IndexResponse(BaseModel):
    value: str | None
    date: str | None


class FactoryResponse(BaseModel):
    factory_id: int
    factory_name: str
    dates: list[datetime.date]
    planned_fulfilment_times: list[int]
    planned_unutilized_capacities: list[int]
    realised_fulfilment_time: list[int]
    realised_unutilized_capacity: list[int]


class FactoriesResponse(BaseModel):
    factories: list[FactoryResponse]


class Product(BaseModel):
    product_id: int
    product_name: str
    dates: list[datetime.date]
    orders: list[int]


class CustomerGroupResponse(BaseModel):
    customer_group_id: int
    latitude: float
    longitude: float
    products: Product


class CustomerGroupsResponse(BaseModel):
    customer_groups: list[CustomerGroupResponse]


class Allocation(BaseModel):
    factory_id: int
    customer_site_group_id: int
    min_allocation_ratio: float
    max_allocation_ratio: float


class AllocationsResponse(BaseModel):
    plan_id: int
    allocations: list[Allocation]


class PlanResponse(BaseModel):
    plan_id: int
    planned_fulfilment_time: int
    planned_unutilized_capacity: int
    plan_generation_date: datetime.date
    selected: int
    autoselected: int
    selection_date: datetime.date | None


class PlansResponse(BaseModel):
    plans: list[PlanResponse]
