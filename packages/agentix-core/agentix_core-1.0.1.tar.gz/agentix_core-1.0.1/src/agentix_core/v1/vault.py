import os
import asyncio
import logging
from typing import Optional
from infisical_sdk import InfisicalSDKClient

logger = logging.getLogger("vault")


class Vault:
    """
    Agentix Vault integration for secure secret management.
    
    Provides secure storage and retrieval of secrets from the Agentix Vault.
    Secrets are stored at /providers/{provider} path in the 'prod' environment.
    
    Usage:
        # Using environment variables (VAULT_URL, VAULT_CLIENT_ID, VAULT_CLIENT_SECRET, VAULT_PROJECT_ID)
        vault = Vault()
        secret = await vault.get_secret(secret_key="credential-123", provider="stripe")
        
        # Or with explicit parameters
        vault = Vault(
            host="https://vault.example.com",
            client_id="your-client-id",
            client_secret="your-client-secret",
            project_id="your-project-id"
        )
    """

    def __init__(
        self,
        host: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        """
        Initialize the Vault client.
        
        Args:
            host (str | None): Vault host URL. Falls back to VAULT_URL environment variable.
            client_id (str | None): Client ID for authentication. Falls back to VAULT_CLIENT_ID.
            client_secret (str | None): Client secret for authentication. Falls back to VAULT_CLIENT_SECRET.
            project_id (str | None): Project ID. Falls back to VAULT_PROJECT_ID.
            
        Raises:
            ValueError: If any required credential is missing from both parameters and environment variables.
            
        Example:
            vault = Vault()  # Uses environment variables
            vault = Vault(host="https://vault.example.com", client_id="...", client_secret="...", project_id="...")
        """
        # Get credentials from parameters or environment variables
        self.host = host or os.getenv("VAULT_URL")
        self.client_id = client_id or os.getenv("VAULT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("VAULT_CLIENT_SECRET")
        self.project_id = project_id or os.getenv("VAULT_PROJECT_ID")
        
        # Validate required credentials
        if not self.host:
            raise ValueError("Vault host is required. Provide 'host' parameter or set VAULT_URL environment variable.")
        
        if not self.client_id:
            raise ValueError("Vault client_id is required. Provide 'client_id' parameter or set VAULT_CLIENT_ID environment variable.")
        
        if not self.client_secret:
            raise ValueError("Vault client_secret is required. Provide 'client_secret' parameter or set VAULT_CLIENT_SECRET environment variable.")
        
        if not self.project_id:
            raise ValueError("Vault project_id is required. Provide 'project_id' parameter or set VAULT_PROJECT_ID environment variable.")
        
        # Initialize Vault client
        self.client = InfisicalSDKClient(host=self.host)
        
        # Authenticate with Universal Auth
        try:
            self.client.auth.universal_auth.login(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            logger.info(f"✅ [VAULT] Successfully authenticated with Vault at {self.host}")
        except Exception as e:
            logger.error(f"❌ [VAULT] Failed to authenticate with Vault: {str(e)}")
            raise ValueError(f"Failed to authenticate with Vault: {str(e)}")

    async def get_secret(self, secret_key: str, provider: str) -> Optional[str]:
        """
        Retrieve a secret from the Vault.
        
        Constructs the secret path as /providers/{provider} and retrieves the secret
        from the 'prod' environment. Returns the raw secret value as stored.
        
        Args:
            secret_key (str): The key/name of the secret to retrieve (e.g., credential ID).
            provider (str): The provider slug used to construct the path (e.g., "stripe", "aws").
            
        Returns:
            str | None: The secret value if found, None if secret doesn't exist or on error.
            
        Raises:
            ValueError: If secret_key or provider is empty.
            
        Example:
            secret = await vault.get_secret(secret_key="cred-123", provider="stripe")
            if secret:
                credentials = json.loads(secret)  # If secret is JSON
        """
        # Validate inputs
        if not secret_key:
            logger.error("[VAULT] secret_key is required and cannot be empty.")
            raise ValueError("secret_key is required and cannot be empty.")
        
        if not provider:
            logger.error("[VAULT] provider is required and cannot be empty.")
            raise ValueError("provider is required and cannot be empty.")
        
        # Construct secret path following Node.js pattern: /providers/{provider}
        secret_path = f"/providers/{provider}"
        
        try:
            # Run synchronous SDK call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            secret = await loop.run_in_executor(
                None,
                lambda: self.client.secrets.get_secret_by_name(
                    secret_name=secret_key,
                    project_id=self.project_id,
                    environment_slug="prod",  # Always use prod environment
                    secret_path=secret_path
                )
            )
            
            # Return the secret value
            if secret and hasattr(secret, 'secretValue'):
                logger.info(f"✅ [VAULT] Successfully retrieved secret '{secret_key}' from {secret_path}")
                return secret.secretValue
            else:
                logger.warning(f"⚠️ [VAULT] Secret '{secret_key}' not found at {secret_path}")
                return None
                
        except Exception as e:
            logger.error(f"❌ [VAULT] Error retrieving secret '{secret_key}' from {secret_path}: {str(e)}")
            return None
