import os
from ..enums.environment import Environment

class DelfinanceClient:
    """
    Main entry point for the SDK configuration and initialization.
    """
    def __init__(self, config: dict):
        """
        DelfinanceClient constructor.
        
        :param config: Dictionary with configuration options:
                       - apiKey: (string) Your API Key
                       - accountId: (string) Your Account ID (x-delfinance-account-id)
                       - environment: (Environment) Environment.SANDBOX or Environment.PRODUCTION
                       - certificatePath: (string) Path to the client certificate (PEM) for mTLS
                       - privateKeyPath: (string) Path to the private key (PEM) for mTLS
        """
        self._validate_config(config)
        
        self.api_key = config['apiKey']
        self.account_id = config['accountId']
        self.environment = config['environment']
        self.certificate_path = config.get('certificatePath')
        self.private_key_path = config.get('privateKeyPath')

    def _validate_config(self, config: dict):
        if not config.get('apiKey'):
            raise Exception("API Key is required.")
        
        if not config.get('accountId'):
            raise Exception("Account ID is required.")
        
        if not config.get('environment'):
            raise Exception("Environment is required.")
            
        if config['environment'] not in [Environment.SANDBOX, Environment.PRODUCTION]:
            raise Exception("Invalid environment.")
            
        if config.get('certificatePath') and not os.path.exists(config['certificatePath']):
            raise Exception(f"Certificate file not found at: {config['certificatePath']}")
            
        if config.get('privateKeyPath') and not os.path.exists(config['privateKeyPath']):
            raise Exception(f"Private key file not found at: {config['privateKeyPath']}")

    def get_api_key(self) -> str:
        return self.api_key

    def get_account_id(self) -> str:
        return self.account_id

    def get_environment(self) -> Environment:
        return self.environment

    def get_certificate_path(self) -> str:
        return self.certificate_path

    def get_private_key_path(self) -> str:
        return self.private_key_path

    def get_base_url(self) -> str:
        if self.environment == Environment.PRODUCTION:
            return 'https://api.delfinance.com/v1'
        
        return 'https://apisandbox.delbank.com.br'
