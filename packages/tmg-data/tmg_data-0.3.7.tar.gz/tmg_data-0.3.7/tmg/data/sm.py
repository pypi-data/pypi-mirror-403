"""
Google Cloud Secret Manager functionality.
"""

import os
import json
from google.cloud import secretmanager
from tmg.data.auth import get_credentials
from tmg.data import logs


class Client:
    """
    Client to bundle Secret Manager functionality.

    Args:
        project (str): The Project ID for the project which the client acts on behalf of.
        credentials (optional): Google Cloud credentials to use. If not provided, uses default credentials.
    """

    def __init__(self, project, credentials=None):
        self.project = project
        
        if credentials is None:
            credentials = get_credentials()
        
        self.credentials = credentials
        self.client = secretmanager.SecretManagerServiceClient(credentials=credentials)

    def create_secret(self, secret_id, labels=None):
        """
        Create a new secret in Secret Manager.

        Args:
            secret_id (str, optional): The ID for the secret to create.
            labels (dict, optional): Labels to apply to the secret. Defaults to None.

        Returns:
            google.cloud.secretmanager_v1.types.Secret: The created secret.

        Examples:
            >>> from tmg.data import secretmanager
            >>> client = secretmanager.Client(project='my-project-id')
            >>> client.create_secret('my-secret', labels={'env': 'production'})
        """
        parent = f"projects/{self.project}"

        secret = {
            "replication": {
                "automatic": {},
            },
        }

        if labels:
            secret["labels"] = labels

        logs.client.logger.info(f'Creating secret {secret_id} in project {self.project}')
        response = self.client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": secret,
            }
        )
        logs.client.logger.info(f'Secret {secret_id} created successfully')
        return response

    def add_secret_version(self, payload, secret_id):
        """
        Add a new version to an existing secret with the given payload.

        Args:
            payload (str or bytes): The secret data to store.
            secret_id (str, optional): The ID of the secret.

        Returns:
            google.cloud.secretmanager_v1.types.SecretVersion: The created secret version.

        Examples:
            >>> from tmg.data import secretmanager
            >>> client = secretmanager.Client(project='my-project-id')
            >>> client.add_secret_version('my-secret-value', 'my-secret')
        """
        parent = f"projects/{self.project}/secrets/{secret_id}"

        # Convert string to bytes if necessary
        if isinstance(payload, str):
            payload = payload.encode("UTF-8")

        logs.client.logger.info(f'Adding new version to secret {secret_id}')
        response = self.client.add_secret_version(
            request={
                "parent": parent,
                "payload": {"data": payload},
            }
        )
        logs.client.logger.info(f'New version added to secret {secret_id}')
        return response

    def get_secret(self, secret_id, version_id="latest"):
        """
        Access a secret version and retrieve its payload as a dictionary.

        Args:
            secret_id (str, optional): The ID of the secret.
            version_id (str, optional): The version of the secret to access. Defaults to "latest".

        Returns:
            dict: The secret payload parsed as a JSON dictionary.

        Examples:
            >>> from tmg.data import secretmanager
            >>> client = secretmanager.Client(project='my-project-id')
            >>> secret_value = client.get_secret('my-secret')
            >>> secret_value = client.get_secret('my-secret', version_id='1')
        """
        name = f"projects/{self.project}/secrets/{secret_id}/versions/{version_id}"

        logs.client.logger.info(f'Retrieving secret {secret_id} version {version_id}')
        response = self.client.access_secret_version(request={"name": name})
        
        payload = response.payload.data.decode("UTF-8")
        logs.client.logger.info(f'Secret {secret_id} retrieved successfully')
        
        return json.loads(payload)

    def delete_secret(self, secret_id):
        """
        Delete a secret and all of its versions.

        Args:
            secret_id (str, optional): The ID of the secret to delete.

        Examples:
            >>> from tmg.data import secretmanager
            >>> client = secretmanager.Client(project='my-project-id')
            >>> client.delete_secret('my-secret')
        """
        name = f"projects/{self.project}/secrets/{secret_id}"

        logs.client.logger.info(f'Deleting secret {secret_id}')
        self.client.delete_secret(request={"name": name})
        logs.client.logger.info(f'Secret {secret_id} deleted successfully')

    def list_secrets(self):
        """
        List all secrets in the project.

        Returns:
            list: A list of secret names.

        Examples:
            >>> from tmg.data import secretmanager
            >>> client = secretmanager.Client(project='my-project-id')
            >>> secrets = client.list_secrets()
        """
        parent = f"projects/{self.project}"

        logs.client.logger.info(f'Listing secrets in project {self.project}')
        secrets = []
        for secret in self.client.list_secrets(request={"parent": parent}):
            secrets.append(secret.name)
        
        logs.client.logger.info(f'Found {len(secrets)} secrets')
        return secrets