
import pandas as pd
import os
import io
from datetime import datetime

from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential

from deltalake import write_deltalake, DeltaTable
from azure.storage.filedatalake import DataLakeServiceClient

import pyreadstat
import pyarrow as pa

from scr.tools.load_env import load_env_file
from scr.tools.utils import setup_logger,load_config

class FabricTools:

    def __init__(self,project_name: str, FABRIC_WORKSPACE_NAME: str):

        # load logger
        self.logger = setup_logger(log_prefix=project_name)

        # load Account name
        load_env_file(".env")
        self.FABRIC_ACCOUNT_NAME = os.getenv('FABRIC_ACCOUNT_NAME')
        
        # load lakehouses
        config = load_config("datastore_config.yaml")
        self.lakehouse_list = ['bronze', 'silver', 'gold', 'sandbox']
        self.gold_lakehouse_name = config['datastore']['lakehouses'][2]
        self.bronze_lakehouse_name = config['datastore']['lakehouses'][0]
        self.silver_lakehouse_name = config['datastore']['lakehouses'][1]

        # Authenticate 
        credential = DefaultAzureCredential()
        self.token = credential.get_token("https://storage.azure.com/.default")
        
        # Create DataLake service client using the credential directly
        self.service_client = DataLakeServiceClient(
            account_url=f"https://{self.FABRIC_ACCOUNT_NAME}.dfs.fabric.microsoft.com",
            credential=credential  # Use the credential object, not the token
        )

        # List accessible lakehouses and workspaces, and validate if the target workspace exists / the user has access
        lakehouses, self.workspaces = self.list_accessible_lakehouses()
        
        # Get the file system (workspace) client
        self.FABRIC_WORKSPACE_NAME= FABRIC_WORKSPACE_NAME
        self.file_system_client = self.service_client.get_file_system_client(
            file_system=self.FABRIC_WORKSPACE_NAME
        )
        
        self.validate_workspace(self.FABRIC_WORKSPACE_NAME)
        

        

    def check_a_datastore_table_exists(self, lakehouse_name: str, table_name: str) -> bool:
        """
        Check if table exists in lakehouse.
        
        Args:
            table_name: Name of the table
            
        Returns:
            bool: True if table exists
        """
        try:
            table_directory = f"{lakehouse_name}.Lakehouse/Tables/dbo/{table_name}"
            directory_client = self.file_system_client.get_directory_client(table_directory)
            print(f'table {table_directory} exists: {directory_client.exists()}')
            return directory_client.exists()
        except Exception:
            return False

    def create_datastore_table_name(self, lakehouse, data_subcat: str, data_contents: str, date_part = datetime.now().strftime('%Y-%m-%d')):
        """
        This function will build the table name based on the data subcategory, data contents and date provided in a set structure
        Args:
            lakehouse: str - the lakehouse name must be one of the following e.g. bronze, silver, gold, sandbox
            data_subcat: str - the data subcategory e.g. rtd, pain_medication, loans, etc
            data_contents: str - the data contents e.g. raw, processed, cleansed
        
        returns:
            table_name: str - the constructed table name
        """
        if lakehouse not in self.lakehouse_list:
            raise ValueError(
                f"Lakehouse '{lakehouse}' not found. Lakehouse may not exist or you may not have access. "
                f"Must match one of: bronze, silver, gold, sandbox"
            )
        
        # set lakehouse as global variable
        self.lakehouse = lakehouse
        
        # set table name
        self.table_name = f"{data_subcat}_{data_contents}" #_{formatted_date}" # OMIT Date in favour of appending data
        return self.lakehouse, self.table_name
    
    
    def create_current_view_tables(self):
        ''' TBD '''
        return 
    
    
    def list_tables_in_lakehouse(self,lakehouse_name: str) -> list:
            """
            List all tables in the lakehouse.
            
            Returns:
                list: List of table names
            """
            try:
                tables_path = f"{lakehouse_name}.Lakehouse/Tables"
                paths = self.file_system_client.get_paths(path=tables_path)
                
                tables = []
                for path in paths:
                    if path.is_directory:
                        table_name = path.name.split('/')[-1]
                        # Exclude system tables
                        if not table_name.startswith('_'):
                            tables.append(table_name)
                
                return tables
            except Exception as e:
                print(f"Error listing tables: {e}")
                return []
            
    def delete_table(
        self, 
        lakehouse_name: str, 
        table_name: str, 
        confirm: bool = False
    ) -> bool:
        """
        Delete a table from the lakehouse.
        
        Args:
            table_name: Name of the table to delete
            confirm: If False, will prompt for confirmation
            
        Returns:
            bool: True if deletion successful
        """
        # Check if table exists
        if not self.check_a_datastore_table_exists(lakehouse_name,table_name):
            print(f"✗ Table '{table_name}' does not exist in lakehouse '{lakehouse_name}'")
            return False
        
        # Confirm deletion
        
        if not confirm:
            response = input(f"Are you sure you want to delete table '{table_name}'? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Deletion cancelled.")
                return False
        
        
        try:
            # Construct path to table directory
            table_directory = f"{lakehouse_name}.Lakehouse/Tables/dbo/{table_name}"
            
            print(f"Deleting table: {table_directory}")
            
            # Get directory client
            directory_client = self.file_system_client.get_directory_client(table_directory)
            
            # Delete the entire directory (recursively)
            directory_client.delete_directory()
            
            print(f"✓ Successfully deleted table '{table_name}'")
            return True
            
        except Exception as e:
            print(f"✗ Error deleting table '{table_name}': {str(e)}")
            raise

    def validate_workspace(self, workspace_name: str) -> None:
        """
        Validate if workspace exists in the list of available workspaces.
        
        Args:
            workspace_name: Name of workspace to validate
            workspaces: List of available workspace names
            
        Raises:
            ValueError: If workspace not found in list
        """
        if workspace_name not in self.workspaces:
            raise ValueError(
                f"Workspace '{workspace_name}' not found. Workspace may not exist or you may not have access. "
                f"Must match one of: {', '.join(self.workspaces)}"
                )
        else:
            print(f'Operating in the {workspace_name} workspace')

    def load_table_to_lakehouse(self,df: pd.DataFrame, delete_old_table = False):
        '''
        Will take a given dataframe and table name and save this into a Fabric Lakehouse under TABLE.
        
        NOTE: the user will need to run 'datastore_table_name' first to deffine the table name being used and unsure that this is standardised 
        
        inputs:
        df - the dataframe for migration
        delete_old_table - if you need to delete the old table (if the schema's don't match for example)

        NOTE: dataframe needs consistent data types to work
        '''
        
        try:
            table_name = self.table_name
            lakehouse_name = self.lakehouse
            
            # Construct the Delta table path
            table_path = f"abfss://{self.FABRIC_WORKSPACE_NAME}@{self.FABRIC_ACCOUNT_NAME}.dfs.fabric.microsoft.com/{lakehouse_name}.lakehouse/Tables/dbo/{table_name}"
            print(f'saving to: {table_path}')
        except:
            print("table name or lakehouse not set - run datastore_table_name function first")
            
        if delete_old_table == True:
            self.delete_table(lakehouse_name, table_name, True)
            self.logger.info(f"Deleted the original table: {lakehouse_name}.lakehouse/Tables/dbo/{table_name}")
            
            
        # Add the load_date column 
        date_part = datetime.now().strftime('%Y-%m-%d')
        formatted_date = date_part.replace('-', '')  # Convert to '20241201' 
        df['load_date'] = formatted_date
        df['load_dttm'] = datetime.now()
        
        # Convert to PyArrow Table explicitly
        arrow_table = pa.Table.from_pandas(df)  
        self.logger.info(f"Successful conversion of dataframe into delta format")  

        # check for existing table 
        table_exist_condition = self.check_a_datastore_table_exists(lakehouse_name,table_name)
        
        if table_exist_condition == True:
            print('Appending to existing table')
            self.logger.info(f"Appending to existing table: {lakehouse_name}.lakehouse/Tables/dbo/{table_name}")
            # Write PyArrow table as Delta (append mode)
            write_deltalake(
                table_path,
                arrow_table,
                mode="append",  # Changed from "overwrite" to "append"
                storage_options={
                    "bearer_token": self.token.token,
                    "use_fabric_endpoint": "true"
                }
            )
            self.logger.info(f"Successfully appended {len(df)} rows to table")
                        
        elif table_exist_condition == False:
            print('Creating new table')
            self.logger.info(f"Create new table: {lakehouse_name}.lakehouse/Tables/dbo/{table_name}")
            # Write PyArrow table as Delta
            write_deltalake(
                table_path,
                arrow_table,  # Use arrow_table instead of df
                mode="overwrite",
                storage_options={
                    "bearer_token": self.token.token,
                    "use_fabric_endpoint": "true"
                }
            )
            self.logger.info(f"✓ Delta table created successfully with {len(df)} rows")
            
    def read_table_from_lakehouse(self, lakehouse_name: str, table_name: str):
        '''
        Read a Delta table from a Fabric Lakehouse into a pandas DataFrame. 
        '''
        
        # check for existing table 
        table_exist_condition = self.check_a_datastore_table_exists(lakehouse_name,table_name)
        
        
        if table_exist_condition == True:
        
            # Construct the Delta table path
            table_path = f"abfss://{self.FABRIC_WORKSPACE_NAME}@{self.FABRIC_ACCOUNT_NAME}.dfs.fabric.microsoft.com/{lakehouse_name}.lakehouse/Tables/dbo/{table_name}"
            print(f'reading from: {table_path}')    
            # Read Delta table
            dt = DeltaTable(
                table_path,
                storage_options={
                    "bearer_token": self.token.token,
                    "use_fabric_endpoint": "true"
                }
            )
            self.logger.info(f"Successfully read table from {table_path}")
            # Convert to pandas DataFrame
            return dt.to_pandas()
        
        elif table_exist_condition == True:
            print(f'WARNING: {lakehouse_name}.lakehouse/Tables/dbo/{table_name} does not exist!')
            
            
        
    def read_file_from_lakehouse(self, lakehouse_name: str, file_name: str):
        '''
        Read a file from a Fabric Lakehouse Files location into a pandas DataFrame.
        '''
        # Construct the file path
        lakehouse_path = f"{lakehouse_name}/Files/{file_name}"
        #print(lakehouse_path)
        
        # Get the file client
        file_client = self.file_system_client.get_file_client(lakehouse_path)
        
        # Download the file content
        download = file_client.download_file()
        file_bytes = download.readall()        
        
        # Read into pandas based on file type
        if file_name.endswith(('.xlsx', '.xls')):
            return pd.ExcelFile(io.BytesIO(file_bytes))
        elif file_name.endswith('.csv'):
            return pd.read_csv(io.BytesIO(file_bytes))
        elif file_name.endswith('.sav'):  # readign SPSS files (.sav) -  UNTESTED - likely doesn't work
            df_pandas, meta = pyreadstat.read_sav(lakehouse_path)
            return df_pandas, meta
        
        else:
            raise ValueError(f"Unsupported file type: {file_name}")
                

    def list_accessible_lakehouses(self):
        """List all lakehouses (file systems) accessible via ADLS endpoint"""
        
        try:
            # List all file systems (lakehouses)
            file_systems = self.service_client.list_file_systems()
            
            lakehouses = []
            workspaces = []
            
            for fs in file_systems:
                lakehouses.append({
                    'name': fs.name,
                    'last_modified': fs.last_modified,
                    'metadata': fs.metadata
                })
                
                workspaces.append(fs.name)  
                
            # Usage
            if lakehouses:
                print(f"Found {len(lakehouses)} accessible lakehouses:\n")
                for lh in lakehouses:
                    print(f"Name: {lh['name']}")
                    print(f"Last Modified: {lh['last_modified']}")
                    print("-" * 50)

            return lakehouses, workspaces

        except Exception as e:
            print(f"Error listing file systems: {e}")
            return None