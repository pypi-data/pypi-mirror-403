class TransferDto:
    """
    Represents the data of a transfer.
    """
    def __init__(self, data: dict = None):
        self.id = None
        self.end_to_end_id = None
        self.external_id = None
        self.status = None
        self.type = None
        self.amount = None
        self.created_at = None
        self.updated_at = None
        self.error = None
        self.payer = None
        self.beneficiary = None

        if data:
            self.id = data.get('id')
            self.end_to_end_id = data.get('endToEndId')
            self.external_id = data.get('externalId')
            self.status = data.get('status')
            self.type = data.get('type')
            self.amount = data.get('amount')
            self.created_at = data.get('createdAt')
            self.updated_at = data.get('updatedAt')
            self.error = data.get('error')
            self.payer = data.get('payer')
            self.beneficiary = data.get('beneficiary')
