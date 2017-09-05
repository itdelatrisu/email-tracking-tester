import os

# Server host
HOST = 'localhost'  #'example.com'

# SSL configuration
SSL_ENABLED = False
SSL_CERT_PATH = '/path/to/certificates/'
SSL_CERTFILE = os.path.join(SSL_CERT_PATH, 'cert.pem')
SSL_KEYFILE = os.path.join(SSL_CERT_PATH, 'privkey.pem')

# Mailer configuration
MAILER_SETTINGS = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': None,  #'example@gmail.com'
    'password': None,  #'password123'
}

# Sending rate limits (time in seconds)
GLOBAL_RATE_LIMIT = {
    'max_amount': 500,
    'refill_time': int(24*60*60/500),
    'refill_amount': 1,
}
IP_RATE_LIMIT = {
    'max_amount': 5,
    'refill_time': 30,
    'refill_amount': 1,
}

# Database location
DB_PATH = os.path.join(os.path.dirname(__file__), 'results.db')

# Results page authentication
RESULTS_AUTH = False
RESULTS_CREDS = {'admin': 'password'}
