# Copyright (C) 2023 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

import os
import time
import requests
import logging
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
from json import JSONDecodeError

from .exceptions import AuthorizationError, NetworkError, InternalServerError, DataSetError, DatasetFileError, SubscriptionError
from .project import Project
from .task import Task
from .utils import DataSetProperty
from .core import CoreAPI, APIConfig
from .datasets.data_handler import DataSetUploader
from .datasets.helpers import verify_manifest, verify_resources, validate_related_file_extra, validate_user_cloud_manifest_file

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class BaseUrlSession(requests.Session):
    def __init__(self, base_url, retries=5, delay=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = base_url
        self.retries = retries
        self.delay = delay

    def request(self, method, url, *args, **kwargs):
        full_url = urljoin(self.base_url, url)
        attempt = 0
        while attempt < self.retries:
            try:
                response = super().request(method, full_url, *args, **kwargs)
                return response
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                attempt += 1
                if attempt < self.retries:
                    print(f"Error: {e}. Retrying {attempt}/{self.retries} in {self.delay} seconds...")
                    time.sleep(self.delay)
                else:
                    print("Max retries reached")
                    raise e
    
class Organization:
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)

    def __str__(self):
        return str(self.__dict__)         


class Client:
    def __init__(
        self,
        token='',
        verbose_output=True,
        server_host='app.mindkosh.com',
        server_port='80'
    ):

        self.token = token or os.environ.get("MK_SDK_TOKEN", None)
        self.server_host = server_host or os.environ.get("server_host", None)
        self.server_port = server_port or os.environ.get("server_port", None)
        self.https = False if server_host == 'localhost' else True
        self.verbose_output = verbose_output

        if not self.token:
            raise AuthorizationError("No Access token specified.")

        self.auth_header = {"Authorization": "Token " + self.token}

        base_url = f"https://{self.server_host}/api/v1/" if self.https else f"http://{self.server_host}:{self.server_port}/api/v1/"
        self.session = BaseUrlSession(base_url)
        self.session.headers.update(self.auth_header)

        self.api = CoreAPI(base_url)

        APIConfig(self.api, self.token, self.verbose_output,
                  self.session, self.auth_header)
        self.org = self._org()

    def _org(self):
        try:
            client_self = self.session.get(self.api.users_self)
            client_self.raise_for_status()
            client_self_json = client_self.json()
            self.name, self._id = client_self_json['name'], client_self_json['account']['id']
            user_url = self.api.org_self
            response = self.session.get(user_url)
            response.raise_for_status()
            return Organization(response.json())
        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection Error")
        except requests.exceptions.RequestException as e:
            if response.status_code == requests.codes.unauthorized:
                raise AuthorizationError(response.json()['code'])
            if response.status_code == requests.codes.internal_server_error:
                raise InternalServerError("Internal Server Error")
            raise e

    def _post(self, url, payload={}):
        try:
            response = self.session.post(
                url,
                json=payload
            )
            if response.status_code in (requests.codes.created,requests.codes.ok):
                return response.json()
            if response.status_code == requests.codes.bad_request:
                raise Exception(response.json())
            if response.status_code == requests.codes.not_found:
                raise Exception('dataset_id not found')
            response.raise_for_status()
            return response
        except JSONDecodeError:
            return response.text
        except requests.exceptions.RequestException as e:
            raise e

    def _get_all(self, url, max_pages=500):
        data = []
        sep = '?' if '?' not in url else '&'
        for page in range(1, max_pages+1):
            url_page = f'{url}{sep}page={page}'
            try:
                response = self.session.get(url_page)
                response.raise_for_status()
                response_json = response.json()
                for result in response_json['results']:
                    data.append(result)

                if not response_json['next']:
                    break
            except requests.exceptions.RequestException as e:
                raise e
        return data

    @property
    def task(self):
        return Task

    @property
    def project(self):
        return Project

    def pfp(self):
        """Shows user profile picture"""
        response = self.session.get(self.api.pfp(self._id))
        if response.status_code != 200:
            raise Exception(response.text)
        Image.open(BytesIO(response.content)).show(title=self.name)
    
    def update_pfp(self,file_path):
        """Updated user profile picture"""
        file_name = os.path.split(file_path)[1]
        if not os.path.exists(file_path) or not file_name.endswith(('.jpg','.png','.jpeg')):
            raise Exception('Invalid file_path or file extension')
        response = self.session.post(url=self.api.update_pfp,files=[('file',(file_name, open(file_path, 'rb'), 'image/jpeg'))])
        if response.status_code != 200:
            raise Exception(response.text)
        print('profile picture udpated')

    def update_tags(
        self,
        dataset_id: int,
        datasetfile_ids: list = [],
        add: list = [],
        remove: list = [],
        all: bool = False
    ) -> bool:
        """
        Add/Remove tags to given `datasetfile_ids` for a dataset.
        Update tags for all dataset files for given dataset_id if `all=True`
        :param dataset_id: dataset id.
        :param datasetfile_ids: list of dataset file ids.
        :param add: list of tags to be added.
        :param remove: list of tags to be removed.
        :param all: `True` to update tags for entire dataset else `False`.
        Returns True if tags were successfully updated else throws error.
        """
        url = self.api.dataset_files_tags()
        payload = {
            'dataset_id' : dataset_id,
            'datasetfile_ids' : datasetfile_ids,
            'add' : add,
            'remove' : remove,
            'all' : all
        }

        self._post(url,payload)
        return True


    def create_dataset(
        self,
        name: str,
        data_type: str,
        location: str = None,
        **kwargs
    ) -> dict:
        """
        Creates a dataset using storage method `vk_cloud`.

        :param name: a valid dataset name.
        :param data_type: any of `image`, `video`, and `pointcloud`
        :param location: default location - `ap-south-1`

        Returns a json response of dataset created
        """

        data_type = DataSetProperty.DataType(data_type).value

        location = location or DataSetProperty.DEFAULT_BUCKET_REGION
        url = self.api.datasets_storage_method('vk_cloud')
        payload = {
            "name": name,
            "data_type": data_type,
            "location": location
        }

        return self._post(url, payload)

    def create_dataset_from_cloud_data(
            self,
            name: str,
            data_type: str,
            resource: str,
            directory: str,
            location: str = 'ap-south-1'
    ):
        data_type = data_type.lower()
        data_type = DataSetProperty.DataType(data_type).value
        
        cloud_service_type = 'aws'
        location = location or DataSetProperty.DEFAULT_BUCKET_REGION
        url = self.api.datasets_storage_method('user_cloud')
        payload = {
            "name": name,
            "data_type": data_type,
            "location": location,
            "resource": resource,
            "directory": directory,
            "cloud_service_type": cloud_service_type
        }

        try:
            response = self.session.post(
                url=url,
                data=payload
            )
            if response.status_code == requests.codes.created:
                print('Dataset created')
                return response.json()
        except requests.exceptions.RequestException as e:
            raise e

    
    def scan_user_cloud(
            self,
            dataset_id: int,
            manifest_file_path: str = None
        ):
        """
        Scan user cloud data with or without manifest file.
        """
        files = []
        if manifest_file_path:
            data_type = self._get_data_type(dataset_id)
            validate_user_cloud_manifest_file(manifest_file_path, data_type)
            files=[('manifest_file', (manifest_file_path, open(manifest_file_path,'rb'), 'application/json'))]

        try:
            response = self.session.post(
                url=self.api.scan_user_cloud(dataset_id),
                data={}, files=files
            )
            if response.status_code == requests.codes.accepted:
                status_api = self.api.scan_user_cloud_status(response.json()['job_id'])
                wait_time = 0
                while wait_time < 60:
                    res = self.session.get(status_api)
                    res_json = res.json()
                    state = res_json['state'].lower()
                    if state == 'finished':
                        msg = 'Files have been successfully scanned'
                        logger.info(msg)
                        return msg
                    elif state == 'failed':
                        raise Exception(f"Exception occured while scanning files. {res_json['message']}")
                    wait_time += 2
                    time.sleep(2)
                msg = 'Files are being scanned. Please wait for some time and check again'
                logger.info(msg)
                return msg
            
            elif response.status_code == requests.code.bad_request:
                raise Exception(response.text)
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            raise e


    def get_datasets(
        self,
        dataset_id: int = None,
        storage_method: str = None,
        **kwargs
    ):
        """
        Returns a list of all the datasets or a particular dataset.

        :param dataset_id: to get the particular dataset.
        :param storage_method: to get datasets from particular storage method. Valid storage
        methods : `vk_cloud` and `user_cloud`.

        """
        url = self.api.datasets
        if dataset_id:
            try:
                response = self.session.get(
                    url=url + '/' + str(dataset_id)
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                raise e

        if storage_method:
            storage_method = DataSetProperty.StorageMethod(storage_method).value
            url += f'?storage_method={storage_method}'

        datasets = self._get_all(url)
        return datasets

    def delete_dataset(
        self,
        dataset_id: int
    ) -> None:
        """
        Deletes a dataset including all of it's data.

        :param dataset_id: id of the dataset to be deleted.

        Returns : None
        """
        url = self.api.datasets_id(dataset_id)

        try:
            response = self.session.delete(url=url)
            if response.status_code == requests.codes.accepted or response.status_code == requests.codes.no_content:
                print(f"Dataset with ID {dataset_id} deleted")
                return
            raise Exception(response.json())

        except requests.exceptions.RequestException as e:
            raise e

    def get_dataset_files(
        self,
        dataset_id: int,
        max_files: int = 50,
        **kwargs
    ) -> list:
        """
        Returns list of files(id, name, size) attached to the dataset.

        :param dataset_id: dataset_id.
        :param max_files: A multiple of 10. 0 < max_files <= total number of files attached to the dataset.  
        """
        assert isinstance(max_files, int)

        max_pages = max_files//10 or 1
        url = self.api.list_dataset_files(dataset_id)
        files = self._get_all(url, max_pages)

        return files

    def delete_files_from_dataset(self, dataset_id: int, delete_all: bool = False, file_ids: list = [], **kwargs) -> None:
        """
        :param dataset_id: dataset_id
        :delete_all: Deletes all the files from given dataset_id
        :file_ids: List of files ids from given dataset_id

        Returns : None
        """
        url = self.api.delete_files_from_dataset(dataset_id)
        payload = None
        if delete_all:
            url = url + '?all=true'
        else:
            if not file_ids or not all(isinstance(file_id, int) for file_id in file_ids):
                raise Exception('file_ids should be a list of integer valuesss')
            payload = {"files": [file_ids]}
        try:
            response = self.session.delete(
                url=url,
                data=payload
            )
            if response.status_code in (requests.codes.accepted,requests.codes.no_content):
                logger.warning(f"files deleted from dataset_id {dataset_id}")
                #TODO:Update files count for client.org
                return
            raise Exception(response.text)
        except requests.exceptions.RequestException as e:
            raise e

    def download_dataset_files(self, dataset_id: int, file_ids: list, save_files_dir: str, **kwargs):
        """
        Downloads dataset files for given dataset_id and file_ids.

        :param dataset_id: dataset_id.
        :file_ids: list of valid file ids that belong to given dataset_id.
        :save_files_dir: local dir path where to save downloaded files.
        """
        if not isinstance(file_ids,list) or len(file_ids)>50:
            raise Exception('file_ids should be a list of valid 50 or less file ids')

        url = self.api.download_dataset_files(dataset_id)
        payload = {"files": file_ids}
        page = 1
        files_downloaded = 0

        while True:
            try:
                url_page = f'{url}?page={page}'
                response = self.session.post(
                    url_page, data=payload)
                response.raise_for_status()
                response = response.json()
                for result in response['results']:
                    name = result['name']
                    presigned_url = result['presigned_url']

                    file_response = self.session.get(presigned_url)
                    file_response.raise_for_status()
                    with open(os.path.join(save_files_dir, name), "wb") as f:
                        f.write(file_response.content)
                        files_downloaded += 1
                        print(f"{files_downloaded} : {name}", end="\r")

                if not response['next']:
                    break
                page += 1

            except requests.exceptions.RequestException as e:
                raise e
        print('\nTotal files downloaded : ', files_downloaded)


    def upload_dataset_files(
            self,
            dataset_id: int,
            resources: list = [],
    ) -> None:
        """
         - Creates a batch and uploads local data to a dataset.
         - Accepts tags and meta data for each file as well
         - Prints the status of image transformations if manifest file is mentioned. 
         - Prints number of files have been uploaded and attached to the given dataset_id.

         Parameters
        ----------

         - `dataset_id`: id of the dataset where to upload the data.
         - `resouces`: A list of local directories or/and files.
        """

        data_type = self._get_data_type(dataset_id)
        if resources:
            for dataset_file in resources:
                if(type(dataset_file).__name__ != "DatasetFile"):
                    raise Exception(
                "resources should be of type DatasetFile")
        else:
            raise Exception(
                "resources or manifest file is required to create dataset")

        num_of_files = len(resources)
        if num_of_files == 0:
            raise Exception("No data to be uploaded")

        batch_key = self._create_dataset_batch(dataset_id)
        file_upload_url = self.api.cloud_data_action('file-upload')
        stream_url = self.api.dataset_upload_status(dataset_id, batch_key)

        logger.warning(f"{num_of_files} files to be uploaded \n")

        uploader = DataSetUploader(
            dataset_id, batch_key, file_upload_url, stream_url, self.auth_header)
        uploader.files_upload_thread(raw_filepaths=resources)

    
    def upload_data(
            self,
            dataset_id: int,
            tags: list = [],
            extra: dict = {},
            resources: list = [],
            recursive: bool = False,
            manifest_file: str = None,
            save_files_dir: str = None,
            **kwargs

    ) -> None:
        """
         - Creates a batch and uploads local data to a dataset. 
         - Prints the status of image transformations if manifest file is mentioned. 
         - Prints number of files have been uploaded and attached to the given dataset_id.

         Parameters
        ----------

         - `dataset_id`: id of the dataset where to upload the data.
         - `resouces`: A list of local directories or/and files.
         - `recursive`: True to upload the data from given directories recursively. Not valid for manifest file.
         - `manifest`: Absolute local path of the manifest file.
         - `save_files_dir`: Local path where to save transformed images mentioned in manifest file.

         Note - `manifest_file` is only valid for .jpg, .png and .jpeg files.
        """

        data_type = self._get_data_type(dataset_id)
        if resources:
            files_to_upload = verify_resources(
                resources, recursive, category=data_type
            )
        elif manifest_file:
            files_to_upload = verify_manifest(
                manifest_file, save_files_dir, dataset_id, category=data_type
            )
        else:
            raise Exception(
                "resources or manifest file is required to create dataset")

        num_of_files = len(files_to_upload)
        if num_of_files == 0:
            raise Exception("No data to be uploaded")

        self._validate_incoming_storage(data_type, num_of_files)
        batch_key = self._create_dataset_batch(dataset_id)
        file_upload_url = self.api.cloud_data_action('file-upload')
        stream_url = self.api.dataset_upload_status(dataset_id, batch_key)

        logger.warning(f"{num_of_files} files to be uploaded \n")

        uploader = DataSetUploader(
            dataset_id, batch_key, file_upload_url, stream_url, self.auth_header, data_type)
        files_uploaded = uploader.files_upload_thread(raw_filepaths=files_to_upload, tags=tags, extra=extra)
        self._update_files_count(files_uploaded,data_type)

    def upload_imagefiles(
            self,
            dataset_id: int,
            imagefiles,
            **kwargs

    ) -> None:
        """
         - Creates a batch and uploads local data to a dataset. 
         - Prints number of files have been uploaded and attached to the given dataset_id.

         Parameters
        ----------

         - `dataset_id`: id of the dataset where to upload the data.
         - `imagefiles`: A list of `mindkosh.ImageFile` objects.
         
        """

        sub = self.org.subscription
        max_size = sub['values']['image']['max_size'] if sub else 10 * 10**8
        incoming_storage = 0
        invalid_files = 0
        sequence_set = []
        for imagefile in imagefiles:
            if type(imagefile).__name__ != "ImageFile":
                raise DatasetFileError("imagefiles: Invalid list of mindkosh.ImageFile objects")
            if imagefile._size > max_size:
                invalid_files += 1
            incoming_storage += imagefile._size
            sequence_set.append(imagefile.sequence)

        if len(sequence_set) != len(set(sequence_set)):
            raise DatasetFileError("Duplicate sequence values found")
        if invalid_files:
            raise SubscriptionError(f"{invalid_files} files are larger than max_size limit for current subscription plan")
        
        num_of_files = len(imagefiles)
        if num_of_files == 0:
            raise Exception("No data to be uploaded")
        
        data_type = self._get_data_type(dataset_id)
        self._validate_incoming_storage(data_type, num_of_files, incoming_storage)
        if data_type != DataSetProperty.DataType.IMAGE.value:
            raise DataSetError('Invalid dataset type')

        batch_key = self._create_dataset_batch(dataset_id)
        file_upload_url = self.api.cloud_data_action('file-upload')
        stream_url = self.api.dataset_upload_status(dataset_id, batch_key)

        logger.warning(f"{num_of_files} files to be uploaded \n")

        uploader = DataSetUploader(
            dataset_id, batch_key, file_upload_url, stream_url, self.auth_header, data_type)
        files_uploaded = uploader.files_upload_thread(imagefiles=imagefiles)
        self._update_files_count(files_uploaded,data_type)
    

    def _upload_basefiles(self, dataset_id, data_type, basefiles):
        sub = self.org.subscription
        max_image_size = sub['values']['image']['max_size'] if sub else 5 * 10**8
        incoming_storage, invalid_files = 0, 0
        related_imagefiles = []

        if data_type==DataSetProperty.DataType.POINTCLOUD.value:
            basefile_class = "PointCloudFile" 
            max_basefile_size = sub['values']['pointcloud']['max_size'] if sub else 5 * 10**8
        elif data_type==DataSetProperty.DataType.IMAGE.value:
            basefile_class = "MainImage"
            max_basefile_size = max_image_size
        else:
            raise Exception("invalid data type")

        for basefile in basefiles:
            if type(basefile).__name__ != basefile_class:
                raise DatasetFileError(f"Invalid list of {basefile_class} objects")
            for related_file in basefile.related_files:
                incoming_storage += related_file._size
                if related_file._size > max_image_size:
                    invalid_files += 1
            if basefile._size > max_basefile_size:
                invalid_files += 1
            incoming_storage += basefile._size
            related_imagefiles.extend(basefile.related_files)
        if invalid_files:
            raise SubscriptionError(f"{invalid_files} files are larger than max_size limit for current subscription plan")
    
        self._validate_incoming_storage(data_type, len(basefiles), incoming_storage)
        batch_key = self._create_dataset_batch(dataset_id)
        file_upload_url = self.api.cloud_data_action('file-upload')
        stream_url = self.api.dataset_upload_status(dataset_id, batch_key)

        uploader = DataSetUploader(
            dataset_id, batch_key, file_upload_url, stream_url,
            self.auth_header, data_type
        )
        
        if related_imagefiles:
            self._validate_incoming_storage('image', len(related_imagefiles), incoming_storage)
            logger.warning(f"Uploading {len(related_imagefiles)} related files")
            files_uploaded = uploader.files_upload_thread(imagefiles=related_imagefiles)
            uploader.event.clear()
            self._update_files_count(files_uploaded,DataSetProperty.DataType.IMAGE)
            time.sleep(10)

        logger.warning(f"Uploading {len(basefiles)} {basefile_class.lower()}s")
        files_uploaded = uploader.files_upload_thread(basefiles=basefiles)
        self._update_files_count(files_uploaded,data_type)


    def upload_mainimages(
            self,
            dataset_id: int,
            rgbfiles: list,
            **kwargs
    ) -> None:
        """
        Uploads mindkosh.MainImage files along with/without their related files.
        """
        data_type = self._get_data_type(dataset_id)
        if data_type != DataSetProperty.DataType.IMAGE.value:
            raise DataSetError('Invalid dataset type')    
        self._upload_basefiles(dataset_id, data_type, rgbfiles)


    def upload_pointcloud_data(
            self,
            dataset_id,
            pointcloudfiles,
            **kwargs
    ) -> None:
        """
        Uploads mindkosh.PointCloud files along with/without their related files.
        """
        data_type = self._get_data_type(dataset_id)
        if data_type != DataSetProperty.DataType.POINTCLOUD.value:
            raise DataSetError('Invalid dataset type')  
        self._upload_basefiles(dataset_id, data_type, pointcloudfiles)


    def _get_data_type(self, dataset_id):
        """Returns data_type of a dataset"""
        dst = self.session.get(
            url=self.api.datasets_id(dataset_id)
        )
        if dst.status_code == requests.codes.not_found:
            raise Exception('dataset_id not found')
        dst.raise_for_status()
        return dst.json()['data_type']

    def _create_dataset_batch(self, dataset_id):
        """Returns : batch_key"""
        response = self._post(self.api.datasets_batch(),
                              payload={'dataset_id': dataset_id})
        return response['batch_key']
    
    def _update_files_count(self, files_uploaded, data_type):
        # TODO: refresh client.org.subscription instead of using this
        if isinstance(data_type, DataSetProperty.DataType):
            data_type = data_type.value
        key = data_type + 's_count' 
        value = getattr(self.org, key)
        setattr(self.org, key, value + files_uploaded)
    
    def _validate_incoming_storage(self, data_type, incoming_files, incoming_storage=0):
        sub = self.org.subscription
        if sub:
            if data_type == DataSetProperty.DataType.IMAGE.value:
                files = self.org.images_count
            elif data_type == DataSetProperty.DataType.POINTCLOUD.value:
                files = self.org.pointclouds_count
            elif data_type == DataSetProperty.DataType.VIDEO.value:
                files = self.org.videos_count
            else:
                raise DataSetError('Invalid data type')

            if files + incoming_files > sub['values'][data_type]['max_files']:
                raise SubscriptionError(f'Organization has exhausted the maximum number of {data_type}s allowed under current Subscription plan')

            if incoming_storage and self.org.storage_consumed_in_bytes + incoming_storage > sub['values']['max_storage']:
                raise SubscriptionError('Organization has exhausted the maximum storage allowed under current Subscription plan')

