# Copyright (C) 2023 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

import requests

from .task import Task
from .utils import verify_name

class Project:
    def __init__(
        self,
        data
    ):
        self.project_id = data['id']
        self.name = data['name']
        self.description = data['description']
        self.status = data['status']

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.name

    def delete(self):
        """deletes the project.
            Deleting a project will also delete associated tasks with it.
        """
        url = self.client.api.projects_id(self.project_id)
        response = self.client.session.delete(url)
        try:
            response.raise_for_status()
            if self.client.verbose_output:
                print(f"Project id {self.project_id} deleted")
        except requests.exceptions.HTTPError as e:
            raise e

    def update_name(self, name):
        url = self.client.api.projects_id(self.project_id)

        name = verify_name(name, 'project')
        try:
            response = self.client.session.patch(
                url, data={'name': name}
            )
            response.raise_for_status()
            response_json = response.json()
            if self.client.verbose_output == True:
                print(
                    f"Name updated for project id {response_json['id']}. New name : {response_json['name']}")
                self.name = name
        except requests.exceptions.HTTPError as e:
            raise e

    def update_description(self, description):
        url = self.client.api.projects_id(self.project_id)
        try:
            response = self.client.session.patch(
                url,
                data={'description': description}
            )
            response.raise_for_status()
            response_json = response.json()
            if self.client.verbose_output == True:
                print(
                    f"Description updated for project id {response_json['id']}. New Description : {response_json['description']}")
                self.description = description
        except requests.exceptions.RequestException as e:
            raise e

    def tasks(self):
        """
        Returns list of task objects attached to the project
        """
        url = self.client.api.project_tasks(self.project_id)
        page = 1
        taskobjects = []
        while True:
            try:
                url_page = f"{url}?page={page}"
                response = self.client.session.get(url_page)
                response.raise_for_status()
                response_json = response.json()
                for data in response_json['results']:
                    taskobjects.append(Task(data))

                if not response_json['next']:
                    break
                page += 1

            except requests.exceptions.RequestException as e:
                raise e
        return taskobjects

    @classmethod
    def create(
        cls,
        name: str,
        description: str = None,
        **kwargs
    ):
        """ creates a new project.
            Args:
                name and descriptional
            Returns:
                `mindkosh.Project`
        """
        name = verify_name(name, 'project')
        url = cls.client.api.projects
        data = {
            "name": name,
            "description": description if description and set(description) != {' '} else None
        }
        try:
            response = cls.client.session.post(
                url, json=data
            )
            response.raise_for_status()
            response_json = response.json()
            print(
                f"New project created. id : {response_json['id']}, name : {response_json['name']}")
            return Project(response_json)

        except requests.exceptions.RequestException as e:
            raise e

    @classmethod
    def get(cls, project_id: int = None):
        """
        Returns list of all project objects if `project_id` is not None else return the selected project object
        """

        if project_id:
            url = cls.client.api.projects_id(project_id)
            try:
                response = cls.client.session.get(url)
                response.raise_for_status()
                return Project(response.json())
            except requests.exceptions.RequestException as e:
                raise e

        url = cls.client.api.projects
        page = 1
        projectobjects = []
        while True:
            try:
                url_page = f"{url}?page={page}"
                response = cls.client.session.get(url_page)
                response.raise_for_status()
                response_json = response.json()

                for data in response_json['results']:
                    projectobjects.append(Project(data))

                page += 1
                if not response_json['next']:
                    break
            except requests.exceptions.HTTPError as e:
                raise e

        return projectobjects
