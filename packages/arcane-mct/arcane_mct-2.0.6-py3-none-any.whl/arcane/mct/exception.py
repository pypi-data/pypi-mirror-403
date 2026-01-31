from typing import Optional

class MctAccountLostAccessException(Exception):
    """Raised when we cannot access to an account."""
    pass


class MerchantCenterServiceDownException(Exception):
    """Raised when we cannot access to MCC service """
    pass

def get_exception_message(merchant_id: int, creator_email: Optional[str] = None) -> str:
    if creator_email:
        return f"{creator_email} has no longer access. Please renew the access to {merchant_id}."
    else:
        return F"We cannot access your Merchant Center account with the id: {merchant_id} from the Arcane account. Are you sure you granted access and gave the correct ID?"
