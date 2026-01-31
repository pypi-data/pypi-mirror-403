# Copyright (C) 2023 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

import os
import time
import json
import asyncio
import aiohttp
import threading
import requests
import logging
from PIL import Image
from typing import Union

from .utils import convert_image_to_bytes
from .helpers import DatasetFile

logger = logging.getLogger(__name__)


class DataSetUploader:
    def __init__(
        self,
        dataset_id: int,
        batch_key: str,
        file_upload_url: str,
        stream_url: str,
        headers: dict,
        data_type: str = 'image',
        sequence_starter: int = 1
    ):

        self.dataset_id = dataset_id
        self.batch_key = batch_key
        self.file_upload_url = file_upload_url
        self.stream_url = stream_url
        self.headers = headers
        self._data_type = data_type
        self._sequence = sequence_starter
        self.event = threading.Event()

    def _skip_file(self,
        message: dict
    ):
        """
        Returns prefixed filename and updates files count if the file is already uploaded.
        Throws error for other errors
        """
        try:
            prefixed_filename = message['filename'][-1]
        except KeyError:
            raise Exception(message)
        self._skipped += 1
        self._sequence += 1

        return prefixed_filename

    def _upload_single_file(
        self,
        datasetfile: Union[str, DatasetFile],
        tags: list,
        convert_tiff_to: str = '.png',
        extra: dict = {},
        **kwargs
    ):

        filepath = datasetfile
        if (type(datasetfile).__name__ == "DatasetFile"):
            filepath = datasetfile.filepath

        base_name = os.path.basename(filepath)
        file_name, extension = os.path.splitext(base_name)

        if extension == '.tiff':
            tiff_im = Image.open(filepath)
            im = tiff_im.convert("RGB")
            byte_im, file_size = convert_image_to_bytes(
                filepath, im, convert_tiff_to)
            base_name = file_name + convert_tiff_to
        else:
            byte_im = open(filepath, 'rb').read()
            file_size = os.path.getsize(filepath)

        data = {
            "dataset_id": self.dataset_id,
            "file_name": base_name,
            "file_size": file_size,
            "meta_data": {
                "batch_key": self.batch_key,
                "sequence": self._sequence
            }
        }

        if (type(datasetfile).__name__ == "DatasetFile"):
            if (datasetfile.tags):
                data['meta_data']['tags'] = datasetfile.tags
            if (datasetfile.extra):
                data['meta_data']['extra'] = datasetfile.extra
            if (datasetfile.related_files):
                data['meta_data']['related_files'] = datasetfile.related_files
        else:
            if tags:
                data['meta_data']['tags'] = tags
            if extra:
                data['meta_data']['extra'] = extra

        resp = requests.post(url=self.file_upload_url,
                             json=data, headers=self.headers)
        if resp.status_code == requests.codes.bad_request:
            return self._skip_file(resp.json())

        resp.raise_for_status()
        resp_json = resp.json()
        self._sequence += 1

        presigned_url = resp_json['url']
        fields = resp_json['fields']
        payload = fields

        res = requests.post(
            presigned_url,
            headers={},
            data=payload,
            files={'file': byte_im}
        )
        res.raise_for_status()

    def _upload_single_imagefile(
        self,
        imagefile,
        **kwargs
    ):
        """
        Used in:
            - Uploading images with extra and tags for image datasets.
            - Uploading related files of a pcd file.
        """

        filepath = imagefile.filepath
        base_name = os.path.basename(filepath)
        byte_im = open(filepath, 'rb').read()

        data = {
            "dataset_id": self.dataset_id,
            "file_name": base_name,
            "file_size": imagefile._size,
            "meta_data": {
                "batch_key": self.batch_key,
                "sequence": getattr(imagefile, 'sequence', None) or self._sequence
            }
        }

        if imagefile.tags:
            data['meta_data']['tags'] = imagefile.tags
        if imagefile.extra:
            data['meta_data']['extra'] = imagefile.extra

        resp = requests.post(url=self.file_upload_url,
                             json=data, headers=self.headers)
        if resp.status_code == requests.codes.bad_request:
            #check and skip uploading if the file is already uploaded
            prefixed_filename = self._skip_file(resp.json())
            imagefile.prefixed_filename = prefixed_filename
            return
        
        resp.raise_for_status()
        resp_json = resp.json()
        self._sequence += 1

        presigned_url = resp_json['url']
        fields = resp_json['fields']
        imagefile.prefixed_filename = fields['key'].split('/')[-1]
        payload = fields

        res = requests.post(
            presigned_url,
            headers={},
            data=payload,
            files={'file': byte_im}
        )
        res.raise_for_status()

    def _upload_single_base_file(self, basefile, **kwargs):
        base_name = os.path.basename(basefile.filepath)
        data = {
            "dataset_id": self.dataset_id,
            "file_name": base_name,
            "file_size": basefile._size,
            "meta_data": {
                "batch_key": self.batch_key,
                "sequence": self._sequence
            }
        }

        if basefile.tags:
            data['meta_data']['tags'] = basefile.tags

        related_files = []
        for related_file in basefile.related_files:
            if related_file.prefixed_filename:
                related_files.append(related_file.prefixed_filename)
        if related_files:
            data['meta_data']['related_files'] = related_files

        resp = requests.post(url=self.file_upload_url,
                             json=data, headers=self.headers)
        if resp.status_code == requests.codes.bad_request:
            return self._skip_file(resp.json())

        resp.raise_for_status()
        resp_json = resp.json()
        self._sequence += 1

        presigned_url = resp_json['url']
        fields = resp_json['fields']
        payload = fields

        res = requests.post(
            presigned_url,
            headers={},
            data=payload,
            files={'file': open(basefile.filepath, 'rb').read()}
        )
        res.raise_for_status()

    def _upload_raw_files(self, files_to_upload, uploader, tags, extra, *args, **kwargs):
        _uploaded = 1
        for datasetfile in files_to_upload:
            uploader(datasetfile, tags, extra)
            print(f'Files uploading... {_uploaded}', end='\r')
            _uploaded += 1
        self.event.set()

    def _upload_fileobjects(self, fileobjects, uploader, *args, **kwargs):
        _uploaded = 1
        for fileobject in fileobjects:
            uploader(fileobject)
            print(f'Files uploading... {_uploaded}', end='\r')
            _uploaded += 1
        self.event.set()

    async def send_heartbeat(self, session):
        while not self.heartbeat_event.is_set():
            try:
                async with session.head(self.stream_url, headers=self.headers) as r:
                    pass
                await asyncio.sleep(100)
            except Exception as e:
                pass

    async def _stream_status(self, num_of_files):
        async with aiohttp.ClientSession() as session:
            # self.heartbeat_event = asyncio.Event()
            # heartbeat_task = asyncio.create_task(self.send_heartbeat(session))
            async with session.get(self.stream_url, headers=self.headers, timeout=None) as response:
                while num_of_files > self._finished + self._skipped:
                    try:
                        chunk = await asyncio.wait_for(response.content.read(1024), timeout=60)
                        line = chunk.decode()
                        line = json.loads(line[6:])
                        if line["status"] == "finished":
                            self._finished += len(line["files"])
                        if self.event.is_set():
                            extracted = format(
                                ((self._finished + self._skipped)/num_of_files)*100, '.2f')
                            print(f"Processing... : {extracted}%", end="\r")

                    except json.JSONDecodeError:
                        lines = line.replace('data: ', '').split('\n')
                        for line in lines:
                            if line and line[0] == '{':
                                line = json.loads(line)
                                if line["status"] == "finished":
                                    self._finished += len(line["files"])

                    except asyncio.TimeoutError:
                        break
                    except aiohttp.EofStream as e:
                        raise e
                time.sleep(1)
                # self.heartbeat_event.set()
                # await heartbeat_task

    def files_upload_thread(self, raw_filepaths=None, imagefiles=None, basefiles=None, tags=[], extra={}):
        if raw_filepaths:
            bulk_uploader = self._upload_raw_files
            uploader = self._upload_single_file
            files_to_upload = raw_filepaths
        else:
            bulk_uploader = self._upload_fileobjects
            if imagefiles:
                uploader = self._upload_single_imagefile
                files_to_upload = imagefiles
            elif basefiles:
                uploader = self._upload_single_base_file
                files_to_upload = basefiles
            else:
                raise Exception('No data to upload')

        num_of_files = len(files_to_upload)
        self._finished, self._skipped = 0, 0
        try:
            status_thread = threading.Thread(target=asyncio.run, args=(
                self._stream_status(num_of_files,),), daemon=True)
            status_thread.start()

            time.sleep(0.1)
            upload_files_thread = threading.Thread(bulk_uploader(
                files_to_upload, uploader, tags, extra), daemon=False)
            upload_files_thread.start()
            status_thread.join()
        except Exception as e:
            raise e

        print(
            f"Files skipped: {self._skipped}. Files uploaded: {self._finished}")
        return self._finished


