"""事件总线模块，直接使用 yitool 的 yi_event_bus 功能"""

# 直接从 yitool 导入事件总线核心功能
from yitool.yi_event_bus import YiEventBus, yi_event_bus
from yitool.yi_event_bus.decorators import emit_event, on_event

# 定义常用事件名称常量
EVENT_USER_REGISTERED = "user.registered"
EVENT_USER_LOGGED_IN = "user.logged_in"
EVENT_USER_LOGGED_OUT = "user.logged_out"
EVENT_RESOURCE_CREATED = "resource.created"
EVENT_RESOURCE_UPDATED = "resource.updated"
EVENT_RESOURCE_DELETED = "resource.deleted"

__all__ = [
    # 事件总线核心功能
    "yi_event_bus",
    "YiEventBus",
    "on_event",
    "emit_event",
    
    # 事件名称常量
    "EVENT_USER_REGISTERED",
    "EVENT_USER_LOGGED_IN",
    "EVENT_USER_LOGGED_OUT",
    "EVENT_RESOURCE_CREATED",
    "EVENT_RESOURCE_UPDATED",
    "EVENT_RESOURCE_DELETED",
]
