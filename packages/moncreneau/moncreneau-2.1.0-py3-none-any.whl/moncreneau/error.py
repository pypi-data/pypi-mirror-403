class MoncreneauError(Exception):
    """Base exception class for Moncreneau API errors"""
    
    def __init__(self, error_data, status_code):
        self.code = error_data.get('code', 'UNKNOWN_ERROR')
        self.message = error_data.get('message', 'An error occurred')
        self.status_code = status_code
        self.details = error_data.get('details')
        
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.code}] {self.message} (HTTP {self.status_code})"
