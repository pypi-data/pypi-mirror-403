import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from requests.exceptions import RequestException

load_dotenv()

def log(service_id: str, level: str, message: str, access_token: str):
    """Pushes the log to a service through LogArbor Logs API"""

    current_time_format_string = "%Y-%m-%d %H:%M:%S"
    current_datetime_object = datetime.now()

    try:
        log_json = {
            "service_id": service_id,
            "token": os.getenv("LOGARBOR_API_TOKEN"),
            "message": message,
            "level": level,
            "time": current_datetime_object.strftime(current_time_format_string),
            "user_id": access_token
        }


        response = requests.post(os.getenv("LOGARBOR_LOG_API"), json=log_json)

        if not response.status_code == 200 and not response.status_code == 202:
            return {"message": f"something went wrong at log api: {response.text}", "status": response.status_code}
    except RequestException as e:
        return {"message": f"An error occurred while accessing Log API: {e}", "status": 500}
    except Exception as e:
        return {"message": f"An error occurred during the log function: {e}", "status": 500}

