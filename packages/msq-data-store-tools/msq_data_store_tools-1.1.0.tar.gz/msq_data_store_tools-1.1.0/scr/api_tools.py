
import requests

# pull functions from tools
from data_store_tools.tools.utils import setup_logger

class APITools:

    def __init__(self,
                 project_name: str,            
                 ):
        '''
        Wrapper for making API calls to Unwrangle with error handling and logging.
        '''
        # logging
        self.logger = setup_logger(log_prefix=project_name)

    def api_response(self, data, success:bool, error_message:str=None):
        """Wrapper for API response with success status and error info."""
        self.data = data
        self.success = success
        self.error_message = error_message  

        # Logging
        if success == False:
            self.logger.error(f"API Error: {error_message}")
        else:
            self.logger.info("API call successful")

        return data

    def make_call(self,
                  url:str, 
                  params:dict, 
                  timeout:int=30):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return self.api_response(data, True)
                except ValueError:
                    return self.api_response(None, False, "Invalid JSON response")
            else:
                return self.api_response(None, False, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            return self.api_response(None, False, f"Request timeout after {timeout}s")
        except requests.exceptions.ConnectionError:
            return self.api_response(None, False, "Connection error")
        except requests.exceptions.RequestException as e:
            return self.api_response(None, False, f"Request error: {str(e)}")
        except Exception as e:
            return self.api_response(None, False, f"Unexpected error: {str(e)}") 
