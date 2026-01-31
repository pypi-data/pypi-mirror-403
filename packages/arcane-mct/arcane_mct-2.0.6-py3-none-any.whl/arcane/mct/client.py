from typing import Optional, cast
import backoff
import socket

from arcane.datastore import Client as DatastoreClient
from arcane.core import BaseAccount, BadRequestError
from arcane.credentials import get_user_decrypted_credentials

from google.oauth2 import service_account

from .helpers import _check_if_multi_client_account, _get_mct_account_details, _get_mct_service, get_mct_account
from .const import MCT_SCOPE

class MctClient:
    def __init__(
        self,
        gcp_service_account: str,
        base_account: Optional[BaseAccount] = None,
        mct_account: Optional[dict] = None,
        datastore_client: Optional[DatastoreClient] = None,
        gcp_project: Optional[str] = None,
        secret_key_file: Optional[str] = None,
        firebase_api_key: Optional[str] = None,
        auth_enabled: bool = True,
        clients_service_url: Optional[str] = None,
        user_email: Optional[str] = None
    ):
        scopes = [MCT_SCOPE]
        creator_email = None
        if gcp_service_account and (mct_account or base_account or user_email):
            if user_email:
                creator_email = user_email
            else:
                if mct_account is None:
                    base_account = cast(BaseAccount, base_account)
                    mct_account = get_mct_account(
                        base_account=base_account,
                        clients_service_url=clients_service_url,
                        firebase_api_key=firebase_api_key,
                        gcp_service_account=gcp_service_account,
                        auth_enabled=auth_enabled
                    )

                creator_email = cast(str, mct_account['creator_email'])

            if creator_email is not None:
                if not secret_key_file:
                    raise BadRequestError('secret_key_file should not be None while using user access protocol')

                credentials = get_user_decrypted_credentials(
                    user_email=creator_email,
                    secret_key_file=secret_key_file,
                    gcp_credentials_path=gcp_service_account,
                    gcp_project=gcp_project,
                    datastore_client=datastore_client
                )
            else:
                credentials = service_account.Credentials.from_service_account_file(gcp_service_account, scopes=scopes)
        elif gcp_service_account:
            ## Used when posting an account using our credential (it is not yet in our database)
            credentials = service_account.Credentials.from_service_account_file(gcp_service_account, scopes=scopes)
        else:
            raise BadRequestError('one of the following arguments must be specified: gcp_service_account and (mct_account or base_account or user_email)')
        self.creator_email = creator_email
        self.credentials = credentials
        self.service = _get_mct_service(credentials)

    @backoff.on_exception(backoff.expo, (socket.timeout), max_tries=3)
    def get_mct_account_details(
        self,
        merchant_id: int
    ):
        return _get_mct_account_details(self.service, merchant_id, self.creator_email)

    @backoff.on_exception(backoff.expo, (socket.timeout), max_tries=3)
    def check_if_multi_client_account(
        self,
        merchant_id: int,
    ):
       return _check_if_multi_client_account(self.service, merchant_id, self.creator_email)



