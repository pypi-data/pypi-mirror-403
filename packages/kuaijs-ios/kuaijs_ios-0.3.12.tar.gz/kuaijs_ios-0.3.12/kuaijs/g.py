from typing import Final

# 平台信息（"ios" 或 "android"）
platform: Final[str] = ""

# 应用版本号（字符串），例如 "1.2.3"
appVersion: Final[str] = ""

# 应用构建号（整数），例如 123
appBuildNumber: Final[int] = 0

# 应用名称，例如 "快点JS"
appName: Final[str] = ""

# 应用包名（Bundle ID），例如 "com.example.app"
appBundleId: Final[str] = ""

# 是否处于调试模式（根据宿主环境设置）
isDebug: Final[bool] = False

# 应用的 package.json 内容
packageJson: Final[dict] = {}


def takeMeToFront() -> bool:
    """将宿主应用切入前台"""
    return True


def restartScript(delay_ms: int = 2000):
    """重启脚本：先异步停止，再在主线程延时重启。"""
    pass

def importClass(className: str) -> any:
    """导入类对象"""
    pass

def loadDex(path: str) -> bool:
    """加载 dex、apk 文件"""
    pass

def getContext() -> any:
    """获取当前上下文"""
    pass