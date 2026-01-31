import enum
import uuid
import random
from copy import deepcopy
from typing import List


class Tool(enum.Enum):
    BoundingBox = "bounding-box"
    Segmentation = "segmentation"
    Polyline = "polyline"
    Polygon = "polygon"
    RotatedBoundingBox = "rotated-bounding-box"
    Ner = "ner"
    Point = "point"
    Pdf = "pdf"
    Brush = "brush"
    PCT = "pct"


class Classification(enum.Enum):
    Multi_dropdown = "multi-dropdown"
    Single_dropdown = "single-dropdown"
    Tree_dropdown = "tree-dropdown"
    Radio = "radio"
    Checkbox = "checkbox"
    Text = "text"
    Instance = "instance"
    Boolean = "boolean"


class Relation(enum.Enum):
    Single = "one-to-one"
    Group = "group"
    Many = "one-to-many"


def random_color():
    return "#" + ''.join([random.choice('ABCDEF0123456789') for i in range(6)])


class LabelOption:
    def __init__(self, value: str, schemaId: str = None):
        self.value = value
        if schemaId:
            self.schemaId = schemaId
        else:
            self.schemaId = uuid.uuid4().hex

    def toDict(self):
        return self.__dict__


class TreeOption:
    def __init__(self, title: str, key: str = None, value: str = None, children: List['TreeOption'] = None):
        if not children:
            children = []
        self.title = title
        self.children = children
        id = uuid.uuid4().hex
        if key:
            self.schemaId = key
        else:
            self.key = id
        if value:
            self.value = value
        else:
            self.value = id

    def toDict(self):
        d = deepcopy(self.__dict__)
        d['children'] = list(map(lambda t: t.toDict(), self.children))
        return d


class Category:
    def __init__(self, tool: str, title: str = "", required: bool = False, schemaId: str = None,
                 columnField: bool = False, color: str = None, shortcutKey: str = "",
                 classifications: List = None, options: List[LabelOption] = None):
        if not classifications:
            classifications = []
        if not options:
            options = []
        self.tool = tool
        self.title = title
        self.required = required
        self.columnField = columnField
        self.color = color
        self.shortcutKey = shortcutKey
        self.classifications = classifications
        self.options = options
        if schemaId:
            self.schemaId = schemaId
        else:
            self.schemaId = uuid.uuid4().hex
        if color:
            self.color = color
        else:
            self.color = random_color()

    def toDict(self):
        d = self.__dict__
        d['classifications'] = list(map(lambda t: t.toDict(), self.classifications))
        d['options'] = list(map(lambda t: t.toDict(), self.options))
        return d


class ClassificationCategory(Category):
    def __init__(self, classification: Classification, title: str = "", required: bool = False,
                 schemaId: str = None, columnField: bool = False, color: str = None, shortcutKey: str = "",
                 classifications: List = None, options: List[LabelOption] = None, treeOptions: List[TreeOption] = None,
                 frameSpecific: bool = False, parentOptionId: str = None, regex: str = None,
                 showDropdown: bool = False, richText: bool = False, exportName: str = None,
                 displayName: str = None, abbreviatedName: str = None, attributeType: str = None,
                 defaultValue: bool = None):
        if not classifications:
            classifications = []
        if not options:
            options = []
        if not treeOptions:
            treeOptions = []

        self.treeOptions = treeOptions
        options = options
        if treeOptions:
            options = flatten(treeOptions)

        super().__init__(classification.value, title, required, schemaId, columnField, color, shortcutKey,
                         classifications, options)
        self.regex = regex
        self.parentOptionId = parentOptionId
        self.frameSpecific = frameSpecific
        self.showDropdown = showDropdown
        self.richText = richText
        self.exportName = exportName
        self.displayName = displayName
        self.abbreviatedName = abbreviatedName
        self.attributeType = attributeType
        self.defaultValue = defaultValue

    def toDict(self):
        d = super(ClassificationCategory, self).toDict()
        d['regex'] = self.regex
        d['treeOptions'] = list(map(lambda t: t.toDict(), self.treeOptions))
        d['parentOptionId'] = self.parentOptionId
        d['frameSpecific'] = self.frameSpecific
        d['showDropdown'] = self.showDropdown
        d['richText'] = self.richText
        if self.exportName is not None:
            d['exportName'] = self.exportName
        if self.displayName is not None:
            d['displayName'] = self.displayName
        if self.abbreviatedName is not None:
            d['abbreviatedName'] = self.abbreviatedName
        if self.attributeType is not None:
            d['attributeType'] = self.attributeType
        if self.defaultValue is not None:
            d['defaultValue'] = self.defaultValue
        return d


class RelationCategory(Category):
    def __init__(self, relation: Relation, title: str = "", required: bool = False, schemaId: str = None,
                 columnField: bool = False, color: str = None, shortcutKey: str = "",
                 classifications: List[ClassificationCategory] = None, options: List[LabelOption] = None):
        super().__init__(relation.value, title, required, schemaId, columnField, color, shortcutKey, classifications,
                         options)


class ToolCategory(Category):
    def __init__(self, tool: Tool, title: str = "", required: bool = False, schemaId: str = None,
                 columnField: bool = False, color: str = None, shortcutKey: str = "",
                 classifications: List[ClassificationCategory] = None, options: List[LabelOption] = None):
        super().__init__(tool.value, title, required, schemaId, columnField, color, shortcutKey, classifications,
                         options)


def flatten(x, title=None):
    resp = []
    if title:
        title = '%s / ' % title
    else:
        title = ''
    if isinstance(x, List):
        for i in x:
            o = LabelOption(value='%s%s' % (title, i.title), schemaId=i.key)
            resp.append(o)
            for j in i.children:
                resp += flatten(j, o.value)
    else:
        o = LabelOption(value='%s%s' % (title, x.title), schemaId=x.key)
        resp.append(o)
        for j in x.children:
            resp += flatten(j, o.value)
    return resp