class DataSetUploaderAsync:
    def __init__(
        self,
        dataset_id,
        batch_key,
        file_upload_url,
        stream_url,
        headers
    ):
        self.dataset_id = dataset_id
        self.batch_key = batch_key
        self.file_upload_url = file_upload_url
        self.stream_url = stream_url
        self.headers = headers
        self._sequence = 0

    async def _get_presigned_url(
        self,
        session: aiohttp.ClientSession,
        filepath: str,
        headers: dict,
        tags: list,
        sequence: int,
        **kwargs
    ):
        base_name = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        data = {
            "dataset_id": self.dataset_id,
            "file_name": base_name,
            "file_size": file_size,
            "meta_data": {
                "batch_key": self.batch_key,
                "sequence": sequence
            }
        }

        if tags:
            data['meta_data']['tags'] = tags
        resp = await session.request('POST', self.file_upload_url, json=data, headers=headers)
        resp.raise_for_status()
        resp_json = await resp.json()
        return resp_json, filepath

    async def _upload_single_file(
        self,
        session: aiohttp.ClientSession,
        data: dict,
        filepath: str,
        **kwargs
    ):
        url = data['url']
        fields = data['fields']
        form_data = aiohttp.FormData()

        for key, value in fields.items():
            form_data.add_field(key, value)
        form_data.add_field('file',
                            open(filepath, 'rb').read()
                            )

        res = await session.post(
            url,
            headers={},
            data=form_data
        )
        res.raise_for_status()
        # await asyncio.sleep(0)

    async def _upload_files(self, files_to_upload, headers, tags):
        async with aiohttp.ClientSession() as session:
            tasks = []

            for file in files_to_upload:
                self._sequence += 1
                tasks.append(self._get_presigned_url(
                    session=session,
                    filepath=file,
                    headers=headers,
                    tags=tags,
                    sequence=self._sequence
                ))

            for task in asyncio.as_completed(tasks):
                resp_json, filepath = await task
                new_task = asyncio.create_task(self._upload_single_file(
                    session=session,
                    data=resp_json,
                    filepath=filepath
                ))
                await new_task

    async def _stream_status(self, num_of_files, headers):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.stream_url, headers=headers, timeout=None) as response:
                finished = 0
                while True:
                    try:
                        chunk = await asyncio.wait_for(response.content.read(1024), timeout=260)
                        line = chunk.decode()
                        line = json.loads(line[6:])
                        if line["status"] == "finished":
                            finished += len(line["files"])
                        elif line["status"] == "failed":
                            num_of_files -= len(line["files"])
                        print(f"Files uploaded : {finished}", end="\r")
                        if num_of_files == finished:
                            break
                    except asyncio.TimeoutError:
                        break
                    except json.JSONDecodeError:
                        pass

    async def _create_files_upload_tasks(self, files_to_upload, headers, tags):
        num_of_files = len(files_to_upload)
        stream_task = asyncio.create_task(
            self._stream_status(num_of_files, headers))
        upload_task = asyncio.create_task(
            self._upload_files(files_to_upload, headers, tags))
        await stream_task
        await upload_task

    def files_upload_thread(self, files_to_upload, headers, tags):
        try:
            asyncio.run(self._create_files_upload_tasks(
                files_to_upload, headers, tags))
        except Exception as e:
            raise e
