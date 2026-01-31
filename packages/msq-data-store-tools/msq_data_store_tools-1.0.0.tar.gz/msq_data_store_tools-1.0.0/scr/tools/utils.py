import pandas as pd
import os
import yaml
import requests
from datetime import datetime
import logging

# Setup logging for better debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_how_many_api_calls_are_left(SERP_API_KEY):
    # find out how many calls we have left
    URL = 'https://serpapi.com/account.json'
    RESP = requests.get(URL, params={'api_key': SERP_API_KEY}).json()
    HAVE_API_CALLS = RESP['plan_searches_left']    
    return HAVE_API_CALLS

# Min Max Function
def minmax(column):
    column_scored = ((column-min(column))/(max(column)-min(column))*100)+1
    return column_scored

def save_dataframe(df, filepath):
    """
    Save DataFrame to Excel file with error handling.
    
    Args:
        df (pd.DataFrame): DataFrame to save
        filepath (str): Path to save the file
    """
    try:
        df.to_excel(filepath, index=False)
        logger.info(f"Saved: {filepath}")
    except PermissionError:
        logger.warning(f"Permission denied when saving: {filepath}")
    except Exception as e:
        logger.error(f"Error saving {filepath}: {str(e)}")

def load_or_create_dataframe(filepath, columns=None):
    """
    Load existing DataFrame or create new one if file doesn't exist.
    
    Args:
        filepath (str): Path to Excel file
        columns (list, optional): Column names for new DataFrame
        
    Returns:
        pd.DataFrame: Loaded or new DataFrame
    """
    try:
        df = pd.read_excel(filepath, engine='openpyxl')
        logger.info(f"Loaded existing file: {filepath}")
        return df
    except FileNotFoundError:
        logger.info(f"File not found, creating new DataFrame: {filepath}")
        return pd.DataFrame(columns=columns or [])

def load_config(config_path="config.yaml"):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def setup_logger(log_dir="logs", log_prefix="amazon_reviews"):
    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)
    # Create a datetime-stamped log filename
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{log_prefix}_{date_str}.log"
    log_path = os.path.join(log_dir, log_filename)
    # Set up the logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    # Create file handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    # Create formatter and add to handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    # Add handler to logger
    logger.addHandler(file_handler)
    return logger   