"""
Models for dashboard display.
"""

class QueueStats:
    def __init__(self):
        self.hosts = dict()
        self.workers = set()
    
    def dict(self):
        return dict(
            hosts = self.hosts,
            workers = list(self.workers)
        )
