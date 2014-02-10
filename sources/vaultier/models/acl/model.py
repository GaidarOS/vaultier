from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.fields import PositiveIntegerField
from django.db.models.manager import Manager
from vaultier.models.acl.fields import AclDirectionField
from vaultier.models.object_reference import ObjectReference, ObjectReferenceTypeField
from vaultier.models.role.fields import RoleLevelField


class AclManager(Manager):
    pass

class Acl(ObjectReference,models.Model):
    class Meta:
        db_table = u'vaultier_acl'
        app_label = 'vaultier'

    objects = AclManager()

    object_type = models.ForeignKey(ContentType, default=None, null=True)
    object_id = PositiveIntegerField(default=None, null=True)
    object = GenericForeignKey('object_type', 'object_id')

    level = RoleLevelField()
    direction = AclDirectionField()

    role = models.ForeignKey('vaultier.Role', on_delete=CASCADE)
    user = models.ForeignKey('vaultier.User', on_delete=CASCADE)

    def get_target_string(self):
        if (self.type == 100):
            return 'workspace:'+str(self.to_workspace.id)
        if (self.type == 200):
            return 'vault:'+str(self.to_vault.id)
        if (self.type == 300):
            return 'card:'+str(self.to_card.id)

    def __unicode__(self):
        return 'Acl(' + str(self.id) + '): to:' + str(self.get_target_string()) + ' level:' + str(self.level) + ' user: '+str(self.user)