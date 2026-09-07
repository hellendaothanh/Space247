from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RentalType(str, Enum):
    ROOM = "room"
    SERVICED_APARTMENT = "serviced_apartment"
    HOUSE_SHARE = "house_share"
    ENTIRE_HOUSE = "entire_house"


class RentalCostSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    electricity_per_kwh: int | None = Field(None, ge=0, strict=True)
    electricity_billing: Literal["state_rate", "fixed"] | None = None
    water_cost: int | None = Field(None, ge=0, strict=True)
    water_unit: Literal["per_m3", "per_person"] | None = None
    parking_fee_monthly: int | None = Field(None, ge=0, strict=True)
    service_fee_monthly: int | None = Field(None, ge=0, strict=True)
    deposit_months: int | None = Field(None, ge=0, strict=True)


class RentalRuleSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allow_pets: bool | None = None
    curfew: bool | None = None
    private_bathroom: bool | None = None
    has_mezzanine: bool | None = None
    has_washing_machine: bool | None = None
    live_with_owner: bool | None = None
    has_elevator: bool | None = None
    fingerprint_lock: bool | None = None
    curfew_time: str | None = Field(None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    max_occupants: int | None = Field(None, ge=1, strict=True)

    @model_validator(mode="after")
    def validate_curfew_time(self):
        if self.curfew is False and self.curfew_time is not None:
            raise ValueError("curfew_time requires curfew=true")
        return self


class RentalFilters(BaseModel):
    rental_type: RentalType | None = None
    allow_pets: bool | None = None
    curfew: bool | None = None
    private_bathroom: bool | None = None
    has_mezzanine: bool | None = None
    has_washing_machine: bool | None = None
    live_with_owner: bool | None = None
    has_elevator: bool | None = None
    fingerprint_lock: bool | None = None
    electricity_billing: Literal["state_rate", "fixed"] | None = None
    max_deposit: float | None = Field(None, ge=0, allow_inf_nan=False)
    near_landmark: str | None = None
    radius_km: float = Field(3.0, gt=0, le=100)


RentalCosts = RentalCostSchema
RentalRules = RentalRuleSchema
