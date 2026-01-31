from typing import Optional

from googleapiclient import discovery
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from google.oauth2 import service_account

from arcane.core import BaseAccount, BadRequestError, UserRightsEnum, RightsLevelEnum
from arcane.requests import call_get_route
from arcane.datastore import Client as DatastoreClient
from arcane.credentials import get_user_decrypted_credentials

from .const import MCT_SCOPE
from .exception import MctAccountLostAccessException, MerchantCenterServiceDownException, get_exception_message

def get_mct_account(
    base_account: BaseAccount,
    clients_service_url: Optional[str] = None,
    firebase_api_key: Optional[str] = None,
    gcp_service_account: Optional[str] = None,
    auth_enabled: bool = True
) -> dict:
    """Call get endpoint to retrieve mct account

    Args:
        base_account (BaseAccount): base account to get
        clients_service_url (Optional[str], optional): clients service url to call. Defaults to None.
        firebase_api_key (Optional[str], optional): needed for calling api. Defaults to None.
        gcp_service_account (Optional[str], optional): needed for calling api. Defaults to None.
        auth_enabled (bool, optional): Boolean to know if we should use token while calling api. Defaults to True.

    Raises:
        BadRequestError: The request does not comply function requirement. See error message for more info

    Returns:
        dict: mct account
    """
    if not (clients_service_url and firebase_api_key and gcp_service_account):
        raise BadRequestError('clients_service_url or firebase_api_key or gcp_service_account should not be None if mct account is not provided')
    url = f"{clients_service_url}/api/mct-account?merchant_id={base_account['id']}&client_id={base_account['client_id']}"
    accounts = call_get_route(
        url,
        firebase_api_key,
        claims={'features_rights': { UserRightsEnum.AMS_GTP: RightsLevelEnum.VIEWER }, 'authorized_clients': ['all']},
        auth_enabled=auth_enabled,
        credentials_path=gcp_service_account
    )
    if len(accounts) == 0:
        raise BadRequestError(f'Error while getting mct account with: {base_account}. No account corresponding.')
    elif len(accounts) > 1:
        raise BadRequestError(f'Error while getting mct account with: {base_account}. Several account corresponding: {accounts}')

    return accounts[0]


def check_access_before_creation(
    mct_account_id: int,
    user_email: str,
    gcp_service_account: str,
    secret_key_file: str,
    gcp_project: str,
    by_pass_user_check: Optional[bool] = False,
    datastore_client: Optional[DatastoreClient] = None) -> bool:
    """ check access before posting account

    Args:
        mct_account_id (int): the id of the account we want to check access
        user_email (str): the email of the user checking access
        gcp_service_account (str): Arcane credential path
        secret_key_file (str): the secret file
        gcp_project (str): the Google Cloud Plateform project
        by_pass_user_check (Optional[bool], optional): By pass user access, used for super admin right. Defaults to False.
        datastore_client (Optional[DatastoreClient], optional): the Datastore client. Defaults to None.

    Raises:
        BadRequestError: Raised when arguments are not good
        MctAccountLostAccessException: Raised when we have no access
        MerchantCenterServiceDownException: Raised when the service is down

    Returns:
        bool: should use user access
    """
    should_use_user_access = True
    scopes = [MCT_SCOPE]

    if not secret_key_file:
        raise BadRequestError('secret_key_file should not be None while using user access protocol')

    user_credentials = get_user_decrypted_credentials(
            user_email=user_email,
            secret_key_file=secret_key_file,
            gcp_credentials_path=gcp_service_account,
            gcp_project=gcp_project,
            datastore_client=datastore_client
        )

    try:
        service = _get_mct_service(user_credentials)
        _get_mct_account_details(service, mct_account_id, user_email)
        _check_if_multi_client_account(service, mct_account_id, user_email)
    except MctAccountLostAccessException as err:
        if not by_pass_user_check:
            if 'multi acccounts' in str(err):
                raise err # We need to raise the mca error as it is
            # We need to overloard the user access error message which different from the run time message
            raise MctAccountLostAccessException(
                "You don't have access to this Merchant Center account, you cannot link it to SmartFeeds."
                " Please ask someone else who have access to do the linking.")
        should_use_user_access = False
        pass

    arcane_credentials = service_account.Credentials.from_service_account_file(gcp_service_account, scopes=scopes)
    try:
        service = _get_mct_service(arcane_credentials)
        _get_mct_account_details(service, mct_account_id, user_email)
        _check_if_multi_client_account(service, mct_account_id, user_email)
        should_use_user_access = False
    except MctAccountLostAccessException as err:
        if by_pass_user_check and not should_use_user_access:
            if 'multi acccounts' in str(err):
                raise err # We need to raise the mca error as it is
            # We need to overloard the user access error message which different from the run time message
            raise MctAccountLostAccessException(
                "You don't have access to this Merchant Center account, you cannot link it to SmartFeeds."
                " Please ask someone else who have access to do the linking.")
        pass
    return should_use_user_access


def _get_mct_service(credentials):
    return discovery.build('content', 'v2.1', credentials=credentials, cache_discovery=False)


def _get_mct_account_details(service, merchant_id: int, user_email: Optional[str] = None):
    """
        From mct id, will return mct account name
    """
    try:
        # Get account status alerts from MCT
        request_account_statuses = service.accounts().get(merchantId=merchant_id,
                                                        accountId=merchant_id)
        response_account_statuses = request_account_statuses.execute()
    # RefreshError is raised when we have invalid merchant_id or we don't have access to the account
    except RefreshError as err:
        raise MctAccountLostAccessException(get_exception_message(merchant_id, user_email))
    except HttpError as err:
        if err.resp.status >= 400 and err.resp.status < 500:
            raise MctAccountLostAccessException(get_exception_message(merchant_id, user_email))
        else:
            raise MerchantCenterServiceDownException(f"The Merchent Center API does not respond. Thus, we cannot check if we can access your Merchant Center account with the id: {merchant_id}. Please try again later." )
    return response_account_statuses['name']


def _check_if_multi_client_account(service, merchant_id: int, user_email: Optional[str] = None):
    """
        Sends an error if the account is a MCA
    """
    try:
        # This API method is only available to sub-accounts, thus it will fail if the merchant id is a MCA
        request_account_products = service.products().list(merchantId=merchant_id)
        response_account_statuses = request_account_products.execute()
    # RefreshError is raised when we have invalid merchant_id or we don't have access to the account
    except RefreshError as err:
        raise MctAccountLostAccessException(get_exception_message(merchant_id, user_email))
    except HttpError as err:
        if err.resp.status >= 400 and err.resp.status < 500:
            raise MctAccountLostAccessException(f"This merchant id ({merchant_id}) is for multi acccounts. You can only link sub-accounts.")
        else:
            raise MerchantCenterServiceDownException(f"The Merchent Center API does not respond. Thus, we cannot check if we can access your Merchant Center account with the id: {merchant_id}. Please try again later." )
    return response_account_statuses
