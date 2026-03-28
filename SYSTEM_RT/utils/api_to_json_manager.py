import json
import os
from typing import Dict, List, Any, Union

def save_object_to_json_file(
    data: Union[Dict[str, Any], List[Any]],
    filename: str,
    directory: str = "json_output" 
) -> Union[str, None]:
    
    save_flag = os.getenv("SAVE_API_TO_JSON")
    
    if not (save_flag and save_flag.lower() == "true"):
        print("Feature flag 'SAVE_API_TO_JSON' is not set to 'true'. Skipping file save.")
        return None

    full_path = os.path.join(directory, filename)
    
    try:
        os.makedirs(directory, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"Successfully saved object data to: {full_path}")
        return full_path

    except TypeError as e:
        print(f"TypeError: The object contains items that are not JSON serializable. Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while writing to file: {e}")
        return None