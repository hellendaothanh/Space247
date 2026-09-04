import logging
from fastapi import APIRouter, Depends, HTTPException, status

from src.schemas.mortgage import MortgageCalcRequest, MortgageCalcResponse
from src.services.mortgage_service import MortgageService, get_mortgage_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/mortgage-calc",
    response_model=MortgageCalcResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate mortgage amortization schedule (Public endpoint)",
    description=(
        "Public financial tool to compute mortgage repayment schedules. "
        "Supports declining balance ('declining_balance') and fixed payment ('fixed_payment'), "
        "preferential interest rate periods, and post-preferential floating rates."
    ),
)
async def calculate_mortgage_schedule(
    request: MortgageCalcRequest,
    mortgage_service: MortgageService = Depends(get_mortgage_service),
) -> MortgageCalcResponse:
    """
    Public mortgage calculator endpoint:
    - No authentication required so all visitors can simulate loan affordability.
    - Validates loan term between 1 and 35 years.
    - Generates complete monthly amortization schedules rounded in VND.
    """
    if request.loan_term_years < 1 or request.loan_term_years > 35:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loan term must be between 1 and 35 years",
        )

    try:
        return mortgage_service.calculate_mortgage(request)
    except Exception as e:
        logger.error("Error calculating mortgage: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculation error: {str(e)}",
        )
