from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.deletion import SET_NULL, PROTECT, CASCADE
import uuid
import hmac
from hashlib import sha1


class Workspace(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1024, blank=True, null=True)
    created_by = models.ForeignKey('core.User', on_delete=PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = u'vaultier_workspace'


class Member(models.Model):
    workspace = models.ForeignKey('core.Workspace', on_delete=CASCADE)
    user = models.ForeignKey('core.User', on_delete=CASCADE, null=True)
    invitation_hash = models.CharField(max_length=64)
    invitation_email = models.CharField(max_length=1024),
    status = models.CharField(
        max_length=1,
        choices=(
            (u'i', u'INVITED'),
            (u'm', u'USER'),
        ))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = u'vaultier_member'


class Role(models.Model):
    member = models.ForeignKey('core.Member', on_delete=CASCADE)
    to_workspace = models.ForeignKey('core.Workspace', on_delete=CASCADE)
    to_vault = models.ForeignKey('core.Vault', on_delete=CASCADE),
    to_card = models.ForeignKey('core.Card', on_delete=CASCADE),
    level = models.CharField(
        max_length=1,
        choices=(
            (u'0', u'DENIED'),
            (u'r', u'READ'),
            (u'c', u'READ+CREATE'),
            (u'w', u'WRITE'),
            (u'a', u'ADMIN'),
        ))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = u'vaultier_role'


class Vault(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1024, blank=True, null=True)
    workspace = models.ForeignKey('core.Workspace', on_delete=CASCADE)
    created_by = models.ForeignKey('core.User', on_delete=PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = u'vaultier_vault'


class Card(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1024, blank=True, null=True)
    vault = models.ForeignKey('core.Vault', on_delete=CASCADE)
    created_by = models.ForeignKey('core.User', on_delete=PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = u'vaultier_card'


class Secret(models.Model):
    type = models.IntegerField(null=False)
    data = models.TextField(null=True)
    card = models.ForeignKey('core.Card', on_delete=CASCADE)
    created_by = models.ForeignKey('core.User', on_delete=PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = u'vaultier_secret'


class Token(models.Model):
    token = models.CharField(max_length=64)
    user = models.ForeignKey('core.User', on_delete=CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        return super(Token, self).save(*args, **kwargs)

    def generate_token(self):
        unique = uuid.uuid4()
        return hmac.new(unique.bytes, digestmod=sha1).hexdigest()

    def __unicode__(self):
        return self.key

    class Meta:
        db_table = u'vaultier_token'


class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = UserManager.normalize_email(email)
        user = self.model(username=username, email=email,
                          is_staff=False, is_active=True, is_superuser=False,
                          last_login=now, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        u = self.create_user(username, email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'

    nickname = models.CharField(max_length=255, blank=False, null=False)
    public_key = models.CharField(max_length=1024, blank=True, null=True)
    email = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField('staff status',
                                   default=False,
                                   help_text='Designates whether the user can log into this admin site.'
    )
    is_active = models.BooleanField('active',
                                    default=True,
                                    help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'
    )

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    objects = UserManager()

    class Meta:
        db_table = u'vaultier_user'


#
# class Membership(models.Model):
#     id = models.IntegerField(primary_key=True)
#     crypted_key = models.TextField(blank=True)
#     role = models.IntegerField()
#     user = models.ForeignKey(User)
#     workspace = models.ForeignKey(Workspace, null=True, blank=True)
#     relation = models.IntegerField(null=True, blank=True)
#     vault = models.ForeignKey(Vault, null=True, blank=True)
#     card = models.ForeignKey(Card, null=True, blank=True)
#     class Meta:
#         db_table = u'membership'
#
# class Secret(models.Model):
#     id = models.IntegerField(primary_key=True)
#     name = models.CharField(max_length=255, blank=True)
#     crypted_data = models.TextField(blank=True)
#     card = models.ForeignKey(Card)
#     class Meta:
#         db_table = u'secret'
