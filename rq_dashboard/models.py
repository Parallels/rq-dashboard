"""
Models for dashboard display.
"""

class QueueStats:
    def __init__(self):
        self.hosts = set()
        self.workers = set()
    
    def dict(self):
        return dict(
            hosts = list(self.hosts),
            workers = list(self.workers)
        )