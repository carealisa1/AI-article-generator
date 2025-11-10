import streamlit_authenticator as stauth

# Configuration for Streamlit Authenticator
# Strong password: Article2025

def create_authenticator():
    """Create and return the authenticator instance"""
    
    # Configuration dictionary with plain text password (will be hashed automatically)
    config = {
        'credentials': {
            'usernames': {
                'admin': {
                    'email': 'admin@aicontentgenerator.com',
                    'first_name': 'Content',
                    'last_name': 'Administrator', 
                    'password': 'Article2025',  # Plain text - will be hashed automatically
                    'failed_login_attempts': 0,  # Will be managed automatically
                    'logged_in': False  # Will be managed automatically
                }
            }
        },
        'cookie': {
            'name': 'ai_content_generator_auth',
            'key': 'ai_content_random_signature_key_2024',  # Random key for cookie encryption
            'expiry_days': 7  # Cookie expires in 7 days
        }
    }
    
    # Hash the passwords once (this will modify the config dict)
    stauth.Hasher.hash_passwords(config['credentials'])
    
    # Create authenticator instance
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    return authenticator

# Credentials for users:
# Email: admin@aicontentgenerator.com
# Password: Article2025