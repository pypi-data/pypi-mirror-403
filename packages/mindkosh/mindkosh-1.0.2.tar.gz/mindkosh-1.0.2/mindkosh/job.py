# Copyright (C) 2023 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

class Segment:
    def __init__(self):
        pass

class Job:
    def __init__(self, url, id, assignee, reviewer, status, time_spent, last_frame):
        self.url = url
        self.id = id
        self.assignee = assignee
        self.reviewer = reviewer
        self.status = status
        self.time_spent = time_spent
        self.last_frame = last_frame

    def __str__(self):
        return str(self.__dict__)

    def download_annotations(self, format, location):
        pass
