import enum

class SourceEnum(enum.Enum):
    Douyin = "douyin"
    Toutiao = "toutiao"
    Weibo = "weibo"
    Wechat = "wechat"
    SouthWeekend = "south_weekend"

class ContextField(enum.Enum):
    Batch = "batch"
    Source = "source"
    Task = "task"
    Slice = "slice"
    News = "news"
    User = "user"
    PushConfig = "push_config"
    PushConfigKeyword = "push_config_keyword"
    SourceKeywordOffset = "source_keyword_offset"

class WebDriverType(enum.Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"
