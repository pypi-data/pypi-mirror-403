from ..dto.transfer_dto import TransferDto

class GetTransferResponse:
    """
    Response wrapper for Get Transfer operation.
    """
    def __init__(self, transfer: TransferDto):
        self.transfer = transfer
