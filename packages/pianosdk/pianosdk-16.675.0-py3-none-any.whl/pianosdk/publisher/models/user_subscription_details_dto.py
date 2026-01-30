from datetime import date, datetime
from pydantic.main import BaseModel
from typing import Optional


class UserSubscriptionDetailsDto(BaseModel):
    term_name: Optional[str] = None
    term_id: Optional[str] = None
    type: Optional[str] = None
    payment_billing_plan: Optional[str] = None
    billing_plan: Optional[str] = None
    subscription_id: Optional[str] = None
    is_stripe: Optional[bool] = None
    payment_method: Optional[str] = None
    status: Optional[str] = None
    status_display: Optional[str] = None
    user_payment_info_id: Optional[str] = None
    access_id: Optional[str] = None
    last_conversion_id: Optional[str] = None
    last_payment_conversion_id: Optional[str] = None
    delivery_schedule_pub_id: Optional[str] = None
    owner: Optional[str] = None
    stripe_billing_sync_state: Optional[str] = None
    stripe_subscription_id: Optional[str] = None


UserSubscriptionDetailsDto.model_rebuild()
