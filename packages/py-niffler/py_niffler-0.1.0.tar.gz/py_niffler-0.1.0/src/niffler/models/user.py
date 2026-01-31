from tortoise import fields

from .__proto__ import ExternalModel


class User(ExternalModel):
    username = fields.CharField(max_length=32, description="用户名")
    password = fields.CharField(max_length=32, description="密码")
    permissions = fields.JSONField(default=list, description="帐户权限")
    cookie = fields.CharField(max_length=320, null=True, description="登陆令牌")
    expiry = fields.FloatField(description="令牌时效")
