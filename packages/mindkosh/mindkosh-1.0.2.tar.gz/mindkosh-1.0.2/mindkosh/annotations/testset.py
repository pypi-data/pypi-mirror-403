# Copyright (C) 2023 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

import threading
import os
import re
import sys
import json
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RectangleSelector
from matplotlib.patches import Rectangle, Polygon
from matplotlib.lines import Line2D
from matplotlib.backend_tools import ToolToggleBase
import matplotlib.colors as colors
import mplcursors

from . import manager
from ..task import Frame
from ..issue import Issue


class SelectorTool(ToolToggleBase):
    default_keymap = None
    description = 'Toggle issue selector'
    default_toggled = True

    def __init__(self, *args, issue_selector, **kwargs):
        self.issue_selector = issue_selector
        super().__init__(*args, **kwargs)

    def enable(self, *args):
        self.issue_selector.set_active(True)
        print('issue selector activated.')

    def disable(self, *args):
        self.issue_selector.set_active(False)
        print('issue selector deactivated.')


class CursorConfig:
    def __init__(self):
        CursorConfig.patches_ = []

    def create(self):
        # TODO : fix issue with polyline
        cursor = mplcursors.cursor(self.patches_, hover=True)
        CursorConfig.cursor = cursor

        def set_annotations(sel):
            sel.annotation.set_text(sel.artist.get_label())
        CursorConfig.cursor.connect("add", set_annotations)

    @staticmethod
    def reset():
        CursorConfig.cursor.remove()
        CursorConfig.patches_ = []

    @staticmethod
    def add_patch(patch):
        CursorConfig.patches_.append(patch)

    @staticmethod
    def remove_annotations(event):
        if event.xdata or event.ydata:
            for s in CursorConfig.cursor.selections:
                CursorConfig.cursor.remove_selection(s)


class IssueManager:
    _CID = None

    def __init__(self, client):
        self.client = client
        self.frame_id = None
        self.job_id = None
        self._issue_rect_position = None

    def create_selector(self):
        def onselect(eclick, erelease):
            self._issue_rect_position = [
                eclick.xdata, eclick.ydata, erelease.xdata, erelease.ydata]

        self.issue_selector = RectangleSelector(plt.gca(), onselect, interactive=True, useblit=True,
                                                props=dict(facecolor='red', edgecolor='black', alpha=0.4))
        return self.issue_selector

    def clear_selector(self):
        self._issue_rect_position = None
        self.issue_selector.clear()

    def create_buttons(self):
        addIssueButton = Button(
            plt.axes([0.45, 0.01, 0.12, 0.05]),
            label="Add Issue",
            hovercolor='#33ff33'
        )
        self.addIssueButton = addIssueButton

    def add_button_events(self, ax, fig, callback):
        def add_issue(event):
            position = self._issue_rect_position
            if not position or position[0] == position[2]:
                print("Select area to add issue")
                return

            # disconnecting key_press_event while taking user input
            fig.canvas.mpl_disconnect(self._CID)
            self.diable_issueButton()

            ticket_name = self._verify_ticket_name(
                input("Enter ISSUE Name : "))

            Issue.create_ticket(
                client=self.client,
                frame=self.frame_id,
                job=self.job_id,
                ticket_name=ticket_name,
                dimension='2d'
            )

            self.plot_issue(
                ax,
                position=position,
                label=ticket_name
            )
            plt.draw()

            # connecting key_press_event and enabling issue button after creating issue
            self.enable_issueButton()
            self._CID = fig.canvas.mpl_connect('key_press_event', callback)

        self.addIssueButton.on_clicked(add_issue)

    def enable_issueButton(self):
        self.addIssueButton.set_active(True)

    def diable_issueButton(self):
        self.addIssueButton.set_active(False)

    @staticmethod
    def plot_issue(ax, position, label):
        issue_rect = Rectangle((position[0], position[1]), position[2]-position[0],
                               position[3]-position[1], linewidth=1, edgecolor=None,
                               facecolor=(0, 0, 0, 0), hatch='--', label=label
                               )
        issue_border = ax.add_patch(issue_rect)
        CursorConfig.add_patch(issue_border)

    @staticmethod
    def _verify_ticket_name(ticket):
        ticket = ticket.strip()
        ticket = re.sub(r" {2,}", " ", ticket)
        if ticket and ticket != ' ':
            return ticket
        else:
            plt.close()
            raise Exception("Could not add issue. Invalid issue name")


