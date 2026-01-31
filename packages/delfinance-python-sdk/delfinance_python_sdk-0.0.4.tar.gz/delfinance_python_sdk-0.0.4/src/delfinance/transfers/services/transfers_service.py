import requests
import json
from ...abstractions.startup.delfinance_client import DelfinanceClient
from ..interfaces.itransfers_service import ITransfersService
from ..dto.transfer_dto import TransferDto
from ..responses.get_transfer_response import GetTransferResponse

class TransfersService(ITransfersService):
    def __init__(self, client: DelfinanceClient):
        self.client = client

    def get_transfer(self, transfer_identifier: str) -> GetTransferResponse:
        url = f"{self.client.get_base_url()}/baas/api/v2/transfers/{transfer_identifier}"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-delbank-api-key': self.client.get_api_key(),
            'x-delfinance-account-id': self.client.get_account_id(),
        }

        # Setup mTLS if configured
        cert = None
        if self.client.get_certificate_path() and self.client.get_private_key_path():
            cert = (self.client.get_certificate_path(), self.client.get_private_key_path())

        try:
            response = requests.get(
                url, 
                headers=headers, 
                cert=cert,
                timeout=30
            )
            
            if response.status_code >= 400:
                raise Exception(f"API Error: {response.text}", response.status_code)
            
            data = response.json()
            dto = TransferDto(data)
            return GetTransferResponse(dto)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request Error: {str(e)}")
