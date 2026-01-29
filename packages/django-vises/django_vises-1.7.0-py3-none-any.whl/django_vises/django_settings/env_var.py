from dataclasses import dataclass, field
from uuid import uuid4

from django_vises.deploy.deploy_stage import DeployStage


@dataclass
class EnvVarAbc:
    """settings.py 实例化为 EV
    在 settings 之外的地方通过 settings.EV 的方式使用, 因为这个实例的变量名是不可控的
    """

    # 部署环境
    DEPLOY_STAGE: str = DeployStage.PRD
    TZ: str = "UTC"

    # Django --- 默认值优先考虑使用 Django 默认值
    # --- 安全相关
    ALLOWED_HOSTS: list[str] = field(default_factory=list)  # dev 环境可以使用 [“*”]
    DEBUG: bool = False
    SECRET_KEY: str = f"django-secure-key-{uuid4().hex}"

    CSRF_TRUSTED_ORIGINS: list[str] = field(
        default_factory=list
    )  # 一般情况可以用 SECURE_PROXY_SSL_HEADER 解决

    # --- 数据库
    # postgresql://username:password@loaclhost:5432/dbname
    DATABASE_URI: str = (
        "sqlite://db.sqlite3?init_command=PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;"
    )

    # --- Cache
    # - https://docs.djangoproject.com/zh-hans/5.2/topics/cache
    CACHES_DEAFULT_BACKEND: str = "django.core.cache.backends.dummy.DummyCache"
    CACHES_DEAFULT_LOCATION: str = ""

    # 在线调试
    SENTRY_DSN: str = ""


# Example:
"""
# in `project.settings.py`

@dataclass
class EnvVar(EnvVarAbc, EnvWizard):
    class _(EnvWizard.Meta):
        env_file = True

    COUSTOM_VAR:str = "custom_var"

EV = EnvVar()
"""
