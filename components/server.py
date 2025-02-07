from components.job_server import EditGPTJobServer
from components.history import EditGPTHistory

class EditGPTServer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EditGPTServer, cls).__new__(cls)

        return cls._instance
    
    def __init__(self):
        self.history = EditGPTHistory()
        self.jobs = EditGPTJobServer()
