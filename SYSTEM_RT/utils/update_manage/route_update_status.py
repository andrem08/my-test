from models import Update_route_status, db
from datetime import datetime

class ROUTE_UPDATE_STATUS:

    def get_all_as_json(self):
        records = Update_route_status.query.all()
        if not records:
            return []

        try:
            columns = [column.name for column in Update_route_status.__table__.columns]
        except AttributeError:
            print("Error: Could not inspect table columns.")
            return []
        
        json_array = []
        for record in records:
            row_dict = {}
            for col in columns:
                value = getattr(record, col, None)
                
                if isinstance(value, datetime):
                    value = value.isoformat()
                    
                row_dict[col] = value
            json_array.append(row_dict)
            
        return json_array