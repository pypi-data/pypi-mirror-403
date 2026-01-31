import json
from typing import Optional
from datetime import datetime, date, time
from pydantic import BaseModel, Field, ConfigDict

from sqlalchemy import Column, BigInteger, String, Float, DateTime, Text, Time, Date, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import UniqueConstraint

do_base = declarative_base()

class Batch(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持从 ORM 模型转换

    id: Optional[int] = None
    total_cnt: Optional[int] = Field(default=0)
    success_cnt: Optional[int] = Field(default=0)
    create_time: Optional[datetime] = Field(default_factory=datetime.now)
    update_time: Optional[datetime] = Field(default_factory=datetime.now)

    @classmethod
    def from_orm(cls, orm_obj: "BatchDO") -> "Batch":
        return cls.model_validate(orm_obj.to_dict())

    def to_orm(self) -> "BatchDO":
        return BatchDO(
            id=self.id,
            total_cnt=self.total_cnt,
            success_cnt=self.success_cnt,
            create_time=self.create_time,
            update_time=self.update_time,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Batch":
        """从字典创建Keyword对象"""
        return cls.model_validate(data)

    def __str__(self) -> str:
        return self.model_dump_json()

class BatchDO(do_base, SerializerMixin):
    __tablename__ = 'batch'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    id = Column(BigInteger, primary_key=True)
    total_cnt = Column(BigInteger, nullable=False)
    success_cnt = Column(BigInteger, nullable=False)
    create_time = Column(DateTime, server_default=func.now(), comment='创建时间')
    update_time = Column(DateTime, server_default=func.now(),
                         onupdate=func.now(), comment='更新时间')

    def __str__(self):
        return f"<{self.__tablename__} {self.to_dict()}>"


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持从 ORM 模型转换

    id: Optional[int] = None
    user_id: Optional[int] = Field(default=None, comment='所属用户ID')
    keywords: Optional[list] = Field(default_factory=list, comment='监测关键词列表')
    start_time: Optional[datetime] = Field(default=None, comment='监测起始时间')
    end_time: Optional[datetime] = Field(default=None, comment='监测终止时间')
    interval: Optional[int] = Field(default=60, comment='监测频率(分钟)')
    status: Optional[int] = Field(default=1, comment='状态: 0-停用, 1-启用')
    next_run_time: Optional[datetime] = Field(default=None, comment='下一次计划生成报告的时间')
    create_time: Optional[datetime] = Field(default_factory=datetime.now, comment='创建时间')
    update_time: Optional[datetime] = Field(default_factory=datetime.now, comment='更新时间')
    is_deleted: Optional[int] = Field(default=0, comment='逻辑删除')

    @classmethod
    def from_orm(cls, orm_obj: "TaskDO") -> "Task":
        return cls.model_validate(orm_obj.to_dict())

    def to_orm(self) -> "TaskDO":
        return TaskDO(
            id=self.id,
            user_id=self.user_id,
            keywords=self.keywords,
            start_time=self.start_time,
            end_time=self.end_time,
            interval=self.interval,
            status=self.status,
            next_run_time=self.next_run_time,
            create_time=self.create_time,
            update_time=self.update_time,
            is_deleted=self.is_deleted,
        )

    def __str__(self) -> str:
        return self.model_dump_json()


class TaskDO(do_base, SerializerMixin):
    __tablename__ = 'task'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False, comment='所属用户ID')
    _keywords = Column('keywords', JSON, nullable=False, comment='监测关键词列表')
    start_time = Column(DateTime, comment='监测起始时间')
    end_time = Column(DateTime, comment='监测终止时间')
    interval = Column(Integer, nullable=False, comment='监测频率(分钟)')
    status = Column(Integer, default=1, comment='状态: 0-停用, 1-启用')
    next_run_time = Column(DateTime, comment='下一次计划生成报告的时间')
    create_time = Column(DateTime, server_default=func.now(), comment='创建时间')
    update_time = Column(DateTime, server_default=func.now(),
                         onupdate=func.now(), comment='更新时间')
    is_deleted = Column(Integer, default=0, comment='逻辑删除')

    @hybrid_property
    def keywords(self):
        """获取keywords字段"""
        return self._keywords if self._keywords else []

    @keywords.setter
    def keywords(self, value):
        """设置keywords字段"""
        self._keywords = value

    def to_dict(self):
        """重写to_dict方法"""
        result = super().to_dict()
        if '_keywords' in result:
            result['keywords'] = self.keywords
            del result['_keywords']
        return result

    def __str__(self):
        return f"<{self.__tablename__} {self.to_dict()}>"


class Keyword(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持从 ORM 模型转换

    id: Optional[int] = None
    keyword: Optional[str] = Field(default=None, max_length=255)
    heat: Optional[float] = Field(default=0)
    create_time: Optional[datetime] = Field(default_factory=datetime.now)
    update_time: Optional[datetime] = Field(default_factory=datetime.now)

    @classmethod
    def from_orm(cls, orm_obj: "KeywordDO") -> "Keyword":
        return cls.model_validate(orm_obj.to_dict())

    def to_orm(self) -> "KeywordDO":
        return KeywordDO(
            id=self.id,
            keyword=self.keyword,
            heat=self.heat,
            create_time=self.create_time,
            update_time=self.update_time,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Keyword":
        """从字典创建Keyword对象"""
        return cls.model_validate(data)

    def __str__(self) -> str:
        return self.model_dump_json()

class KeywordDO(do_base, SerializerMixin):
    __tablename__ = 'keyword'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    id = Column(BigInteger, primary_key=True)
    keyword = Column(String(255), nullable=False)
    heat = Column(Float, default=0)
    create_time = Column(DateTime, server_default=func.now(), comment='创建时间')
    update_time = Column(DateTime, server_default=func.now(),
                        onupdate=func.now(), comment='更新时间')

    def __str__(self):
        return f"<{self.__tablename__} {self.to_dict()}>"


class Slice(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持 ORM 转换

    id: Optional[int] = None
    task_id: Optional[int] = Field(None, comment='任务ID')
    title: Optional[str] = Field(max_length=255, comment='切片标题/事件名')
    summary: Optional[str] = None
    heat: Optional[float] = Field(0.0, comment='热度值')
    sentiment: Optional[str] = Field(default="NEUTRAL", comment='情感倾向')
    event_time: Optional[datetime] = Field(default=None, comment='实际事件发生时间')
    create_time: Optional[datetime] = Field(default_factory=datetime.now, comment='记录创建时间')

    news_cnt: Optional[int] = Field(default=0, exclude=True)
    @classmethod
    def from_orm(cls, orm_obj: "SliceDO") -> "Slice":
        """从数据库模型转换（直接使用Pydantic内置解析）"""
        return cls.model_validate(orm_obj.to_dict())

    def to_orm(self) -> "SliceDO":
        """转换为数据库模型"""
        return SliceDO(
            id=self.id,
            task_id=self.task_id,
            title=self.title,
            summary=self.summary,
            heat=self.heat,
            sentiment=self.sentiment,
            event_time=self.event_time,
            create_time=self.create_time
        )

    def __str__(self) -> str:
        return self.model_dump_json()

class SliceDO(do_base, SerializerMixin):
    __tablename__ = 'slice'
    __table_args__ = {'mysql_charset': 'utf8mb4'}
    __allow_unmapped__ = True

    id = Column(BigInteger, primary_key=True)
    task_id = Column(BigInteger, nullable=False, comment='关联任务ID')
    title = Column(String(255), nullable=False, comment="切片标题/事件名")
    heat = Column(Float, default=0.0, comment='热度值')
    sentiment = Column(String(32), default="NEUTRAL", comment="情感倾向")
    summary = Column(Text, comment="切片摘要")
    event_time = Column(DateTime, comment="实际事件发生时间")
    create_time = Column(DateTime, server_default=func.now(), comment='记录创建时间')

    def __str__(self):
        return f"<{self.__tablename__} {self.to_dict()}>"

class News(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持从 ORM 模型转换

    id: Optional[int] = None
    task_id: Optional[int] = None
    slice_id: Optional[int] = None
    title: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None, max_length=512)
    publish_time: Optional[datetime] = None
    source: Optional[str] = Field(default=None, max_length=64)
    sentiment: Optional[str] = Field(default="NEUTRAL")
    create_time: Optional[datetime] = Field(default_factory=datetime.now)

    @classmethod
    def from_orm(cls, orm_obj: "NewsDO") -> "News":
        return cls.model_validate(orm_obj.to_dict())

    def to_orm(self) -> "NewsDO":
        return NewsDO(
            id=self.id,
            task_id=self.task_id,
            slice_id=self.slice_id,
            title=self.title,
            content=self.content,
            url=self.url,
            publish_time=self.publish_time,
            source=self.source,
            sentiment=self.sentiment,
            create_time=self.create_time
        )

    @classmethod
    def from_dict(cls, data: dict) -> "News":
        """从字典创建News对象"""
        return cls.model_validate(data)

    def __str__(self) -> str:
        return self.model_dump_json()

class NewsDO(do_base, SerializerMixin):
    __tablename__ = 'news'
    __table_args__ = {'mysql_charset': 'utf8mb4'}
    __allow_unmapped__ = True

    id = Column(BigInteger, primary_key=True)
    task_id = Column(BigInteger, nullable=False, comment='关联任务ID')
    slice_id = Column(BigInteger, comment='关联事件ID/切片ID')
    title = Column(String(255), nullable=False, comment='标题')
    content = Column(Text, comment='内容摘要')
    url = Column(String(512), nullable=False, comment='原文链接')
    publish_time = Column(DateTime, nullable=False, comment='发布时间')
    source = Column(String(64), nullable=False, comment='来源')
    sentiment = Column(String(32), default='NEUTRAL', comment='情感倾向')
    create_time = Column(DateTime, server_default=func.now(), comment='入库时间')

    def __str__(self):
        return f"<{self.__tablename__} {self.to_dict()}>"

    update_time = Column(DateTime, server_default=func.now(),
                         onupdate=func.now(), comment='更新时间')

    # 原始字段，存储JSON字符串
    _ext = Column('ext', Text, comment='拓展字段')

    # 业务字段，不持久化
    slice_pos: Optional[int] = None

    @hybrid_property
    def ext(self):
        """获取ext字段时会自动将JSON字符串转为字典"""
        if self._ext is None:
            return {}
        try:
            return json.loads(self._ext)
        except (json.JSONDecodeError, TypeError):
            return {}

    @ext.setter
    def ext(self, value):
        """设置ext字段时会自动将字典转为JSON字符串"""
        if value is None:
            self._ext = None
        elif isinstance(value, str):
            # 如果是字符串，直接存储（假设已经是JSON字符串）
            self._ext = value
        else:
            # 如果是字典或其他可序列化对象，转为JSON
            self._ext = json.dumps(value, ensure_ascii=False)

    def to_dict(self):
        """重写SerializerMixin的to_dict方法，确保ext返回字典"""
        result = super().to_dict()
        if '_ext' in result:
            result['ext'] = self.ext  # 使用property返回字典
            del result['_ext']
        return result

    def __str__(self):
        return f"<{self.__tablename__} {self.to_dict()}>"

class SourceKeywordOffset(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持ORM转换

    id: Optional[int] = None
    keyword_id: Optional[int] = Field(None, comment='关键词id')
    source: Optional[str] = Field(None, max_length=32, comment='渠道')
    create_time: Optional[datetime] = Field(default=datetime.min, comment='创建时间')
    update_time: Optional[datetime] = None

    @classmethod
    def from_orm(cls, orm_obj: "SourceKeywordOffsetDO") -> "SourceKeywordOffset":
        """从数据库模型转换"""
        return cls.model_validate(orm_obj.to_dict())

    def to_orm(self) -> "SourceKeywordOffsetDO":
        """转换为数据库模型"""
        return SourceKeywordOffsetDO(
            id=self.id,
            keyword_id=self.keyword_id,
            source=self.source,
            create_time=self.create_time,
            update_time=self.update_time
        )

    def __str__(self) -> str:
        return self.model_dump_json()

class SourceKeywordOffsetDO(do_base, SerializerMixin):
    __tablename__ = 'source_keyword_offset'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    id = Column(BigInteger, primary_key=True)
    keyword_id = Column(BigInteger, nullable=False, comment='关键词id')
    source = Column(String(255), nullable=False, comment='渠道')
    create_time = Column(DateTime, server_default=func.now(), comment='创建时间')
    update_time = Column(DateTime, server_default=func.now(),
                        onupdate=func.now(), comment='更新时间')

    def __str__(self):
        return f"<SourceKeywordOffsetDO(id={self.id}, keyword_id={self.keyword_id}, source={self.source})>"

class PushConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持 ORM 转换

    id: Optional[int] = None
    user_id: Optional[int] = None
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    push_frequency: Optional[int] = None
    expire_date: Optional[date] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    @classmethod
    def from_orm(cls, orm_obj: "PushConfigDO") -> "PushConfig":
        """从数据库模型转换"""
        return cls.model_validate(orm_obj.to_dict())

    def to_orm(self) -> "PushConfigDO":
        """转换为数据库模型"""
        return PushConfigDO(
            id=self.id,
            user_id=self.user_id,
            name=self.name,
            start_time=self.start_time,
            end_time=self.end_time,
            push_frequency=self.push_frequency,
            expire_date=self.expire_date,
            create_time=self.create_time,
            update_time=self.update_time
        )

    def __str__(self) -> str:
        return self.model_dump_json()

class PushConfigDO(do_base, SerializerMixin):
    __tablename__ = 'push_config'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'comment': '报告推送配置表'}

    id = Column(BigInteger, primary_key=True, comment='主键ID')
    user_id = Column(BigInteger, nullable=False, comment='用户ID')
    name = Column(String(32), nullable=False, comment='配置名称')
    start_time = Column(Time, nullable=False, comment='一天中推送开始的时间')
    end_time = Column(Time, nullable=False, comment='一天中推送结束的时间')
    push_frequency = Column(BigInteger, nullable=True, comment='推送频率（分钟）')
    expire_date = Column(Date, nullable=False, comment='过期时间')
    create_time = Column(DateTime, default=func.now(), nullable=True, comment='创建时间')
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=True,
                         comment='更新时间')

    def __str__(self):
        return f"<{self.__tablename__} {self.to_dict()}>"

class PushConfigKeyword(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持 ORM 转换

    id: Optional[int] = None
    config_id: Optional[int] = None
    keyword_id: Optional[int] = None
    create_time: Optional[datetime] = None

    @classmethod
    def from_orm(cls, orm_obj: "PushConfigKeywordDO") -> "PushConfigKeyword":
        """从数据库模型转换"""
        return cls.model_validate(orm_obj.to_dict())

    def to_orm(self) -> "PushConfigKeywordDO":
        """转换为数据库模型"""
        return PushConfigKeywordDO(
            id=self.id,
            config_id=self.config_id,
            keyword_id=self.keyword_id,
            create_time=self.create_time
        )

    def __str__(self) -> str:
        return self.model_dump_json()

class PushConfigKeywordDO(do_base, SerializerMixin):
    __tablename__ = 'push_config_keyword'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    id = Column(BigInteger, primary_key=True)
    config_id = Column(BigInteger, nullable=False)
    keyword_id = Column(BigInteger, nullable=False)
    create_time = Column(DateTime, server_default=func.now(),
                         onupdate=func.now(), comment='创建时间')

    def __str__(self):
        return f"<{self.__tablename__} {self.to_dict()}>"

class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持 ORM 转换

    id: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    status: Optional[int] = None

    @classmethod
    def from_orm(cls, orm_obj: "UserDO") -> "User":
        """从数据库模型转换"""
        return cls.model_validate(orm_obj.to_dict())

    def to_orm(self) -> "UserDO":
        """转换为数据库模型"""
        return UserDO(
            id=self.id,
            username=self.username,
            password=self.password,
            phone=self.phone,
            avatar_url=self.avatar_url,
            create_time=self.create_time,
            update_time=self.update_time,
            status=self.status
        )

    def __str__(self) -> str:
        return self.model_dump_json()

class UserDO(do_base, SerializerMixin):
    __tablename__ = 'user'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'comment': '用户表'}

    id = Column(BigInteger, primary_key=True, comment='主键ID')
    username = Column(String(50), nullable=False, comment='用户名')
    password = Column(String(128), nullable=False, comment='密码')
    phone = Column(String(20), nullable=False, comment='电话号码')
    avatar_url = Column(String(256), nullable=True, default=None, comment='头像链接')
    create_time = Column(DateTime, default=func.now(), nullable=True, comment='创建时间')
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=True,
                         comment='更新时间')
    status = Column(BigInteger, nullable=False, comment='状态')

    def __str__(self):
        return f"<{self.__tablename__} {self.to_dict()}>"

class ProxyUsage(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 支持从 ORM 模型转换

    id: Optional[int] = None
    source: Optional[str] = Field(None, max_length=32, comment='渠道')
    ip: Optional[str] = Field(None, max_length=64, comment='代理ip')
    success_cnt: Optional[int] = Field(default=0, comment='成功获取次数')
    total_cnt: Optional[int] = Field(default=0, comment='总获取次数')
    create_time: Optional[datetime] = Field(default_factory=datetime.now, comment='代理创建时间')
    update_time: Optional[datetime] = Field(default_factory=datetime.now, comment='代理更新时间')

    # 非持久化字段
    success_rate: Optional[float] = Field(default=0.0, exclude=True, comment='成功率')

    @classmethod
    def from_orm(cls, orm_obj: "ProxyUsageDO") -> "ProxyUsage":
        """从数据库模型转换"""
        return cls.model_validate(orm_obj.to_dict())

    def to_orm(self) -> "ProxyUsageDO":
        """转换为数据库模型"""
        return ProxyUsageDO(
            id=self.id,
            source=self.source,
            ip=self.ip,
            success_cnt=self.success_cnt,
            total_cnt=self.total_cnt,
            create_time=self.create_time,
            update_time=self.update_time,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyUsage":
        """从字典创建ProxyUsage对象"""
        return cls.model_validate(data)

    def calculate_success_rate(self) -> float:
        """计算成功率"""
        if self.total_cnt and self.total_cnt > 0:
            return round((self.success_cnt or 0) / self.total_cnt * 100, 2)
        return 0.0
    

    def __str__(self) -> str:
        return self.model_dump_json()


class ProxyUsageDO(do_base, SerializerMixin):
    __tablename__ = 'proxy_usage'
    __table_args__ = (
        UniqueConstraint('source', 'ip', name='uk_source_ip'),
        {'mysql_charset': 'utf8mb4', 'comment': '代理使用情况表'}
    )
    __allow_unmapped__ = True  # 允许业务定义未持久化的拓展字段

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(32), nullable=False, comment='渠道')
    ip = Column(String(64), nullable=False, comment='代理ip')
    success_cnt = Column(BigInteger, default=0, comment='成功获取次数')
    total_cnt = Column(BigInteger, default=0, comment='总获取次数')
    create_time = Column(DateTime, server_default=func.now(), comment='代理创建时间')
    update_time = Column(DateTime, server_default=func.now(),
                        onupdate=func.now(), comment='代理更新时间')

    # 业务字段，不持久化
    success_rate: Optional[float] = None

    def calculate_success_rate(self) -> float:
        """计算成功率"""
        if self.total_cnt and self.total_cnt > 0:
            return round(self.success_cnt / self.total_cnt * 100, 2)
        return 0.0

    def __str__(self):
        return f"<{self.__tablename__} {self.to_dict()}>"