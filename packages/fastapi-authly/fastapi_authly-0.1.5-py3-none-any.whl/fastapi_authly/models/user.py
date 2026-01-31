from tortoise import fields
from tortoise.models import Model
from datetime import datetime


class User(Model):
    id = fields.IntField(primary_key=True, description="用户ID")
    email = fields.CharField(max_length=255, unique=True, description="邮箱（唯一）")
    username = fields.CharField(max_length=100, unique=True, description="用户名（唯一）")
    hashed_password = fields.CharField(max_length=255, description="加密后的密码")
    full_name = fields.CharField(max_length=255, null=True, description="全名")
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_superuser = fields.BooleanField(default=False, description="是否超级用户")

    # 时间字段
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    last_login = fields.DatetimeField(null=True, description="最后登录时间")

    class Meta:
        table = "users"
        table_description = "用户表"
        ordering = ["-created_at"]

    def __str__(self):
        return f"User(id={self.id}, username={self.username}, email={self.email})"

    async def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.now()
        await self.save(update_fields=["last_login"])