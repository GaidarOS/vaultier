import datetime
import uuid
import hmac
from hashlib import sha1
from django.utils.timezone import utc
from django.db.models.aggregates import Count
from django.utils import timezone
from django.db import models
from django.db.models.deletion import PROTECT
from django.db.models.manager import Manager
from django.db.models.signals import pre_save, post_save
from django.conf import settings
from vaultier.models.member.fields import MemberStatusField
from vaultier.models.member.model import Member
from vaultier.models.workspace.model import Workspace
from vaultier.mailer.lostkey.sender import LostKeyEmailSender


class LostKeyManager(Manager):
    def on_pre_save(self, sender, instance=None, *args, **kwargs):
        if not instance.id:
            self._generate_hash(instance=instance)
            self._generate_expiration_time(instance=instance)

    def _generate_hash(self, instance=None):
        unique_hash = uuid.uuid4()
        instance.hash = hmac.new(unique_hash.bytes, digestmod=sha1).hexdigest()

    def _generate_expiration_time(self, instance=None):
        expiration_time = settings.BK_FEATURES.get('lostkey_hash_expiration_time')
        instance.expires_at = timezone.now().replace(tzinfo=utc) + datetime.timedelta(milliseconds=expiration_time)

    def send_notification(self, sender, instance=None, *args, **kwargs):
        """
        Sends email to user with the valid url for update the public key
        :param sender:
        :param instance:
        :param args:
        :param kwargs:
        :return: None
        """
        if not instance.used:
            sender = LostKeyEmailSender(instance)
            sender.send()

    def disable_lost_key(self, user):
        """
        Soft delete nan shared workspaces of a given user
        :param user:
        :return:
        """
        self._disable_memberships(user)
        self._softdelete_unrecoverable_workspaces(user)

    @classmethod
    def _disable_memberships(cls, user):
        """
        Set all membership of given user to MemberStatusField.STATUS_MEMBER_BROKEN
        :param user:
        :return:
        """
        Member.objects.filter(user=user).update(status=MemberStatusField.STATUS_MEMBER_BROKEN)

    @classmethod
    def find_workspace_is_recoverable(cls, workspace_id, user):
        """
        Return True if the workspace is recoverable.
        A work space is recoverable when it share among any user and those users have
        the status set to MemberStatusField.STATUS_MEMBER
        :param workspace_id: int
        :param user: vaultier.models.user.model.User
        :return: bool
        """
        return 0 < Member.objects.filter(workspace_id=workspace_id,
                                         status=MemberStatusField.STATUS_MEMBER) \
            .exclude(user=user).count()


    def rebuild_lost_key(self, user):
        """
        :param user:
        :return:
        """
        self._set_unrecoverable_workspaces_broken(user)
        self._set_status_member_without_workspace_key(user)
        self._softdelete_unrecoverable_workspaces(user)

    def _set_status_member_without_workspace_key(self, user):
        """
        Update status of shared memberships for a given user
        :param user:
        :return:
        """
        unrecoverable_workspaces = self._get_unrecoverable_workspaces(user)
        Member.objects.filter(user=user) \
            .exclude(workspace_id__in=unrecoverable_workspaces.values_list('pk', flat=True)) \
            .update(status=MemberStatusField.STATUS_MEMBER_WITHOUT_WORKSPACE_KEY, workspace_key='')

    def _set_unrecoverable_workspaces_broken(self, user):
        """
        Set the membership status to broken
        just for nonrecoverable workspaces
        :param user:
        :return:
        """
        unrecoverable_workspaces = self._get_unrecoverable_workspaces(user)
        Member.objects.filter(user=user, workspace_id__in=unrecoverable_workspaces.values_list('pk', flat=True)) \
            .update(status=MemberStatusField.STATUS_MEMBER_BROKEN)

    def _softdelete_unrecoverable_workspaces(self, user):
        """
        Deletes workspaces whe
        :param user:
        :return:
        """
        unrecoverable_workspaces = self._get_unrecoverable_workspaces(user)
        Workspace.bulk_delete(unrecoverable_workspaces)

    def _get_unrecoverable_workspaces(self, user):
        """
        Filter Workspace where the user is the only member
        :param user:
        :return: QuerySet
        """
        return Workspace.objects.filter(
            pk__in=Member.objects.filter(user=user).values_list('workspace_id', flat=True)
        ).annotate(is_recoverable=Count('membership')).exclude(is_recoverable__gt=1)


class LostKey(models.Model):
    class Meta:
        db_table = u'vaultier_lost_key'
        app_label = 'vaultier'

    objects = LostKeyManager()
    hash = models.TextField(null=False)
    created_by = models.ForeignKey('vaultier.User', on_delete=PROTECT, related_name='distracted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=False)
    used = models.BooleanField(default=False)


def register_signals():
    pre_save.connect(LostKey.objects.on_pre_save, sender=LostKey)
    post_save.connect(LostKey.objects.send_notification, sender=LostKey)