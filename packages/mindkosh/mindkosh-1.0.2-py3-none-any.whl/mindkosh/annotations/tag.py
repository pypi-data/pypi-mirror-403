class Tag:
    def __init__(
        self,
        id,
        frame,
        label_id,
        group,
        source,
        attributes,
        **kwargs
    ):
        self.id = id
        self.frame = frame
        self.label_id = label_id
        self.group = group
        self.source = source
        self.attributes = attributes
        self.label_name = kwargs['label_name']

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.label_name
