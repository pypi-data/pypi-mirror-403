import sys
import warnings
from datetime import datetime, timedelta
from typing import Any

if sys.version_info >= (3, 14):
    from uuid import uuid7
else:
    from uuid_backport import uuid7

from django.db import models
from django.utils.timezone import now


class RecordManager(models.Manager):
    def get_last_x_hour_queryset(self, hours):
        return (
            super()
            .get_queryset()
            .filter(created_time__gte=now() - timedelta(hours=hours))
        )

    def get_last_x_day_queryset(self, days):
        return (
            super()
            .get_queryset()
            .filter(created_time__gte=now() - timedelta(days=days))
        )


class RecordAbcWithoutIdAbc(models.Model):
    """基本数据库模型 - 日志型 - 无 id
    创建时间，无更新需求
    """

    # Django 5.2 开始支持联合主键,继承后添加主键字段

    # 记录创建时间
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class RecordAbc(RecordAbcWithoutIdAbc):
    """基本数据库模型 - 记录型
    创建时间，无更新需求
    """

    id = models.UUIDField(primary_key=True, unique=True, default=uuid7, editable=False)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.id}"


class ObjectWithoutIdAbc(models.Model):
    """基本数据库模型 - 对象型 - 无 id
    创建时间，最后更新时间, 需要继承者自行实现 __str__()
    """

    # 记录创建时间
    created_time = models.DateTimeField(auto_now_add=True)

    # 记录最后更新时间
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ObjectAbc(ObjectWithoutIdAbc):
    """基本数据库模型 - 对象型
    创建时间，最后更新时间
    """

    id = models.UUIDField(primary_key=True, unique=True, default=uuid7, editable=False)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.id}"


class KeyValueAbc(ObjectWithoutIdAbc):
    """基本数据库模型 - 键值对型 - key:value
    创建时间，最后更新时间
    """

    # key
    key = models.TextField(primary_key=True, unique=True)

    # value
    value = models.JSONField()

    class Meta:
        abstract = True


class GroupKeyValueManager(models.Manager):
    def get_first(self, key: str, group: str | None = None):
        return super().get_queryset().filter(group=group, key=key).first()

    def get_object(self, key: str, group: str | None = None):
        return super().get_queryset().filter(group=group, key=key).get()

    def get_value(self, key: str, group: str | None = None) -> Any:
        obj = self.get_object(key=key, group=group)

        return obj.value

    def set_value(self, key: str, value, group: str | None = None):
        self.get_queryset().update_or_create(
            group=group, key=key, defaults={"value": value}
        )
        return

    def get_value_and_update_time(  # TODO:这个应该被废弃,使用 get_object 替代
        self, key: str, group: str | None = None
    ) -> tuple[list, datetime | None]:
        warnings.warn(
            "please use .get_object()/.get_first() instead", DeprecationWarning
        )

        obj = self.get_object(key=key, group=group)

        return obj.value, obj.updated_time

    def get_values_by_group(self, group: str) -> dict:
        return dict(
            self.get_queryset()
            .filter(group=group)
            .values_list("key", "value", flat=True)
        )


class GroupKeyValueKeyAbc(KeyValueAbc):
    """基本数据库模型 - 键值对型 - group.key:value
    创建时间，最后更新时间
    """

    # https://docs.djangoproject.com/zh-hans/5.2/topics/composite-primary-key/
    pk = models.CompositePrimaryKey("group", "key")

    # group - 可选的一级分组
    group = models.TextField(null=False)
    # key - 必须存在的二级分组
    key = models.TextField(null=False)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["group"]),
            models.Index(fields=["key"]),
        ]

    def __str__(self):
        return f"{self.group}.{self.key}:{self.value}"
