
import pandas as pd
import os

import tempfile
from io import StringIO
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azureml.core import Workspace, Datastore, Dataset

from scr.tools.load_env import load_env_file
from scr.tools.utils import setup_logger

class AzureTools:

    def __init__(self,project_name: str):

        # load logger
        self.logger = setup_logger(log_prefix=project_name)

        # load keys
        load_env_file(".env")
                
        self.STORAGE_KEY = os.getenv('AZ_STORAGE_KEY')
        self.STORAGE_ACCOUNT_NAME =  os.getenv('BLOB_STORAGE_ACCOUNT_NAME')
        self.DATASTORE_NAME = os.getenv('AZMLS_DATASTORE_NAME')

        self.CONN_STRING = os.getenv('BLOB_STORAGE_CONNECTION_STRING')
        self.CONTAINER_NAME = os.getenv('BLOB_CONTAINER_NAME')

        self.TENANT_ID = os.getenv('AZ_TENANT_ID')
        self.CLIENT_ID = os.getenv('AZ_CLIENT_ID')
        # Authenticate 
        credential = DefaultAzureCredential()
        self.token = credential.get_token("https://storage.azure.com/.default")

    def upload_to_ml_datastore(self,
                            data: pd.DataFrame,  
                            blob_file_name: str,                           
                            blob_file_path: str
                            ):
        """
        Upload data from pandas to Blob storage, Via the AMLS datastore.

        Please note that this is not the same as the FM DataStore which is based on Fabric.

        Input:
        - data: DataFrame to upload
        - blob_file_name: Name of the blob file (e.g., 'data.csv')
        - blob_file_path: Path within the blob container (e.g., 'folder')

        Global variables (from .env file):
        - AZMLS_DATASTORE_NAME: Name of the Azure ML datastore configured in your workspace

        1. Connect to Azure ML Workspace
        2. Access the specified datastore
        3. Save DataFrame to a temporary CSV file
        4. Upload the temporary file to blob storage via the datastore
        5. Log the upload status
        """

        # Connect to workspace
        ws = Workspace.from_config()
        self.logger.info(f"Connected to workspace: {ws.name}")

        # Get the datastore
        datastore = Datastore.get(ws, self.DATASTORE_NAME)

        # Save DataFrame to temporary CSV file  
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, blob_file_name)
            data.to_csv(temp_path, index=False)

            # Upload the temp file to blob storage via the datastore
            dataset = Dataset.File.upload_directory(
                src_dir=tmpdir,
                target=(datastore, blob_file_path),
                overwrite=True,
                show_progress=True
            )
            self.logger.info(f"uploaded {blob_file_name} to {datastore.name} that is connected to {datastore.account_name}/{datastore.container_name}/{blob_file_path}")



    def upload_to_blob(self,
                       data: pd.DataFrame,
                       blob_file_name: str):
        '''
        Take a data frame and save it to a blob in Azure Blob Storage.
        The data is converted to CSV format in memory before uploading.
        Saving to Blob reduces local storage needs and centralizes data.

        Global variables (from .env file):
        - CONN_STRING: Azure Storage connection string - 
        - CONTAINER_NAME: Azure Blob container name - 

        Input:
        - data: DataFrame to upload
        - local_file_path: Local file path (for logging purposes)
        '''

        # Try connection string first (Azure VM)
        blob_service_client = BlobServiceClient.from_connection_string(self.CONN_STRING)

        # Get the container client
        container_client = blob_service_client.get_container_client(self.CONTAINER_NAME)
        #blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=f"{STORAGE_PATH}/{TEST_BLOB_NAME}") # this method seems to also work for AMLS

        # Convert DataFrame to CSV in memory
        csv_buffer = StringIO()
        data.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        # Upload as blob
        container_client.upload_blob(name=blob_file_name, data=csv_data, overwrite=True)
        self.logger.info(f"Completed saving to blob:  {self.CONTAINER_NAME}/{blob_file_name}")         

    def download_from_blob(self,
                            blob_file_name: str) -> pd.DataFrame:
        '''
        Download a blob from Azure Blob Storage and load it into a pandas DataFrame.
        The data is assumed to be in CSV format and is loaded directly from memory.
        Loading from Blob provides centralized data access without local storage needs.

        Global variables (from .env file):
        - CONN_STRING: Azure Storage connection string - 
        - CONTAINER_NAME: Azure Blob container name - 

        Input:
        - blob_file_name: Name of the blob file to download

        Output:
        - DataFrame containing the downloaded data
        '''

        # Try connection string first (Azure VM)
        blob_service_client = BlobServiceClient.from_connection_string(self.CONN_STRING)

        # Get the container client
        #container_client = blob_service_client.get_container_client(self.CONTAINER_NAME)
        self.logger.info(f"Starting loading from blob: {self.CONTAINER_NAME}/{blob_file_name}")
        blob_client = blob_service_client.get_blob_client(container=self.CONTAINER_NAME, blob=blob_file_name) # this method seems to also work for AMLS

        # Download blob data as string
        blob_data = blob_client.download_blob()
        csv_content = blob_data.content_as_text()

        # Convert CSV string to DataFrame in memory
        csv_buffer = StringIO(csv_content)
        data = pd.read_csv(csv_buffer)
        self.logger.info(f"Completed loading from blob: {self.CONTAINER_NAME}/{blob_file_name}")
        
        return data