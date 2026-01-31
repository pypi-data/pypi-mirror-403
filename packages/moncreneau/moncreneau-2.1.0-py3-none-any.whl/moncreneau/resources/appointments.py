from typing import List, Optional, Dict, Any


class Appointments:
    """Resource for managing appointments"""
    
    def __init__(self, http_client):
        self.http = http_client
    
    def create(
        self,
        department_id: int,
        date_time: str,
        name: str,
        external_user_id: Optional[str] = None,
        worker_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new appointment
        
        Args:
            department_id: ID of the department (integer)
            date_time: Appointment date and time (ISO 8601 format, e.g. '2026-02-15T10:00:00')
            name: Full name of the patient
            external_user_id: Your system's user identifier for tracking (optional)
            worker_id: ID of the staff member/worker (required only if department has showAdminsInBooking=true)
        
        Returns:
            Created appointment data including externalUserId if provided
        """
        data = {
            'departmentId': department_id,
            'dateTime': date_time,
            'name': name
        }
        
        if external_user_id is not None:
            data['externalUserId'] = external_user_id
        
        if worker_id is not None:
            data['workerId'] = worker_id
        
        return self.http.post('/appointments', data)
    
    def retrieve(self, id: str) -> Dict[str, Any]:
        """
        Retrieve an appointment by ID
        
        Args:
            id: Appointment ID
        
        Returns:
            Appointment data
        """
        return self.http.get(f'/appointments/{id}')
    
    def list(
        self,
        page: int = 0,
        size: int = 50,
        status: Optional[str] = None,
        department_id: Optional[str] = None,
        external_user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List appointments with pagination and filters
        
        Args:
            page: Page number (0-indexed)
            size: Number of items per page (max 100)
            status: Filter by status (SCHEDULED, COMPLETED, CANCELLED, etc.)
            department_id: Filter by department ID
            external_user_id: Filter by your external user ID
            start_date: Filter appointments after this date
            end_date: Filter appointments before this date
        
        Returns:
            Paginated list of appointments
        """
        params = {'page': page, 'size': size}
        
        if status:
            params['status'] = status
        if department_id:
            params['departmentId'] = department_id
        if external_user_id:
            params['externalUserId'] = external_user_id
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        
        return self.http.get('/appointments', params)
    
    def cancel(self, id: str) -> None:
        """
        Cancel an appointment
        
        Args:
            id: Appointment ID
        """
        self.http.delete(f'/appointments/{id}')
