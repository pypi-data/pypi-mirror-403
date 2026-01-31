import os
import sys
import json
from dotenv import load_dotenv
from flask import Flask

# Add src to path so we can import delfinance   
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from delfinance.abstractions.startup.delfinance_client import DelfinanceClient
from delfinance.abstractions.enums.environment import Environment
from delfinance.transfers.services.transfers_service import TransfersService

app = Flask(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '.env.example')

load_dotenv(env_path)

@app.route('/')
def home():
    output = []
    def echo(text):
        output.append(str(text))

    echo("<h1>Teste do SDK Python 3.7</h1>")

    try:
        # Configuração inicial via Variáveis de Ambiente
        api_key = os.getenv('DELFINANCE_API_KEY', 'test_api_key_default')
        account_id = os.getenv('DELFINANCE_ACCOUNT_ID', 'test_account_id_default')
        
        env_str = os.getenv('DELFINANCE_ENVIRONMENT')
        env = Environment.PRODUCTION if env_str == 'production' else Environment.SANDBOX
        
        cert_path = os.getenv('DELFINANCE_CERT_PATH')
        key_path = os.getenv('DELFINANCE_KEY_PATH')
        test_transfer_id = os.getenv('TEST_TRANSFER_ID', 'tr_example')

        config = {
            'apiKey': api_key,
            'accountId': account_id,
            'environment': env,
            'certificatePath': cert_path,
            'privateKeyPath': key_path
        }

        client = DelfinanceClient(config)

        echo("<h3>1. Inicialização</h3>")
        echo("<ul>")
        echo(f"<li>Ambiente: {client.get_environment().value}</li>")
        echo(f"<li>Base URL: {client.get_base_url()}</li>")
        masked_key = client.get_api_key()[:5] + "***" if len(client.get_api_key()) > 5 else "***"
        echo(f"<li>API Key: {masked_key}</li>")
        echo(f"<li>Account ID: {client.get_account_id()}</li>")
        echo("</ul>")

        # Teste do Serviço de Transferências
        echo("<h3>2. Teste de GET Transfer</h3>")
        
        transfers_service = TransfersService(client)
        
        try:
            echo(f"Buscando transferência: {test_transfer_id} <br/>")
            
            response = transfers_service.get_transfer(test_transfer_id)
            
            echo("<pre>")
            # Convert object to dict for printing
            echo(json.dumps(response.transfer.__dict__, indent=4))
            echo("</pre>")

        except Exception as e:
            echo(f"<p style='color:orange'><strong>Resultado esperado (Erro de API ou Conexão):</strong> {str(e)}</p>")
            echo("<small>Nota: Se você não configurou um .env com credenciais reais, este erro é esperado.</small>")

    except Exception as e:
        echo(f"<p style='color:red'>Erro Crítico: {str(e)}</p>")

    echo("<br/>")
    echo(f"Python Version: {sys.version}")
    
    return "\n".join(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
