import os
from typing import Optional, Dict, Any

import boto3
import boto3.utils
import requests


class AWSService():
    """
    A service class to interact with AWS S3 for downloading and managing raw satellite imagery products.

    This class provides methods for obtaining authentication tokens from an external provider 
    (e.g., Copernicus), downloading imagery from S3, and managing datasets using GDAL.
    
    Example usage:
        ### Initialize the AWSService with optional credentials
        service = AWSService(
            client_id="your_aws_key",
            client_secret="your_aws_secret"
        )
        
        ### Download products from S3
        imagery_metadata = [{"properties": {...}, "assets": {...}}]
        service.download_zipped_raw_products(
            imagery=imagery_metadata,
            output_dir="/path/to/save"
        )
    """
    
    def __init__(self, client_id:Optional[str] = None, client_secret:Optional[str] = None) -> None:
        """
        Initializes the AWSService instance with optional AWS credentials.
        
        If no credentials are provided, it will look for them in the environment variables:
        `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

        Parameters:
            client_id (Optional[str]): The AWS access key ID. Defaults to environment variable `AWS_ACCESS_KEY_ID`.
            client_secret (Optional[str]): The AWS secret access key. Defaults to environment variable `AWS_SECRET_ACCESS_KEY`.
        """
        if client_id is None and "AWS_ACCESS_KEY_ID" in os.environ and "AWS_SECRET_ACCESS_KEY" in os.environ:
            self.client_id = os.getenv('AWS_ACCESS_KEY_ID')
            self.client_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
        else:
            self.client_id = client_id
            self.client_secret = client_secret
        
    def get_token(self, client_id:str, token_provider:str, username:Optional[str] = None, password:Optional[str] = None) -> str:
        """
        Fetches an authentication token from the specified token provider.

        Parameters:
            client_id (str): The client ID for the token provider. For Copernicus, this is typically 'cdse-public'.
            token_provider (str): The URL of the token provider to authenticate against.
            username (str): The username required for authentication.
            password (str): The password required for authentication.

        Returns:
            str: The authentication token used to access secure resources.

        Raises:
            Exception: If the request fails or returns an error.
        
        Example:
            token = service.get_token(
                client_id="cdse-public",
                token_provider="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                username="your_username",
                password="your_password"
            )
        """
        
        if username is None and "TOKEN_USERNAME" in os.environ and "TOKEN_PASSWORD" in os.environ:
            username = os.getenv('TOKEN_USERNAME')
            password = os.getenv('TOKEN_PASSWORD')
        
        data = {
            "client_id": client_id,
            "username": username,
            "password": password,
            "grant_type": "password",
        }
        try:
            response = requests.post( token_provider, data=data, timeout=10)
            response.raise_for_status()
        except Exception:
            raise Exception(f"Token creation failed. Reponse from the server was: {response.json()}")
        
        return response.json()["access_token"]
    
    """
    """
    # def get_file(self, file_path:str, session_token:str) -> gdal.Dataset:
    #     """
    #     Retrieves a file from AWS S3 using GDAL with the provided session token.

    #     Parameters:
    #         file_path (str): The S3 path to the file (e.g., 'bucket_name/path/to/file').
    #         session_token (str): The session token for AWS S3 access.

    #     Returns:
    #         gdal.Dataset: A GDAL dataset representing the file from S3.

    #     Raises:
    #         Exception: If there is an error retrieving the file from S3.
        
    #     Example:
    #         dataset = service.get_file(
    #             file_path="bucket_name/path/to/file",
    #             session_token="your_session_token"
    #         )
    #     """
    #     try:
    #         from osgeo import gdal
    #     except:
    #         print('GDAL was not found.')
    #         return
        
    #     gdal.SetConfigOption('AWS_ACCESS_KEY_ID', self.client_id)
    #     gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', self.client_secret)
    #     gdal.SetConfigOption('AWS_SESSION_TOKEN', session_token)
    #     gdal.SetConfigOption('AWS_REGION', 'us-east-2')
    #     return gdal.Open(f'/vsis3{file_path}')
    
    def download_raw_product(self, image:Dict[str, Any], endpoint:str, output_dir:Optional[str] = f'{os.getcwd()}/') -> None:
        """
        Retrieves a file from AWS S3 using GDAL with the provided session token.

        Parameters:
            file_path (str): The S3 path to the file (e.g., 'bucket_name/path/to/file').
            session_token (str): The session token for AWS S3 access.

        Returns:
            gdal.Dataset: A GDAL dataset representing the file from S3.

        Raises:
            Exception: If there is an error retrieving the file from S3.
        
        Example:
            dataset = service.get_file(
                file_path="bucket_name/path/to/file",
                session_token="your_session_token"
            )
        """
        # session = boto3.session.Session()
        # https://registry.opendata.aws/sentinel-2-l2a-cogs/
        s3 = boto3.resource(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=self.client_id,
            aws_secret_access_key=self.client_secret,
            region_name='default'
        )
        
        link = image['assets']['PRODUCT']['alternate']['s3']['href'].strip('/').split('/')
        bucket = s3.Bucket(link.pop(0))
        product = '/'.join(link)
        files = bucket.objects.filter(Prefix=product)
        if not list(files):
            raise FileNotFoundError(f"Could not find any files for {product}")
        
        for file in files:
            file_path = os.path.join(output_dir, file.key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if not os.path.isdir(file_path) and not os.path.exists(file_path):
                bucket.download_file(file.key, file_path)

    def download_zipped_raw_products(self, image_metadata: Dict[str, Any], session_token:str, output_dir:Optional[str] = '') -> None:
        """
        Downloads raw satellite image product as zipped files and saves them to the specified output directory.

        Parameters:
            imagery (Dict[str, Any]): Image metadata dictionary, containing download URL.
            output_dir (Optional[str]): The directory where the downloaded zipped files will be stored. Defaults to the current working directory.

        Example:
            service.download_zipped_raw_products(
                imagery=imagery_metadata,
                output_dir="/path/to/save"
            )
        """
        url = image_metadata['assets']['PRODUCT']['href']

        headers = {"Authorization": f"Bearer {session_token}"}

        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, headers=headers, stream=True)

        file_name = image_metadata['id'].replace('.SAFE', '')
        with open(f'{output_dir}/{file_name}.zip', 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)