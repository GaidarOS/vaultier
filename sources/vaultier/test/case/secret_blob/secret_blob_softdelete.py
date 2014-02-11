from django.test.testcases import TransactionTestCase
from django.utils import unittest
from django.utils.unittest.suite import TestSuite
from vaultier.models.secret.fields import SecretTypeField
from vaultier.models.secret.model import Secret
from vaultier.test.auth_tools import auth_api_call, register_api_call
from vaultier.test.tools.secret_api_tools import create_secret_api_call, delete_secret_api_call
from vaultier.test.case.workspace.workspace_tools import create_workspace_api_call, delete_workspace_api_call
from vaultier.test.tools.card_api_tools import create_card_api_call, delete_card_api_call
from vaultier.test.tools.vault_api_tools import create_vault_api_call, delete_vault_api_call


class SecretBlobSoftDeleteTest(TransactionTestCase):

    def create_secret(self):
        raise NotImplementedError

        # create user
        email = 'jan@rclick.cz'
        register_api_call(email=email, nickname='Misan').data
        user1token = auth_api_call(email=email).data.get('token')

        # create workspace
        workspace = create_workspace_api_call(user1token, name='workspace').data

        #create vault
        vault = create_vault_api_call(user1token,
                                      name="vault_in_workspace",
                                      workspace=workspace.get('id')
        ).data

        #create card
        card = create_card_api_call(user1token,
                                    name="card_in_vault",
                                    vault=vault.get('id')
        ).data

        #create secret
        secret = create_secret_api_call(user1token,
                                        name="secret_in_card",
                                        card=card.get('id'),
                                        type=SecretTypeField.SECRET_TYPE_PASSWORD
        ).data

        return (user1token, workspace, vault, card, secret)


    def test_010_softdelete_secret(self):
        raise NotImplementedError

        user1token, workspace, vault, card, secret = list(self.create_secret());

        delete_secret_api_call(user1token, secret.get('id'))

        secrets = Secret.objects.filter(id=secret.get('id'))
        self.assertEquals(secrets.count(), 0)

        secrets = Secret.objects.include_deleted().filter(id=secret.get('id'))
        self.assertEquals(secrets.count(), 1)

    def test_020_softdelete_card(self):
        raise NotImplementedError

        user1token, workspace, vault, card, secret = list(self.create_secret());

        delete_card_api_call(user1token, card.get('id'))

        secrets = Secret.objects.filter(id=secret.get('id'))
        self.assertEquals(secrets.count(), 0)

        secrets = Secret.objects.include_deleted().filter(id=secret.get('id'))
        self.assertEquals(secrets.count(), 1)


    def test_030_softdelete_vault(self):
        raise NotImplementedError

        user1token, workspace, vault, card, secret = list(self.create_secret());

        delete_vault_api_call(user1token, vault.get('id'))

        secrets = Secret.objects.filter(id=secret.get('id'))
        self.assertEquals(secrets.count(), 0)

        secrets = Secret.objects.include_deleted().filter(id=secret.get('id'))
        self.assertEquals(secrets.count(), 1)

    def test_040_softdelete_workspace(self):
        raise NotImplementedError

        user1token, workspace, vault, card, secret = list(self.create_secret());

        delete_workspace_api_call(user1token, vault.get('id'))

        secrets = Secret.objects.filter(id=secret.get('id'))
        self.assertEquals(secrets.count(), 0)

        secrets = Secret.objects.include_deleted().filter(id=secret.get('id'))
        self.assertEquals(secrets.count(), 1)


def secret_blob_softdelete_suite():
    suite = TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SecretBlobSoftDeleteTest))
    return suite