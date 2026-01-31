# Copyright (C) 2023 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

import requests
import random

class Issue:
    def __init__(
        self,
        name,
        job,
        frame,
        position,
        **kwargs
    ):
        self.name = name
        self.job = job
        self.frame = frame
        self.position = position
        if 'id' in kwargs:
            self.id = kwargs['id']
        if 'created_date' in kwargs:
            self.created_date = kwargs['created_date']
        if 'comments' in kwargs:
            comments = kwargs['comments']
            self.comments = [Comment(comment) for comment in comments]
        if kwargs['annotation']:
            if kwargs['annotation']['type']=='shape':
                self.shape_id = kwargs['annotation']['id']
            else:
                self.track_id = kwargs['annotation']['id']

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.name

    @classmethod
    def get_frame_issues(cls,client,frame,job):     
        url = client.api.frame_issues(job, frame)
        page = 1
        issueobjects = []
        while True:
            try:
                url_page = f"{url}&page={page}"
                response = client.session.get(url_page)
                response.raise_for_status()
                response_json = response.json()
                for data in response_json['results']:
                    issueobjects.append(Issue(**data))

                page += 1
                if not response_json['next']:
                    break
            except requests.exceptions.HTTPError as e:
                raise e
        return issueobjects

    @classmethod
    def create_ticket(
        cls,
        client,
        frame,
        job,
        ticket_name,
        dimension='2d',
        shape_id = None,
        track_id = None,
        **kwargs
    ):
        """Issue can be created with or without attaching it to an annotation(shape or track). 
        Returns: Issue id"""

        if dimension == '3d':
            position = [0.0, 0.0]
        else:
            x1 = random.randint(1, 50)
            y1 = random.randint(1, 50)
            position = (0, 0, x1, y1)

        data = {
            "frame" : frame, 
            "job" : job, 
            "name" : ticket_name,
            "position" : position
        }

        if shape_id:
            data['annotation'] = {
                'type': 'shape', 'id':shape_id
            }           
        elif track_id:
            data['annotation'] = {
                'type': 'track', 'id':track_id
            }            
            
        response = client.session.post(
            url = client.api.issues(),
            json=data
        )
        if response.status_code ==  requests.codes.not_found:
            raise Exception(f"Annotation id {data['annotation']['id']} not found")
        response.raise_for_status()
        response = response.json()
        print(f"Issue added : {response['name']}, Frame : {response['frame']} ")
        return response['id']


class Comment:
    def __init__(self,data) -> None:
        self.id = data['id']
        self.message = data['message']
        self.auther = data['author']['name']

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.message
    

    @classmethod
    def add_comment(cls,client,issue_id,message):
        commentsurl = client.api.comments()
        data = {"issue":issue_id, "message":message}

        response = client.session.post(
            url = commentsurl,
            json = data,
            headers = client.auth_header
        )
        response.raise_for_status()
        if response.status_code == requests.codes.created:
            print(f'comment added on issue {issue_id}')