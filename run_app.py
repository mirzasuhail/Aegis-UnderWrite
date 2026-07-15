import os
import sys

# Add project root directory to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

from backend.app import create_app

# Create app instance
config_name = os.environ.get('FLASK_CONFIG', 'dev')
app = create_app(config_name)

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    print("="*60)
    print("RUNNING CREDIT CARD APPROVAL SYSTEM FLASK SERVER")
    print("="*60)
    print(f"Server address: http://{host}:{port}/")
    print("="*60)
    app.run(host=host, port=port, debug=app.config['DEBUG'])
