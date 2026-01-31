# Copyright (C) 2022 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

import re
from enum import Enum
from .exceptions import InvalidLabelError


class LabelType(str, Enum):
    SEMANTIC_MASK = 'semantic_mask'
    INSTANCE_MASK = 'instance_mask'

    @classmethod
    def values(cls):
        return tuple(x.value for x in cls)


class Label:
    def __init__(
        self,
        name: str,
        color: str,
        type : str = None,
        sequence: int = None,
        extra: dict = {},
        **kwargs
    ):
        self.name = name
        self.color = color
        self.extra = extra
        self.sequence = sequence
        self.track = kwargs.get('track', False)
        self.lock_dimensions = kwargs.get('lock_dimensions', False)

        if type:
            self.type = type
            if self.type not in LabelType.values():
                raise InvalidLabelError('Invalid label type')

        if 'id' in kwargs:
            self.id = kwargs['id']
        if 'attributes' in kwargs:
            attributes = kwargs['attributes']
            attributes = [attributes] if not isinstance(
                attributes, (list, tuple)) else attributes
            self.attributes = [Attribute(attr) for attr in attributes]
        else:
            self.attributes = []

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def verify_color(label):
        color = label.color
        if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color):
            raise InvalidLabelError(
                f"color '{color}' is not valid for label '{label}'")

    @staticmethod
    def verify(labels):
        if not isinstance(labels, list):
            labels = [labels]
        names = []
        sequence_set = []
        for label in labels:
            errors = []
            # verify extra
            required_keys = ('width', 'height', 'length')
            for key in required_keys:
                if key not in label.extra:
                    label.extra[key] = 1
                elif not isinstance(label.extra[key], int) or not 0 < label.extra[key] < 100:
                    errors.append(
                        f"\nInvalid label {key} : {label.extra[key]}.")

            # Check name  and  sequence
            if label.name in names:
                errors.append(f"label name '{label.name}' is not unique.")
            if not isinstance(label.sequence, int) or label.sequence < 0:
                errors.append(f"sequence value must be a positive integer.")
            if label.sequence in sequence_set:
                errors.append(
                    f"label sequence '{label.sequence}' is not unique.")

            if not (isinstance(label.track, bool) and isinstance(label.lock_dimensions, bool)):
                errors.append(
                    f"track and lock_dimensions values should be type of boolean")

            if errors:
                raise InvalidLabelError(
                    f"Invalid label: {label.name}. Message: {' '.join(errors)}")
            # check color
            Label.verify_color(label)

            # check attributes
            Attribute.verify(label.attributes)

            names.append(label.name)
            sequence_set.append(label.sequence)


class Attribute:
    def __init__(self, attr):
        self.id = attr['id'] if 'id' in attr else None
        self.name = attr['name']
        self.sequence = attr['sequence']
        self.mutable = attr['mutable']
        self.input_type = attr['input_type']
        self.default_value = attr['default_value']
        self.values = attr['values']

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def verify(attributes):
        names = []
        sequence_set = []
        for att in attributes:
            name = att.name
            if not name:
                raise InvalidLabelError('attribute name is required')
            if name in names:
                raise InvalidLabelError(
                    "attribute names for a label should be unique")
            if not isinstance(att.sequence, int) or att.sequence < 0:
                raise InvalidLabelError(
                    f"sequence value must be a positive integer.")
            if att.sequence in sequence_set:
                raise InvalidLabelError(
                    f"attribute sequence '{att.sequence}' is not unique.")

            error_msg = None
            if not isinstance(att.mutable, bool):
                error_msg = 'boolean value required for attr mutable'
            elif not att.input_type in ('checkbox', 'text', 'number', 'select', 'radio'):
                error_msg = 'invalid input_type for attribute'
            elif not isinstance(att.values, (list, tuple)):
                error_msg = 'list/tuple is required for attr values'
            elif not all(isinstance(value, str) for value in att.values):
                error_msg = 'all values should be string type'

            if error_msg:
                raise InvalidLabelError(error_msg)

            names.append(name)
            sequence_set.append(att.sequence)