class TestSet:
    def __init__(self):
        self.frames = []
        self._index = 0

    def add_frames(self, frames):
        """Adds a list of frame objects to the testset
        :param frames : list of frame objects
        """
        for f in frames:
            assert isinstance(f, Frame), f"Invalid frame object : {f}"
            if f.datasetfile.size > 4 * 10 ** 6:
                raise Exception('can not visualize large files')

        self.frames.extend(frames)

    def remove_frames(self, frames):
        for f in frames:
            try:
                self.frames.remove(f)
            except ValueError:
                pass

    def clear(self):
        self._index = 0
        self.frames = []
        sys.stdout.write('testset cleared \n')

    def visualize(
        self,
        show_annotations=True,
        show_issues=False,
        fill_color=0.3
    ):
        """Visualise all the frames added to testset.
            - Frames can be from different tasks too.
            - Supports adding an issue to any frame (issue name and the position rectangle on image)

            Args :
                `show_annotations` (bool) : wheather draw annotations or not
                `show_issues` (bool) : wheather show issues or not
                `fill_color` (float) : Color intensity in a rectangle or polygon
        """

        self._index = 0
        self.show_annotations = show_annotations
        self.show_issues = show_issues
        self.fill_color = fill_color

        if self.frames:
            return
        if not self.frames:
            raise IndexError('frames list is empty, nothing to visualize')

        if not (isinstance(self.fill_color, (int, float))) or not (0.0 <= self.fill_color <= 1.0):
            raise ValueError("fill_color should be in range of 0 to 1")

        plt.rcParams['figure.dpi'] = 110
        plt.rcParams['image.interpolation'] = 'none'
        # plt.rcParams['toolbar'] = 'toolmanager'
        fig, ax = plt.subplots()
        fig.canvas.manager.toolbar.pack(side='bottom')  # fill='y'
        self.ax = ax
        self.fig = fig

        self.cursormanager = CursorConfig()
        self._plot_image()

        # issue_selector = issuemanager.create_selector()
        # TODO : add toggle icon / make the click area larger
        # fig.canvas.manager.toolmanager.add_tool('Selector', SelectorTool, issue_selector=issue_selector)
        # fig.canvas.manager.toolbar.add_tool('Selector', 'toolitem')
        # fig.canvas.manager.toolmanager.remove_tool('forward')
        # fig.canvas.manager.toolmanager.remove_tool('back')
        self._hault = False

        def toggle_image(event):
            if not self._hault:
                if event.key in ('left', 'up'):
                    self._hault = True
                    self._index = self._index-1 if self._index > 0 else \
                        len(self.frames)-1 if self._index == 0 else 0

                elif event.key in ('right', 'down'):
                    self._hault = True
                    self._index = self._index+1 if self._index < len(self.frames)-1 else \
                        0 if self._index == len(self.frames)-1 else 0

                elif event.key == 'escape':
                    return plt.close()

                else:
                    return

                self.ax.cla()
                self.cursormanager.reset()
                self._plot_image()
                self.cursormanager.create()
                plt.draw()
                self._hault = False
            return

        def on_button_press(event):
            threading.Thread(target=toggle_image, args=(event,)).start()

        self.cursormanager.create()
        plt.connect('motion_notify_event',
                    self.cursormanager.remove_annotations)
        fig.canvas.mpl_connect('key_press_event', on_button_press)
        plt.connect('close_event', lambda event: self.clear())
        plt.show()

    def _plot_image(self):
        self.fig.canvas.set_window_title(
            self.frames[self._index].datasetfile.name)
        self.ax.imshow(self.frames[self._index].im())

        if self.show_annotations:
            self._plot_annotations()

        if self.show_issues:
            self._plot_issues()

        current = self._index + 1
        total = len(self.frames)
        task = self.frames[self._index].task_id
        frame = self.frames[self._index].frame_id
        print(
            f"Frame ({current}/{total}) : (task_id : {task}, frame_id : {frame})")

    def _plot_issues(self):
        issues = self.frames[self._index].issues
        for issue in issues:
            if issue['resolver']:
                continue
            position = issue['position']
            IssueManager.plot_issue(
                ax=self.ax,
                position=position,
                label=issue["name"]
            )

    def _plot_annotations(self):
        legends = set()

        annotations = self.frames[self._index].annotations()
        shapes = annotations["shapes"]

        label_names = set()

        for shape in shapes:
            tool_type = shape["type"]
            if not tool_type:
                return
            points = shape["points"]
            edgecolor = "w"
            for label in self.frames[self._index].labels:
                if label.id == shape["label_id"]:
                    edgecolor = colors.to_rgb(label.color)
                    facecolor = edgecolor + (self.fill_color,)
                    break

            if tool_type == "rectangle":
                rect = Rectangle((points[0], points[1]), points[2]-points[0], points[3]-points[1],
                                 linewidth=1, edgecolor=edgecolor, facecolor=facecolor, label=label.name)
                border = self.ax.add_patch(rect)
                self.cursormanager.add_patch(border)

            elif tool_type == "polygon":
                polygon = Polygon([(points[2*i], points[2*i+1]) for i in range(len(points)//2)],
                                  linewidth=1, edgecolor=edgecolor, facecolor=facecolor, label=label.name)
                border = self.ax.add_patch(polygon)
                self.cursormanager.add_patch(border)

            elif tool_type == "polyline":
                x = [points[2*i] for i in range(len(points)//2)]
                y = [points[2*i+1] for i in range(len(points)//2)]
                border = self.ax.plot(x, y, c=label.color,
                                      linewidth=1, label=label.name)

            elif tool_type == "cuboid":
                continue

            elif tool_type == "points":
                x = [points[2*i] for i in range(len(points)//2)]
                y = [points[2*i+1] for i in range(len(points)//2)]
                border = self.ax.scatter(
                    x, y, c=label.color, s=10, label=label.name)
                self.cursormanager.add_patch(border)

            if label.name not in label_names:
                legend_element = (Line2D([0], [0], marker='o', label=label.name,
                                         markerfacecolor=label.color, c=label.color,
                                         markersize=6, ls=''))
                legends.add(legend_element)
                label_names.add(label.name)

        self.ax.legend(handles=legends)

    @property
    def _combined_labels_images_annotations_(self):
        task_and_frames = {}
        combined_labels = []
        combined_images = {}
        for frame in self.frames:
            if frame.task_id in task_and_frames:
                task_and_frames[frame.task_id].append(frame.frame_id)
                combined_images[frame.task_id][frame.frame_id] = frame
            else:
                task_and_frames[frame.task_id] = [frame.frame_id]
                combined_images[frame.task_id] = {frame.frame_id: frame}
                combined_labels += frame.labels

        combined_annotations = []
        for task_id, frame_ids in task_and_frames.items():
            try:
                url = self.client.api.frame_annotations(
                    task_id, "_".join([str(frame) for frame in frame_ids]))
                response = self.client.session.get(url)
                response.raise_for_status()
                response = response.json()
                response["labels"] = [label.__dict__ for label in frame.labels]
                response["task_id"] = task_id
                combined_annotations.append(response)

            except Exception as e:
                raise e

        return combined_labels, combined_images, combined_annotations

    def download_annotations(self, location, filename=None, format=None):
        """Downdloads annotations for all the frames added in the testset.
            - frames added in testset can be from differnt tasks.
            - Downloads raw annotations if no format is mentioned.
            - Valid dataset options are :
                    'coco', 'yolo', 'voc', 'datumaro'

            Args:
                - `location` (str) : Path to the local directory.
                - `filename` (str, optional) : name of the annotation file
                - `format` (str, optional) : dataset format in which you want to download annotations.
        """

        if not os.path.exists(location):
            raise FileNotFoundError(f"No such file or directory: '{location}'")

        labels_, images_, raw_annotations_ = self._combined_labels_images_annotations_
        json_object = json.dumps(raw_annotations_, indent=4)
        if not format:
            filename = os.path.join(location, filename or "annotatoins_" +
                                    datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p") + ".json")
            with open(filename, "w") as outfile:
                outfile.write(json_object)
                print("Downloaded : ", filename)
                return
        frames = {}
        for frame in self.frames:
            frames[frame.frame_id] = frame
        filename = os.path.join(
            location, format + "_" + datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p"))

        manager.create(
            images_,
            raw_annotations=raw_annotations_,
            labels=labels_,
            annotationfile=filename,
            annotationformat=format
        )

    def convert_datasets(
        self,
        datasets,
        format,
        newformat,
        location
    ):
        manager.convert(
            datasetspath=datasets,
            format=format, newformat=newformat,
            location=location
        )
