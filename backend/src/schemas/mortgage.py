from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CalculationMethod(str, Enum):
    DECLINING_BALANCE = "declining_balance"  # Dư nợ giảm dần
    FIXED_PAYMENT = "fixed_payment"          # Trả đều / Niên kim cố định


class MortgageCalcRequest(BaseModel):
    property_price: float = Field(
        ...,
        ge=0,
        description="Property price in VND (e.g. 5,000,000,000)",
    )
    down_payment_percent: float = Field(
        default=30.0,
        ge=0.0,
        le=100.0,
        description="Down payment percentage (0% to 100%)",
    )
    down_payment_amount: float | None = Field(
        default=None,
        ge=0.0,
        description="Optional fixed down payment amount in VND (overrides percent if provided)",
    )
    loan_term_years: int = Field(
        default=20,
        description="Loan term in years (must be between 1 and 35)",
    )
    annual_interest_rate: float = Field(
        default=7.5,
        ge=0.0,
        le=50.0,
        description="Initial/preferential annual interest rate in percent (e.g. 7.5 for 7.5%)",
    )
    preferential_period_months: int = Field(
        default=12,
        ge=0,
        description="Duration of preferential rate in months (default 12)",
    )
    post_preferential_rate: float | None = Field(
        default=10.5,
        ge=0.0,
        le=50.0,
        description="Annual floating interest rate after preferential period in percent (e.g. 10.5)",
    )
    calculation_method: CalculationMethod | str = Field(
        default=CalculationMethod.DECLINING_BALANCE,
        description="Calculation method: 'declining_balance' or 'fixed_payment'",
    )

    @field_validator("loan_term_years")
    @classmethod
    def validate_loan_term(cls, v: int) -> int:
        if v < 1 or v > 35:
            raise ValueError("loan_term_years must be between 1 and 35")
        return v

    @field_validator("calculation_method")
    @classmethod
    def validate_method(cls, v: CalculationMethod | str) -> str:
        if isinstance(v, CalculationMethod):
            return v.value
        val = str(v).lower().strip()
        valid = {m.value for m in CalculationMethod}
        if val not in valid:
            raise ValueError(f"Invalid calculation_method '{v}'. Allowed: {valid}")
        return val


class AmortizationScheduleItem(BaseModel):
    month: int = Field(..., description="Month number (1 to N)")
    principal_payment: float = Field(..., description="Monthly principal payment in VND")
    interest_payment: float = Field(..., description="Monthly interest payment in VND")
    total_payment: float = Field(..., description="Total payment for the month in VND")
    remaining_balance: float = Field(..., description="Remaining loan balance at end of month in VND")
    interest_rate: float = Field(..., description="Annual interest rate applied for this month (%)")


class MortgageCalcResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    property_price: float
    down_payment_amount: float
    down_payment_percent: float
    loan_amount: float
    loan_term_years: int
    loan_term_months: int
    calculation_method: str
    monthly_payment_first_month: float
    monthly_payment_max: float
    monthly_payment_min: float
    total_interest: float
    total_payment: float
    schedule: list[AmortizationScheduleItem] = Field(default_factory=list)
