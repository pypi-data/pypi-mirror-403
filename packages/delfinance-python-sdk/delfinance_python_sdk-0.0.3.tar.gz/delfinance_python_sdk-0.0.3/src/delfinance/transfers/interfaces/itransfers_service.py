from abc import ABC, abstractmethod

class ITransfersService(ABC):
    @abstractmethod
    def get_transfer(self, transfer_identifier: str):
        pass
