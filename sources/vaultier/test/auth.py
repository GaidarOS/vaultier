from django.test.testcases import TestCase, TransactionTestCase
from django.utils import unittest
from django.utils.unittest.suite import TestSuite
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST
from vaultier.auth.authentication import Backend

from vaultier.test.auth_tools import auth_api_call, register_api_call
from tools import format_response
from app.settings import PROJECT_ROOT

class SignaturesTest(TestCase):
    def test_rsa(self):
        email = 'jan.misek@rclick.cz'
        privkey = open(PROJECT_ROOT+'/vaultier/test/fixtures/vaultier.key').read()
        pubkey = open(PROJECT_ROOT+'/vaultier/test/fixtures/vaultier.pub').read()
        signature = Backend.sign(privkey, email);

        self.assertTrue(Backend.verify(pubkey, email, signature))
        self.assertFalse(Backend.verify(pubkey, 'Unsigned text', signature))


class ApiRegisterTest(TransactionTestCase):

    def test_010_register(self):

        # register user
        email = email='jan.misek@rclick.cz'
        response = register_api_call(email=email, nickname='Misan')
        self.id = response.data.get('id')
        self.assertEqual(response.status_code, HTTP_201_CREATED, msg=format_response(response))

        # register user again should be forbidden
        response = register_api_call(email=email, nickname='Misan')
        self.assertTrue(response.data.get('email') is not None)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST, msg=format_response(response))


    def test_020_auth(self):
         # register user
        email = email='jan.misek@rclick.cz'
        response = register_api_call(email=email, nickname='Misan')
        self.id = response.data.get('id')
        self.assertEqual(response.status_code, HTTP_201_CREATED, msg=format_response(response))

        # try to login, check proper signature
        response = auth_api_call(email=email)
        self.assertEqual(response.status_code, HTTP_200_OK, msg=format_response(response))

        # try to login, check wrong signature
        response = auth_api_call(email=email, signature='WrongSignature')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN, msg=format_response(response))

def auth_suite():
    suite = TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SignaturesTest))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ApiRegisterTest))
    return suite