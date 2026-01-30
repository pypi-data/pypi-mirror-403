from django.urls import reverse
from django.contrib.postgres.fields import ArrayField
from netbox.models import NetBoxModel
from django.db import models
from .choices import SNMPUserVersionChoices, SNMPAuthChoices, SNMPPrivChoices, SNMPLevelChoices, SNMPOIDChoices, SNMPNotifyChoices
from django.core.validators import MinValueValidator, MaxValueValidator


class SNMPBase(NetBoxModel):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        abstract = True


# region TRAP PROFILES
class TrapProfiles(SNMPBase):
    version = models.CharField(max_length=32, choices=SNMPUserVersionChoices.CHOICES, default=SNMPUserVersionChoices.V3)
    target = models.GenericIPAddressField()
    port = models.PositiveIntegerField(default=162, validators=[MaxValueValidator(65535)])
    level = models.CharField(max_length=32, choices=SNMPLevelChoices.CHOICES, default=SNMPLevelChoices.AUTH_PRIV)
    timeout = models.PositiveIntegerField(default=15)
    retries = models.PositiveIntegerField(default=3)
    user_profile = models.ForeignKey("UserProfiles", on_delete=models.PROTECT, related_name="trapprofiles", null=True, blank=True)

    def get_absolute_url(self):
        return reverse("plugins:netbox_snmp:trapprofiles", args=[self.pk])

    class Meta:
        verbose_name_plural = "Trap Profiles"
        ordering = ["name"]

    def __str__(self):
        return self.name


# endregion


# region USER PROFILES
class UserProfiles(SNMPBase):
    auth = models.CharField(choices=SNMPAuthChoices.CHOICES, blank=True)
    priv = models.CharField(choices=SNMPPrivChoices.CHOICES, blank=True)

    def get_absolute_url(self):
        return reverse("plugins:netbox_snmp:userprofiles", args=[self.pk])

    class Meta:
        verbose_name_plural = "User Profiles"
        ordering = ["name"]

    def __str__(self):
        return self.name


# endregion


# region MIB TREES
class MIBTrees(SNMPBase):
    view_type = models.CharField(choices=SNMPOIDChoices.CHOICES, default=SNMPOIDChoices.INCLUDED)
    oid = ArrayField(models.CharField(max_length=32), verbose_name="OID(s)", blank=True, default=list)

    def get_absolute_url(self):
        return reverse("plugins:netbox_snmp:mibtrees", args=[self.pk])

    class Meta:
        verbose_name_plural = "MIB Views"
        ordering = ["name"]

    def __str__(self):
        return self.name


# endregion


# region NOTIFY
class NotifyProfiles(SNMPBase):
    notification_type = models.CharField(choices=SNMPNotifyChoices.CHOICES, default=SNMPNotifyChoices.TRAP)

    def get_absolute_url(self):
        return reverse("plugins:netbox_snmp:notifyprofiles", args=[self.pk])

    class Meta:
        verbose_name_plural = "Notify Profiles"
        ordering = ["name"]

    def __str__(self):
        return self.name


# endregion
