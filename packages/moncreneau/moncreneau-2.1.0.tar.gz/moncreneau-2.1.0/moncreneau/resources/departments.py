from typing import List, Dict, Any


class Departments:
    """Resource for managing departments"""
    
    def __init__(self, http_client):
        self.http = http_client
    
    def list(self) -> List[Dict[str, Any]]:
        """
        List all departments
        
        Returns:
            List of departments
        """
        return self.http.get('/departments')
    
    def retrieve(self, id: str) -> Dict[str, Any]:
        """
        Retrieve a department by ID
        
        Args:
            id: Department ID
        
        Returns:
            Department data
        """
        return self.http.get(f'/departments/{id}')
    
    def get_availability(
        self,
        id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get availability for a department
        
        Args:
            id: Department ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Availability data with slots
        """
        params = {
            'startDate': start_date,
            'endDate': end_date
        }
        return self.http.get(f'/departments/{id}/availability', params)
