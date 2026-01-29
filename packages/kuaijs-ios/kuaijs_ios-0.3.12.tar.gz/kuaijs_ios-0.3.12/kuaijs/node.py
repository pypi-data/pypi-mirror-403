from typing import Any, Dict, List, Literal, Optional, TypedDict, Union


class SelectorParams(TypedDict, total=False):
    """节点选择器参数

    属性:
      maxDepth: 代表要获取节点的层级，越少速度越快，默认 50

    示例:
      >>> from kuaijs.node import createNodeSelector
      >>> selector = createNodeSelector({"maxDepth": 10})
    """

    maxDepth: Optional[int]  # 最大层级深度默认 50


class NodeBounds:
    """节点边界

    属性:
      x: x 坐标
      y: y 坐标
      width: 宽度
      height: 高度
      centerX: 节点中心 x 坐标
      centerY: 节点中心 y 坐标
    """

    x: int
    y: int
    width: int
    height: int
    centerX: int
    centerY: int

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 0,
        centerX: int = 0,
        centerY: int = 0,
    ):
        """创建节点边界对象（类型提示用）

        参数:
          x: x 坐标
          y: y 坐标
          width: 宽度
          height: 高度
          centerX: 节点中心 x 坐标
          centerY: 节点中心 y 坐标

        返回:
          None

        示例:
          >>> from kuaijs.node import NodeBounds
          >>> b = NodeBounds(x=0, y=0, width=100, height=50)
          >>> b.centerX
          0
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.centerX = centerX
        self.centerY = centerY


class NodeInfo:
    """节点信息（类型提示用）"""

    id: str = ""  # 节点 ID
    identifier: str = ""  # 节点标识符
    label: str = ""  # 节点标签
    type: str = ""  # 节点类型
    value: str = ""  # 节点值
    placeholderValue: str = ""  # 节点占位符值
    title: str = ""  # 节点标题
    visible: bool = False  # 是否可见
    enabled: bool = False  # 是否启用
    bounds: NodeBounds = NodeBounds()
    depth: int = 0  # 节点层级深度
    index: int = 0  # 节点索引
    parentId: str = ""  # 父节点 ID
    childCount: int = 0  # 子节点数量

    def clickCenter(self) -> bool:
        """点击节点中心

        返回:
          bool: 是否点击成功

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> n = createNodeSelector().getOneNodeInfo()
          >>> ok = n.clickCenter() if n else False
        """
        return True

    def clickRandom(self) -> bool:
        """点击节点随机位置

        返回:
          bool: 是否点击成功

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> n = createNodeSelector().getOneNodeInfo()
          >>> ok = n.clickRandom() if n else False
        """
        return True

    def hittable(self) -> bool:
        """节点是否可接收事件（用于判断是否显示在屏幕上）

        返回:
          bool: 是否可接收事件

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> n = createNodeSelector().getOneNodeInfo()
          >>> visible_on_screen = n.hittable() if n else False
        """
        return True

    def parent(self) -> Optional["NodeInfo"]:
        """获取父节点

        返回:
          Optional[NodeInfo]: 父节点信息，不存在时返回 None

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> n = createNodeSelector().getOneNodeInfo()
          >>> p = n.parent() if n else None
        """
        return None

    def child(self, index: int) -> Optional["NodeInfo"]:
        """获取子节点

        参数:
          index: 子节点索引

        返回:
          Optional[NodeInfo]: 子节点信息，不存在时返回 None

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> n = createNodeSelector().getOneNodeInfo()
          >>> c0 = n.child(0) if n else None
        """
        return None

    def allChildren(self) -> List["NodeInfo"]:
        """获取所有子节点

        返回:
          List[NodeInfo]: 子节点数组

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> n = createNodeSelector().getOneNodeInfo()
          >>> children = n.allChildren() if n else []
        """
        return []

    def siblings(self) -> List["NodeInfo"]:
        """获取所有兄弟节点

        返回:
          List[NodeInfo]: 兄弟节点数组

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> n = createNodeSelector().getOneNodeInfo()
          >>> arr = n.siblings() if n else []
        """
        return []

    def previousSiblings(self) -> List["NodeInfo"]:
        """获取所有前兄弟节点

        返回:
          List[NodeInfo]: 前兄弟节点数组

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> n = createNodeSelector().getOneNodeInfo()
          >>> arr = n.previousSiblings() if n else []
        """
        return []

    def nextSiblings(self) -> List["NodeInfo"]:
        """获取所有后兄弟节点

        返回:
          List[NodeInfo]: 后兄弟节点数组

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> n = createNodeSelector().getOneNodeInfo()
          >>> arr = n.nextSiblings() if n else []
        """
        return []

    def toJSON(self) -> Dict[str, Any]:
        """转换为 JSON 对象（用于支持 JSON.stringify/序列化）

        返回:
          Dict[str, Any]: 包含节点属性的字典

        示例:
          >>> import json
          >>> from kuaijs.node import createNodeSelector
          >>> n = createNodeSelector().getOneNodeInfo()
          >>> s = json.dumps(n.toJSON(), ensure_ascii=False) if n else "{}"
        """
        return {}


class NodeSelector:
    """节点选择器

    用于按条件选择节点，并拉取节点信息。

    示例:
      >>> from kuaijs.node import createNodeSelector
      >>> selector = createNodeSelector({"maxDepth": 50})
      >>> selector = selector.label("登录").enabled(True)
      >>> nodes = selector.getNodeInfo()
    """

    def __init__(self, params: Optional[SelectorParams] = None):
        """创建节点选择器（类型提示用）

        参数:
          params: 选择器参数（如 maxDepth）

        返回:
          None
        """
        self.params = params or {"maxDepth": 50}

    def releaseNode(self) -> None:
        """释放内存

        返回:
          None

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> selector = createNodeSelector()
          >>> selector.releaseNode()
        """
        return None

    def clearSelector(self) -> "NodeSelector":
        """清除所有选择条件

        返回:
          NodeSelector: 当前选择器（支持链式调用）

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> selector = createNodeSelector().label("A").clearSelector()
        """
        return self

    def loadNode(self, timeout: int = 5000) -> "NodeSelector":
        """加载节点数据

        参数:
          timeout: 超时时间，单位毫秒，默认 5000

        返回:
          NodeSelector: 当前选择器（支持链式调用）

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> selector = createNodeSelector().loadNode(5000)
        """
        return self

    def xml(self, timeout: int = 5000) -> Optional[str]:
        """获取节点 XML 字符串

        参数:
          timeout: 超时时间，单位毫秒，默认 5000

        返回:
          Optional[str]: 节点 XML 字符串

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> xml = createNodeSelector().xml()
        """
        return None

    def getNodeInfo(self, timeout: int = 5000) -> List[NodeInfo]:
        """获取节点信息

        参数:
          timeout: 超时时间，单位毫秒，默认 5000

        返回:
          List[NodeInfo]: 节点信息数组

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> nodes = createNodeSelector().getNodeInfo()
        """
        return []

    def getOneNodeInfo(self, timeout: int = 5000) -> Optional[NodeInfo]:
        """获取一个节点信息

        参数:
          timeout: 超时时间，单位毫秒，默认 5000

        返回:
          Optional[NodeInfo]: 节点信息，不存在时返回 None

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> node = createNodeSelector().getOneNodeInfo()
        """
        return None

    def id(self, id: str) -> "NodeSelector":
        """通过节点 id 选择节点

        参数:
          id: 节点 id

        返回:
          NodeSelector: 当前选择器（支持链式调用）

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> selector = createNodeSelector().id("node_id")
        """
        return self

    def xpath(self, path: str) -> "NodeSelector":
        """通过 xpath 选择节点

        参数:
          path: xpath 路径

        返回:
          NodeSelector: 当前选择器（支持链式调用）

        示例:
          >>> from kuaijs.node import createNodeSelector
          >>> selector = createNodeSelector().xpath("//XCUIElementTypeButton")
        """
        return self

    def label(self, label: str) -> "NodeSelector":
        """通过标签选择节点

        参数:
          label: 节点标签

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def labelMatch(self, match: str) -> "NodeSelector":
        """通过标签匹配选择节点

        参数:
          match: 匹配字符串

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def title(self, title: str) -> "NodeSelector":
        """通过标题选择节点

        参数:
          title: 节点标题

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def titleMatch(self, match: str) -> "NodeSelector":
        """通过标题匹配选择节点

        参数:
          match: 匹配字符串

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def identifier(self, identifier: str) -> "NodeSelector":
        """通过节点标识符选择节点

        参数:
          identifier: 节点标识符

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def identifierMatch(self, match: str) -> "NodeSelector":
        """通过节点标识符匹配选择节点

        参数:
          match: 匹配字符串

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def type(self, type_title: str) -> "NodeSelector":
        """通过类型选择节点

        参数:
          type_title: 节点类型

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def typeMatch(self, match: str) -> "NodeSelector":
        """通过类型匹配选择节点

        参数:
          match: 匹配字符串

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def value(self, value: str) -> "NodeSelector":
        """通过值选择节点

        参数:
          value: 节点值

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def valueMatch(self, match: str) -> "NodeSelector":
        """通过值匹配选择节点

        参数:
          match: 匹配字符串

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def placeholderValue(self, placeholderValue: str) -> "NodeSelector":
        """通过占位符值选择节点

        参数:
          placeholderValue: 节点占位符值

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def placeholderValueMatch(self, match: str) -> "NodeSelector":
        """通过占位符值匹配选择节点

        参数:
          match: 匹配字符串

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def enabled(self, flag: bool) -> "NodeSelector":
        """通过启用状态选择节点

        参数:
          flag: 是否启用

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def visible(self, flag: bool) -> "NodeSelector":
        """通过可见性选择节点

        参数:
          flag: 是否可见

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def index(self, idx: int) -> "NodeSelector":
        """通过索引选择节点

        参数:
          idx: 节点索引

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def depth(self, d: int) -> "NodeSelector":
        """通过深度选择节点

        参数:
          d: 节点层级

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def childCount(self, childCount: Union[int, str]) -> "NodeSelector":
        """通过子节点数量选择节点

        参数:
          childCount: 子节点数量（支持 int 或表达式字符串）

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self

    def bounds(self, x: int, y: int, width: int, height: int) -> "NodeSelector":
        """通过节点位置选择节点

        参数:
          x: x 坐标
          y: y 坐标
          width: 宽度
          height: 高度

        返回:
          NodeSelector: 当前选择器（支持链式调用）
        """
        return self


def createNodeSelector(params: Optional[SelectorParams] = None) -> NodeSelector:
    """创建节点选择器

    参数:
      params: maxDepth 最大层级深度默认 50
    返回:
      NodeSelector: 链式选择器

    示例:
      >>> from kuaijs.node import createNodeSelector
      >>> selector = createNodeSelector({"maxDepth": 20})
      >>> nodes = selector.getNodeInfo()
    """
    return NodeSelector(params)
