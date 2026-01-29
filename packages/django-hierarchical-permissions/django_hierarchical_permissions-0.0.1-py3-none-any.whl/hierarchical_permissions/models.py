from django.contrib.auth.models import Group, User
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from hierarchical_permissions.conf import get_organizational_unit_types


class OrganizationalUnit(MPTTModel):
    name = models.CharField(max_length=100)
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    type = models.CharField(
        max_length=20,
        choices=get_organizational_unit_types(),
    )

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return f"{self.name} ({self.type})"


class UserGroup(models.Model):
    organizational_units = models.ManyToManyField(
        OrganizationalUnit, related_name="user_groups"
    )
    users = models.ManyToManyField(User, related_name="user_groups")
    permission_groups = models.ManyToManyField(Group, related_name="user_groups")


class BaseModel(models.Model):
    parent = TreeForeignKey(
        "hierarchical_permissions.OrganizationalUnit",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
