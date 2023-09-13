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


class CustomerGroupData(BaseModel):
    customer_group_id: int
    product_id: int
    mean_order_qty: float
    std_order_qty: float


class FactoryData1(BaseModel):
    factory_id: int
    production_hours: int


class FactoryData2(BaseModel):
    factory_id: int
    product_id: int
    production_rate: float


class PlanRequest(BaseModel):
    plan_id: int


class PlansRequest(BaseModel):
    plan_ids: list[int]


# response models
class Indices(BaseModel):
    planned_fulfilment_time: float
    planned_unutilized_capacity: float
    plan_generation_date: datetime.date
    realised_fulfilment_time: float
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
    planned_fulfilment_time: list[float]
    realised_dates: list[datetime.date]
    realised_unutilized_capacity: list[float]
    realised_fulfilment_time: list[float]
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
    customer_group_name: str
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


class MultipleAllocationsResponse(BaseModel):
    data: list[Allocations]


class Plan(BaseModel):
    plan_id: int
    plan_category: int
    planned_fulfilment_time: float
    planned_unutilized_capacity: float
    plan_generation_date: datetime.date
    selected: int
    autoselected: int
    selection_date: datetime.date | None


class PlanResponse(BaseModel):
    data: Optional[Plan]


class PlansResponse(BaseModel):
    data: Optional[list[Plan]]


class PlanIdsResponse(BaseModel):
    plan_ids: list[int]


class FactoryInformationParameter(BaseModel):
    factory_id: int
    factory_name: str
    production_hours: int
    latitude: float
    longitude: float


class FactoryProductionParameter(BaseModel):
    factory_id: int
    factory_name: str
    product_id: int
    product_name: str
    production_rate: float


class FactoryParametersResponse(BaseModel):
    factory_information: list[FactoryInformationParameter]
    factory_production_information: list[FactoryProductionParameter]


class FactoryTarget(BaseModel):
    factory_id: int
    planned_fulfilment_time: float
    planned_unutilized_capacity: float
    planned_date: datetime.date
    min_prod_hours: float


class PlannedFactoryTargets(BaseModel):
    plan_id: int
    factory_targets: list[FactoryTarget]


class FactoryTargetResponse(BaseModel):
    data: list[PlannedFactoryTargets]
