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


class FactoryAddressParameter(BaseModel):
    factory_id: int
    factory_lat: float
    factory_lon: float


class ProductionParameter(BaseModel):
    product_id: int
    production_rate: float


class FactoryProductionParameter(BaseModel):
    factory_id: int
    max_production_hrs: float
    production_rate: list[ProductionParameter]


class ProductDemandParameter(BaseModel):
    product_id: int
    order_mean: float
    order_std: float


class DemandParameter(BaseModel):
    customer_site_group_id: int
    customer_demand: list[ProductDemandParameter]


class ProblemParametersRequest(BaseModel):
    factory_parameters: list[FactoryProductionParameter]
    demand_parameters: list[DemandParameter]


class PlanRequest(BaseModel):
    plan_id: int


# response models
class Indices(BaseModel):
    planned_fulfilment_time: int
    planned_unutilized_capacity: int
    plan_generation_date: datetime.date
    realised_fulfilment_time: int
    realised_unutilized_capacity: float


# return only one column and date of indices
class IndexResponse(BaseModel):
    value: str | None
    date: str | None


class IndicesResponse(BaseModel):
    data: Optional[Indices]


class Factory(BaseModel):
    factory_id: int
    factory_name: str
    planned_datetimes: list[datetime.datetime]
    planned_unutilized_capacity: list[float]
    planned_fulfilment_time: list[int]
    realised_dates: list[datetime.date]
    realised_unutilized_capacity: list[float]
    realised_fulfilment_time: list[int]
    # str, str for planned fulfilment time, unutilized capacity


class FactoryResponse(BaseModel):
    data: Optional[Factory]


class FactoriesResponse(BaseModel):
    data: Optional[list[Factory]]


class Product(BaseModel):
    product_id: int
    product_name: str
    order_dates: list[datetime.date]  # order-date
    quantities: list[int]  # quantity


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
