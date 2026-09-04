import logging
from src.schemas.mortgage import (
    AmortizationScheduleItem,
    CalculationMethod,
    MortgageCalcRequest,
    MortgageCalcResponse,
)

logger = logging.getLogger(__name__)


class MortgageService:
    @staticmethod
    def calculate_mortgage(request: MortgageCalcRequest) -> MortgageCalcResponse:
        """
        Calculate mortgage amortization schedule supporting:
        - declining_balance (dư nợ giảm dần: gốc chia đều hàng tháng, lãi tính trên dư nợ còn lại)
        - fixed_payment (niên kim cố định / trả góp đều: tổng gốc + lãi cố định mỗi tháng theo chu kỳ lãi suất)
        - preferential interest rate period (e.g., first 12-24 months) and floating post-preferential rate.
        - Robust edge cases: 0% down payment (100% loan), 100% down payment (0 loan), 0% interest rate.
        """
        price = float(request.property_price)

        # 1. Determine down payment and principal loan amount
        if request.down_payment_amount is not None:
            down_payment = max(0.0, min(price, float(request.down_payment_amount)))
            down_payment_percent = (down_payment / price * 100.0) if price > 0 else 0.0
        else:
            down_payment_percent = max(0.0, min(100.0, float(request.down_payment_percent)))
            down_payment = price * (down_payment_percent / 100.0)

        loan_amount = max(0.0, price - down_payment)
        total_months = request.loan_term_years * 12
        pref_months = max(0, min(total_months, request.preferential_period_months))

        pref_rate = max(0.0, float(request.annual_interest_rate))
        post_rate = (
            max(0.0, float(request.post_preferential_rate))
            if request.post_preferential_rate is not None
            else pref_rate
        )

        method = (
            request.calculation_method
            if isinstance(request.calculation_method, str)
            else request.calculation_method.value
        ).lower()

        # Handle edge case: 100% down payment or 0 loan amount
        if loan_amount <= 0 or total_months <= 0:
            return MortgageCalcResponse(
                property_price=round(price, 0),
                down_payment_amount=round(price, 0),
                down_payment_percent=round(down_payment_percent, 2),
                loan_amount=0.0,
                loan_term_years=request.loan_term_years,
                loan_term_months=total_months,
                calculation_method=method,
                monthly_payment_first_month=0.0,
                monthly_payment_max=0.0,
                monthly_payment_min=0.0,
                total_interest=0.0,
                total_payment=0.0,
                schedule=[],
            )

        schedule: list[AmortizationScheduleItem] = []
        current_balance = loan_amount

        if method == CalculationMethod.FIXED_PAYMENT.value:
            # Fixed Payment (Annuity / Niên kim cố định)
            r1 = (pref_rate / 100.0) / 12.0
            r2 = (post_rate / 100.0) / 12.0

            # Compute monthly payment for preferential period based on full total_months
            if r1 > 0:
                pmt1 = loan_amount * (r1 * ((1 + r1) ** total_months)) / (((1 + r1) ** total_months) - 1)
            else:
                pmt1 = loan_amount / total_months

            pmt2: float | None = None

            for m in range(1, total_months + 1):
                if m <= pref_months:
                    monthly_r = r1
                    applied_rate = pref_rate
                    target_pmt = pmt1
                else:
                    monthly_r = r2
                    applied_rate = post_rate
                    # Recalculate fixed payment for remaining term at post_rate
                    if pmt2 is None:
                        remaining_months = total_months - pref_months
                        if remaining_months > 0:
                            if r2 > 0:
                                pmt2 = (
                                    current_balance
                                    * (r2 * ((1 + r2) ** remaining_months))
                                    / (((1 + r2) ** remaining_months) - 1)
                                )
                            else:
                                pmt2 = current_balance / remaining_months
                        else:
                            pmt2 = current_balance
                    target_pmt = pmt2

                interest_payment = current_balance * monthly_r
                if m == total_months:
                    # Final month adjustment
                    principal_payment = current_balance
                    remaining_balance = 0.0
                else:
                    principal_payment = max(0.0, min(current_balance, target_pmt - interest_payment))
                    remaining_balance = max(0.0, current_balance - principal_payment)

                total_payment = principal_payment + interest_payment

                schedule.append(
                    AmortizationScheduleItem(
                        month=m,
                        principal_payment=round(principal_payment, 0),
                        interest_payment=round(interest_payment, 0),
                        total_payment=round(total_payment, 0),
                        remaining_balance=round(remaining_balance, 0),
                        interest_rate=round(applied_rate, 2),
                    )
                )
                current_balance = remaining_balance

        else:
            # Declining Balance (Dư nợ giảm dần)
            fixed_principal = loan_amount / total_months

            for m in range(1, total_months + 1):
                if m <= pref_months:
                    applied_rate = pref_rate
                else:
                    applied_rate = post_rate

                monthly_r = (applied_rate / 100.0) / 12.0
                interest_payment = current_balance * monthly_r

                if m == total_months:
                    principal_payment = current_balance
                    remaining_balance = 0.0
                else:
                    principal_payment = min(current_balance, fixed_principal)
                    remaining_balance = max(0.0, current_balance - principal_payment)

                total_payment = principal_payment + interest_payment

                schedule.append(
                    AmortizationScheduleItem(
                        month=m,
                        principal_payment=round(principal_payment, 0),
                        interest_payment=round(interest_payment, 0),
                        total_payment=round(total_payment, 0),
                        remaining_balance=round(remaining_balance, 0),
                        interest_rate=round(applied_rate, 2),
                    )
                )
                current_balance = remaining_balance

        total_interest = sum(item.interest_payment for item in schedule)
        first_month_payment = schedule[0].total_payment if schedule else 0.0
        max_payment = max((item.total_payment for item in schedule), default=0.0)
        min_payment = min((item.total_payment for item in schedule), default=0.0)

        return MortgageCalcResponse(
            property_price=round(price, 0),
            down_payment_amount=round(down_payment, 0),
            down_payment_percent=round(down_payment_percent, 2),
            loan_amount=round(loan_amount, 0),
            loan_term_years=request.loan_term_years,
            loan_term_months=total_months,
            calculation_method=method,
            monthly_payment_first_month=round(first_month_payment, 0),
            monthly_payment_max=round(max_payment, 0),
            monthly_payment_min=round(min_payment, 0),
            total_interest=round(total_interest, 0),
            total_payment=round(loan_amount + total_interest, 0),
            schedule=schedule,
        )


_mortgage_service: MortgageService | None = None


def get_mortgage_service() -> MortgageService:
    global _mortgage_service
    if _mortgage_service is None:
        _mortgage_service = MortgageService()
    return _mortgage_service
