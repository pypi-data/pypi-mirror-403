# Copyright (C) 2023 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

from .task import Task, Frame, PointCloud
from .project import Project
from .annotations.testset import TestSet


class APIConfig():
    def __init__(self, api, token, verbose_output, session, auth_header):
        self.api = api
        self.token = token
        self.verbose_output = verbose_output
        self.session = session
        self.auth_header = auth_header
        self.client = type("Client", (object,), {
                           "api": self.api, "auth_header": self.auth_header, "session": self.session, "verbose_output": self.verbose_output})
        Project.client = self.client
        Task.client = self.client
        TestSet.client = self.client
        Frame.client = self.client
        PointCloud.client = self.client


class CoreAPI():

    """ Build parameterized API URLs """

    def __init__(self, base_url):
        self.base_url = base_url

    """ Project API calls """

    @property
    def projects(self):
        return 'projects'

    def projects_id(self, project_id):
        return f"{self.projects}/{project_id}"

    def project_tasks(self, project_id):
        return f"{self.projects_id(project_id)}/tasks"

    """ User API calls """

    @property
    def users_self(self):
        return 'users/self'
    
    @property
    def update_pfp(self):
        return f"{self.users_self}/update-pfp"
    
    def pfp(self, user_id):
        return f"users/{user_id}/pfp"
    
    """ Organization API calls """

    @property
    def org_self(self):
        return 'organizations/self'

    """ Task API calls """

    @property
    def tasks(self):
        return "tasks"

    def tasks_page(self, page_id):
        return f"{self.tasks}?page={page_id}"

    def tasks_id(self, task_id):
        return f"{self.tasks}/{task_id}"

    def jobs_for_a_task(self, task_id):
        return f"{self.tasks}/{task_id}/jobs"

    def comments(self):
        return f"comments"

    def task_data_meta(self):
        return f"task-data/meta"

    def task_data_frames(self, task_id, limit, search, download):
        search = search if search else ''
        return f"task-data/frames?task_id={task_id}&limit={limit}&search={search}&download={download}"

    def frame_annotations(self, task_id, frame_ids):
        return f"{self.tasks}/{task_id}/annotations?frame_ids={frame_ids}"

    def tasks_status(self, job_id):
        return f"{self.tasks}/status?job_id={job_id}"

    def tasks_id_annotations_format(self, task_id, fileformat):
        return f"{self.tasks_id(task_id)}/annotations?format={fileformat}"

    def tasks_id_annotations(self, task_id, public_url, fileformat):
        if public_url:
            return f"{self.tasks_id(task_id)}/annotations?format={fileformat}&webhook_url={public_url}"
        return f"{self.tasks_id(task_id)}/annotations?format={fileformat}"

    """Releases"""

    def releases(self, task_id):
        return f'releases?task_id={task_id}'

    def release_id(self, release_id):
        return f'releases/{release_id}'

    def download_release(self, release_id):
        return f'{self.release_id(release_id)}?action=download'
    

    """ Issue api calls """

    def issues(self):
        return f"issues"
    
    def export_issues(self):
        return f"{self.issues()}/export-csv"
    
    def task_issues(self, task_id):
        return f"{self.issues()}?task={task_id}"

    def frame_issues(self, job_id, frame):
        return f"{self.issues()}?job={job_id}&frame={frame}"

    """ cloud api calls """

    @property
    def base_cloud_data(self):
        return f"cloud-data"

    def cloud_data_action(self, action):
        return f"{self.base_url}{self.base_cloud_data}?action={action}"

    """ Dataset api calls """

    @property
    def datasets(self):
        return f"datasets"

    def datasets_batch(self):
        return f"{self.datasets}/batch"

    def datasets_id(self, dataset_id):
        return f"{self.datasets}/{dataset_id}"

    def datasets_storage_method(self, storage):
        return f"{self.datasets}?storage_method={storage}"

    def dataset_upload_status(self, dataset_id, batch_key):
        return f"{self.base_url}{self.datasets}/{dataset_id}/upload-status?batch_key={batch_key}"

    def list_dataset_files(self, dataset_id):
        return f"dataset/files?dataset_id={dataset_id}"

    def download_dataset_files(self, dataset_id):
        return f"{self.datasets}/{dataset_id}/download"

    def download_dataset_file(self, datasetfile_id):
        return f"dataset/files/{datasetfile_id}/download"

    def delete_files_from_dataset(self, dataset_id):
        return f"{self.datasets}/{dataset_id}/delete-files"

    def dataset_delete_status(self, job_id):
        return f"{self.datasets}/delete-status?job_id={job_id}"

    def dataset_files_tags(self):
        return f"dataset/files/tags"
    
    def scan_user_cloud(self, dataset_id):
        return f"{self.datasets_id(dataset_id)}/scan-user-cloud"
    
    def scan_user_cloud_status(self, job_id):
        return f"{self.datasets}/scan-user-cloud-status?job_id={job_id}"

    """misc"""

    @property
    def tags(self):
        return f"tags"
