# Copyright (C) 2023 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

import os
import re
import time
import logging
import requests
import validators

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
import matplotlib.colors
import mplcursors

try:
    import open3d as o3d
except ImportError:
    pass
from PIL import Image
from io import BytesIO

import mimetypes
import tempfile

from .utils import TaskProperty, AnnotationFormats, verify_name
from .label import Label, Attribute
from .issue import Issue, Comment
from .annotations.tag import Tag
from .annotations.manager import _verify_annotations
from .exceptions import InvalidTagError, InvalidLabelError

logger = logging.getLogger(__name__)


class DatasetFile:
    def __init__(self, id, original_name, size, meta_data, tags, **kwargs):
        self.id = id
        self.name = original_name
        self.size = size
        self.meta_data = meta_data
        self.tags = tags
        self.presigned_url = kwargs.get('presigned_url', None)

    def __repr__(self):
        return self.name


class Frame:

    def __init__(
        self,
        frame_id: int,
        job_id: int,
        datasetfile: DatasetFile,
        task_id: int,
        labels: list
    ):
        self.frame_id = frame_id
        self.datasetfile = datasetfile
        self.task_id = task_id
        self.job_id = job_id
        self.labels = labels  # task labels

    def __str__(self):
        return str({"frame_id": self.frame_id, "datasetfile": self.datasetfile, "task_id": self.task_id})

    def __repr__(self):
        return self.datasetfile.name

    def _get_presigned_url(self):
        url = self.client.api.download_dataset_file(self.datasetfile.id)
        response = self.client.session.post(url)
        response.raise_for_status()
        return response.json()["presigned_url"]

    def im(self):
        """
        Returns : a PIL.Image object

        """
        if not self.datasetfile.presigned_url:
            self.datasetfile.presigned_url = self._get_presigned_url()
        try:
            response = requests.get(self.datasetfile.presigned_url)
            # FIXME: re-try with a new presigned url if it's expired already
            _im = Image.open(BytesIO(response.content))
            return _im
        except Exception as e:
            raise e

    def tags(self):
        """returns list of classification tags 
        """
        tags_ = self.annotations()["tags"]
        _tags = []
        for tag in tags_:
            for label in self.labels:
                if label.id == tag["label_id"]:
                    _tags.append(Tag(**tag, label_name=label.name))
                    break
        return _tags

    def issues(self):
        issues = Issue.get_frame_issues(
            self.client, self.frame_id, self.job_id)
        return issues

    def annotations(self):
        try:
            url = self.client.api.frame_annotations(
                self.task_id, self.frame_id)
            response = self.client.session.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise e
        return response.json()

    def download(self, location):
        try:
            im = self.im()
            mime_type = im.get_format_mimetype() or 'image/jpg'
            im_ext = mimetypes.guess_extension(mime_type)
            if im_ext == None:
                im_ext = '.jpg'
            outfile = f"task-{self.task_id}_frame-{self.frame_id}{im_ext}"
            fullpath = os.path.join(location, outfile)
            im.save(fullpath)
            print("Saved :", fullpath)

        except requests.exceptions.HTTPError as e:
            raise e

    def add_issue(self, issue_name: str, shape_id: int = None, track_id: int = None, message: str = None):
        issue_name = verify_name(issue_name, 'issue')

        issue_id = Issue.create_ticket(
            client=self.client,
            frame=self.frame_id,
            job=self.job_id,
            ticket_name=issue_name,
            dimension='2d',
            shape_id=shape_id,
            track_id=track_id
        )

        if message:
            Comment.add_comment(self.client, issue_id, message)

    def add_issue_comment(self, issue_id, message):
        Comment.add_comment(self.client, issue_id, message)

    def visualize(
            self,
            show_annotations=True,
            show_issues=True,
            fill_color=0.35
    ):

        if self.datasetfile.size > 4*10**6:
            raise Exception('can not visualize large files')
        im = self.im()
        plt.rcParams['figure.dpi'] = 110
        plt.rcParams['image.interpolation'] = 'none'
        fig, ax = plt.subplots()

        fig.canvas.manager.toolbar.pack(side='bottom')  # fill='y'
        ax.imshow(im)
        plt.title(self.datasetfile.name)

        legends = set()

        if show_annotations == False:
            return plt.show()

        if not (isinstance(fill_color, (int, float))) or not (0.0 <= fill_color <= 1.0):
            raise ValueError("fill_color should be in range of 0 to 1")

        annotations = self.annotations()

        shapes = annotations["shapes"]
        label_names = set()
        self._patches = []

        for shape in shapes:
            tool_type = shape["type"]
            if not tool_type:
                continue

            points = shape["points"]
            edgecolor = "w"
            for label in self.labels:
                if label.id == shape["label_id"]:
                    edgecolor = matplotlib.colors.to_rgb(label.color)
                    facecolor = edgecolor + (fill_color,)
                    break

            if tool_type == "rectangle":
                rect = patches.Rectangle((points[0], points[1]), points[2]-points[0], points[3] -
                                         points[1], linewidth=1, edgecolor=edgecolor, facecolor=facecolor, label=label.name)
                liness = ax.add_patch(rect)
                self._patches.append(liness)

            elif tool_type == "polygon":
                polygon = patches.Polygon([(points[2*i], points[2*i+1]) for i in range(len(
                    points)//2)], linewidth=1, edgecolor=edgecolor, facecolor=facecolor, label=label.name)
                liness = ax.add_patch(polygon)
                self._patches.append(liness)

            elif tool_type == "polyline":
                x = [points[2*i] for i in range(len(points)//2)]
                y = [points[2*i+1] for i in range(len(points)//2)]
                liness = plt.plot(x, y, c=label.color,
                                  linewidth=1, label=label.name)

            elif tool_type == "cuboid":
                continue

            elif tool_type == "points":
                x = [points[2*i] for i in range(len(points)//2)]
                y = [points[2*i+1] for i in range(len(points)//2)]
                liness = plt.scatter(x, y, c=label.color,
                                     s=10, label=label.name)
                self._patches.append(liness)

            if label.name not in label_names:
                legend_element = (Line2D([0], [0], marker='o', label=label.name,
                                  markerfacecolor=label.color, c=label.color, markersize=5, ls=''))
                legends.add(legend_element)
                label_names.add(label.name)

        if legends:
            ax.legend(handles=legends)

        def plot_issue(position, label):
            issue_rect = patches.Rectangle((position[0], position[1]), position[2]-position[0],
                                           position[3]-position[1], linewidth=1, edgecolor=None,
                                           facecolor=(0, 0, 0, 0), hatch='--', label=label)
            issue_border = ax.add_patch(issue_rect)
            self._patches.append(issue_border)

        cursor = mplcursors.cursor(self._patches, hover=True)
        self._patches = None

        def set_annotations(sel):
            sel.annotation.set_text(sel.artist.get_label())
        cursor.connect("add", set_annotations)

        def remove_annotations(event):
            if event.xdata or event.ydata:
                for s in cursor.selections:
                    cursor.remove_selection(s)
        plt.connect('motion_notify_event', remove_annotations)
        plt.show()


class PointCloud:
    def __init__(
        self,
        frame_id: int,
        job_id: int,
        datasetfile: DatasetFile,
        task_id: int,
        labels: list
    ):
        self.frame_id = frame_id
        self.datasetfile = datasetfile
        self.task_id = task_id
        self.job_id = job_id
        self.labels = labels  # task labels

    def __str__(self):
        return str({"frame_id": self.frame_id, "datasetfile": self.datasetfile, "task_id": self.task_id})

    def __repr__(self):
        return self.datasetfile.name

    def issues(self):
        issues = Issue.get_frame_issues(
            self.client, self.frame_id, self.job_id)
        return issues

    def add_issue(self, issue_name, shape_id: int = None, track_id: int = None, message: str = None):
        issue_name = verify_name(issue_name, 'issue')

        issue_id = Issue.create_ticket(
            client=self.client,
            frame=self.frame_id,
            job=self.job_id,
            dimention='3d',
            ticket_name=issue_name,
            shape_id=shape_id,
            track_id=track_id
        )

        if message:
            Comment.add_comment(self.client, issue_id, message)

    def add_issue_comment(self, issue_id, message):
        Comment.add_comment(self.client, issue_id, message)

    @property
    def file(self):
        try:
            url = self.client.api.download_dataset_file(self.datasetfile.id)
            response = self.client.session.post(url)
            response.raise_for_status()
            response = requests.get(response.json()["presigned_url"])
        except requests.exceptions.HTTPError as e:
            raise e
        return response.content

    def annotations(self):
        try:
            url = self.client.api.frame_annotations(
                self.task_id, self.frame_id)
            response = self.client.session.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise e
        return response.json()

    @staticmethod
    def _verify_color(color):
        assert isinstance(color, tuple) and len(color) == 3
        for c in color:
            if not isinstance(c, int) or c < 0 or c > 255:
                raise Exception("Invalid color")

    def visualize(
        self,
        show_annotations=True,
        bg=(0, 0, 0),
        points_color=None,
    ):
        self.show_annotations = show_annotations
        self.points_color = points_color

        self._verify_color(bg)
        if bg:
            return

        file = tempfile.NamedTemporaryFile(suffix='.pcd').name
        with open(file, 'wb') as fp:
            fp.write(self.file)
        pcd = o3d.io.read_point_cloud(file)

        # visualizer
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name=self.datasetfile.name)
        vis.get_render_option().background_color = bg
        vis.get_render_option().point_size = 1
        vis.add_geometry(pcd)

        # get frame annotations and draw
        annotations = self.annotations()

        shapes = annotations["shapes"]
        for shape in shapes:
            if not shape["type"]:
                continue
            for label in self.labels:
                if label.id == shape["label_id"]:
                    edgecolor = matplotlib.colors.to_rgb(label.color)
                    break
            _extra = shape["extra"]
            _size = _extra["parameter"]

            # create bbox
            box = o3d.geometry.TriangleMesh.create_box(
                width=_size["w"], depth=_size["h"], height=_size["l"]
            )
            box.compute_vertex_normals()
            box.paint_uniform_color([1.0, 1.0, 1.0])

            box_mesh = o3d.geometry.LineSet.create_from_triangle_mesh(box)
            box_mesh.paint_uniform_color(edgecolor)

            # get center coordinates using center point
            _center_point = _extra['center_point']
            _center = pcd.points[_center_point]

            # get center of mesh
            c1 = _center[0] - (_size['l']/2)
            c2 = _center[1] - (_size['w']/2)
            c3 = _center[2] - (_size['l']/2)

            box_mesh.translate((c1, c2, c3))
            vis.add_geometry(box_mesh)

        vis.run()
        vis.destroy_window()


class Task:
    def __init__(
        self,
        data
    ):
        self.task_id = data['id']
        self.name = data['name']
        self.batches = data['batches']
        self.project_id = data['project_id']
        self.labels = [Label(**label) for label in data['labels']]
        self.category = data['category'] if 'category' in data else None
        self.job_modes = data['job_modes'] if 'job_modes' in data else [
            'validation', 'qc']
        self.dimension = data['dimension']
        self.multi_annotators = data['multi_annotators']
        self.data = data['data']
        self._segments = data['segments']

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        if getattr(self, "_deleted", False):
            return "<Task (deleted)>"
        return f"<Task id={self.task_id!r} name={self.name!r}>"

    @property
    def meta(self):
        meta_data = self.client.session.get(
            url=self.client.api.task_data_meta(),
            json={'task_id': self.task_id}
        )
        meta_data.raise_for_status()
        meta_data = meta_data.json()
        return {'size': meta_data['size'], 'tags': meta_data['tags']}

    @property
    def job_id_frame_ids_mapping(self):
        if not hasattr(self, '_job_id_frame_ids_mapping'):
            self._job_id_frame_ids_mapping = {}
            for segment in self._segments:
                self._job_id_frame_ids_mapping[segment['job']['id']] = (
                    segment['start_frame'], segment['stop_frame'])
        return self._job_id_frame_ids_mapping

    def frames(self, search: str = None, max_frames: int = 10):
        # TODO: allow page number in params
        if self.category == 'video':
            return

        limit = max_frames if max_frames <= 50 else 50
        url = self.client.api.task_data_frames(
            self.task_id, limit, search=search, download=0)
        response = self.client.session.get(
            url=url)
        response.raise_for_status()
        frames = response.json()['results']

        frame_objs = []
        frames_job_id_mapping = self.job_id_frame_ids_mapping
        for frame in frames:
            frame_id = frame['frame']
            for job_id, (start_frame, stop_frame) in frames_job_id_mapping.items():
                if start_frame <= job_id <= stop_frame:
                    break
            dataset_file = frame['dataset_file']
            datasetfile = DatasetFile(
                dataset_file['id'],
                dataset_file['name'].split('_', 1)[-1],
                dataset_file['size'],
                dataset_file['meta_data'] if 'meta_data' in dataset_file else {},
                dataset_file['tags'] if 'tags' in dataset_file else [],
                presigned_url=dataset_file['presigned_url'] if 'presigned_url' in dataset_file else None
            )
            if self.dimension == '2d':
                frame_objs.append(
                    Frame(frame_id, job_id, datasetfile, self.task_id, self.labels))
            else:
                frame_objs.append(PointCloud(
                    frame_id, job_id, datasetfile, self.task_id, self.labels))
        return frame_objs

    def add_annotation_issue(
        self,
        frame_id: int,
        issue_name: str,
        shape_id: int = None,
        track_id: int = None,
        message: str = None
    ):
        if frame_id < 0 or frame_id >= self.meta['size']:
            raise Exception('Invalid frame id')
        if not issue_name or not isinstance(issue_name, str):
            raise Exception('Invalid issue name')

        for job_id, (start_frame, stop_frame) in self.job_id_frame_ids_mapping.items():
            if start_frame <= job_id <= stop_frame:
                break

        issue_id = Issue.create_ticket(
            client=self.client,
            frame=frame_id,
            job=job_id,
            ticket_name=issue_name,
            dimension=self.dimension,
            shape_id=shape_id,
            track_id=track_id
        )

        if message:
            Comment.add_comment(self.client, issue_id, message)

    def delete(self) -> None:
        self._delete_task(self.client, self.task_id)
        for attr in list(vars(self).keys()):
            setattr(self, attr, None)
        self._deleted = True

    def update_name(self, name: str) -> None:
        name = verify_name(name, 'task')

        try:
            url = self.client.api.tasks_id(self.task_id)
            response = self.client.session.patch(
                url,
                json={"name": name}
            )
            response.raise_for_status()

            if self.client.verbose_output == True:
                print(f"Task id {self.task_id} updated. New name : {name}")
                self.name = name

        except requests.exceptions.HTTPError as e:
            raise e

    def update_project_id(self, new_project_id: int):
        task_id = self.task_id
        project_id = new_project_id

        if project_id:
            p_url = self.client.api.projects_id(project_id)
            p_response = self.client.session.get(p_url)

            if p_response.status_code == 404:
                raise Exception(f"project id {project_id} not found")

        try:
            url = self.client.api.tasks_id(task_id)
            response = self.client.session.patch(
                url, json={'project_id': project_id})
            response.raise_for_status()
            if self.client.verbose_output == True:
                print(
                    f"Task id {task_id} updated. New project_id : {project_id}")
                self.project_id = project_id
        except requests.exceptions.HTTPError as e:
            raise e

    def upload_annotations(self, annotation_format, local_path, webhook_url=None):
        """
        :param annotation_format(str): Format of annotation file
        :param local_path(str): Path to annotations file(zip)
        """
        dst_format = AnnotationFormats.validate(
            annotation_format, self.category, upload=True)

        # verify if task has all the labels from annotation file
        if self.category != 'pointcloud':
            _verify_annotations(local_path, annotation_format, self.labels)

        try:
            url = self.client.api.tasks_id_annotations(
                self.task_id, webhook_url, fileformat=dst_format)
            f = open(local_path, 'rb')
            resp = self.client.session.put(
                url=url,
                data={},
                files={'annotation_file': f.read()}
            )
            resp.raise_for_status()
            if resp.status_code == 202:
                print('Annotations upload started')
            else:
                return resp
        except requests.exceptions.RequestException as e:
            raise e

    def get_releases(self):
        """
        Returns all the release for given task
        """
        try:
            response = self.client.session.get(
                url=self.client.api.releases(self.task_id)
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            raise e

    def create_release(self, format: str, batches: list = [], description: str = None, webhook_url=None):
        """Creates an annotation release for given list of job_ids/batches and annotation format.

        :param format: annotation format
        :param batches: list of valid job ids for selected task
        :param description : optional description.

        - Valid annotation formats:

            - 2d : 'coco', 'yolo', 'voc', 'datumaro', 'segmentation_mask', 'cvat'.
            - 3d : 'kitti'.

        - Exceptions:
            - Invalid annotation format error.
            - Invalid batches list for the task.
            - A Release for given batches and format already exists.

        Returns: created release(json)"""

        url = self.client.api.releases(self.task_id)
        if webhook_url:
            if not validators.url(webhook_url):
                raise Exception('Invalid webhook url')
            url += f'&webhook_url={webhook_url}'

        validated_format = AnnotationFormats.validate(format, self.category)
        payload = {'task_id': self.task_id, 'description': description,
                   'format': validated_format, 'batches': batches}

        try:
            response = self.client.session.post(
                url, json=payload)
            if response.status_code == requests.codes.created:
                return response.json()
            raise Exception(response.text)
        except requests.exceptions.RequestException as e:
            raise e

    def delete_release(self, release_id):
        try:
            res = self.client.session.delete(
                url=self.client.api.release_id(release_id)
            )
            if res.status_code in (requests.codes.accepted, requests.codes.no_content):
                print(f'release_id {release_id} deleted')
                return
            raise Exception(res.text)
        except requests.exceptions.RequestException as e:
            raise e

    def download_release(self, release_id: int, local_path: str, **kwargs):
        """Downloads the release at `local_path` if it's ready to download else starts creating it.
        """
        if not os.path.isdir(local_path):
            raise IOError('invalid directory ', local_path)

        url = self.client.api.download_release(release_id)

        resp = self.client.session.get(url)
        resp.raise_for_status()
        if resp.status_code == requests.codes.accepted:
            print('Release is being prepared')
            return
        filename = os.path.join(local_path, f'release_id_{release_id}.zip')

        response = requests.get(resp.json())
        with open(filename, 'wb') as fp:
            fp.write(response.content)
            print(f"Downloaded : {filename}")

    def add_label(self, label, **kwargs):
        """
        add/update a label to a task.

        :param label: `mindkosh.Label`

        Returns :  updated label object
        """
        if type(label).__name__ != "Label":
            raise InvalidLabelError('invalid label')

        Label.verify(label)
        Attribute.verify(label.attributes)

        task_url = self.client.api.tasks_id(self.task_id)

        label.attributes = [att.__dict__ for att in label.attributes]
        payload = {"labels": [vars(label)]}

        try:
            response = self.client.session.patch(
                task_url, json=payload)
            response.raise_for_status()
            labels = response.json()['labels']
            for l in labels:
                if l['name'] == label.name:
                    print('label updated')
                    return Label(**l)
            raise Exception('Could not add/update label')

        except requests.exceptions.RequestException as e:
            raise e
        
    def download_issues(self,
            save_at:str,
            job_ids:list = []
        ) -> None:
        """
        Download issues in csv format for a task.

        :param save_at: Local directory where to save the exported issues.
        :param job_ids: Export issues for job_ids if it's not empty, else export issues for entire task
        """

        if not os.path.isdir(save_at) or not os.path.exists(save_at):
            raise IOError('invalid directory ', save_at)

        payload = {'task_id': self.task_id, 'job_ids': job_ids}
        
        try:
            response = self.client.session.post(
                url=self.client.api.export_issues(), json=payload)
            response.raise_for_status()

            c_d = response.headers.get("Content-Disposition", "")
            match = re.findall('filename="(.+)"', c_d)
            filename = match[0] if match else f"task_id_{self.task_id}_issues.csv" 
            full_path = os.path.join(save_at, filename) 
            with open(full_path, "wb") as f:
                f.write(response.content)

            print("Issues downloaded: ", full_path)
        except requests.exceptions.RequestException as e:
            raise e


    @classmethod
    def create(
        cls,
        name: str,
        labels: list,
        dataset_id: int,
        tags: list = None,
        project_id: int = None,
        batches: int = 1,
        job_modes: list = ['validation'],
        qc_data: int = 20,
        multi_annotators: bool = False,
        **kwargs
    ) -> "Task | str":
        
        """
        Creates a task for given `dataset_id` and `tags`.

        :param name: A valid task name.
        :param labels: List of label objects. Each label should be an instance of `mindkosh.Label`.
        :param dataset_id: A valid dataset_id.
        :param project_id: Adds the task to a project (optional).
        :param batches: Devides the task into multiple jobs.
        :param qc_data: percentage of data that should be marked for qc.

        Returns : Task object if task is created successfully else a string
        """

        name = verify_name(name, 'task')

        if not multi_annotators:
            if not isinstance(qc_data, int) or not 0 <= qc_data <= 100:
                raise Exception("Invalid qc_data")
        else:
            qc_data = 0

        job_modes = [TaskProperty.JOB_MODES(
            mode.lower()).value for mode in job_modes]

        labels = (labels,) if not isinstance(labels, (list, tuple)) else labels
        for label in labels:
            if type(label).__name__ != "Label":
                raise InvalidLabelError(f"Invalid Label object : '{label}'")
        Label.verify(labels)

        labels_json = []
        for label in labels:
            label.attributes = [att.__dict__ for att in label.attributes]
            labels_json.append(label.__dict__)

        url = cls.client.api.tasks
        payload = {
            'name': name,
            'labels': labels_json,
            'batches': batches,
            'job_modes': job_modes,
            'tools': TaskProperty.TOOLS,
            'data': {
                'dataset_id': dataset_id
            },
            'qc_data': qc_data,
            'multi_annotators': multi_annotators
        }
        if project_id:
            payload['project_id'] = project_id
        if tags:
            payload['data']['tags'] = tags

        try:
            response = cls.client.session.post(
                url,
                json=payload
            )

            if response.status_code == requests.codes.accepted:
                return cls._wait_till_done(response.json()['job_id'])

            if response.status_code == requests.codes.bad_request:
                response = response.json()
                if 'data' in response:
                    data = response['data']
                    if 'tags' in data:
                        raise InvalidTagError(str(data['tags']))
                    raise Exception(data['dataset_id'])
                raise Exception(response)

            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            raise e

    @classmethod
    def _wait_till_done(cls, job_id):
        url = cls.client.api.tasks_status(job_id)
        while True:
            res = cls.client.session.get(url).json()
            state = res['state'].lower()
            if state == 'finished':
                return cls.get(res['result']['task_id'])
            elif state == 'Failed':
                return f"Failed to create task. {res['message']}"
            time.sleep(2)

    @staticmethod
    def _delete_task(client, task_id: int):
        try:
            url = client.api.tasks_id(task_id)
            response = client.session.delete(url)
            if response.status_code == requests.codes.no_content or response.status_code == requests.codes.accepted:
                logger.warning(f"Task id {task_id} deleted")
                return
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise e

    @classmethod
    def get(cls, task_id: int = None):
        """
        Returns list of all task objects if `task_id` is not None else return the selected task object
        """

        if task_id:
            url = cls.client.api.tasks_id(task_id)
            try:
                response = cls.client.session.get(url)
                response.raise_for_status()
                return Task(response.json())
            except requests.exceptions.HTTPError as e:
                raise e

        page = 1
        taskobjects = []
        while True:
            url = cls.client.api.tasks_page(page)
            try:
                response = cls.client.session.get(url)
                response.raise_for_status()
                response_json = response.json()

                for data in response_json['results']:
                    taskobjects.append(Task(data))

                if not response_json['next']:
                    break
                page += 1

            except requests.exceptions.HTTPError as e:
                raise e

        return taskobjects
