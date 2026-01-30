"""
Google Cloud Platform authentication utilities.
"""

import os
from google.auth import default, impersonated_credentials
from google.auth.transport.requests import Request


def get_credentials():
    """
    Get Google Cloud credentials with optional service account impersonation.
    
    If GOOGLE_IMPERSONATE_SERVICE_ACCOUNT environment variable is set,
    impersonates that service account. Otherwise, uses default credentials.
    
    Returns:
        google.auth.credentials.Credentials: Google Cloud credentials to use for authentication.
    """
    impersonate_sa = os.getenv('GOOGLE_IMPERSONATE_SERVICE_ACCOUNT')

    if impersonate_sa:
        source_credentials, _ = default(
        scopes = [
            'https://www.googleapis.com/auth/bigquery',
            'https://www.googleapis.com/auth/cloud-platform',
            'https://www.googleapis.com/auth/drive',
        ])
        source_credentials.refresh(Request())

        return impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=impersonate_sa,
            target_scopes=['https://www.googleapis.com/auth/cloud-platform'],
            lifetime=3600
        )
    else:
        credentials, _ = default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        return credentials
