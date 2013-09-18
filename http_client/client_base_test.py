"""
Unit tests for client_base
"""
import unittest
from mock import Mock
from mock import sentinel as _
import client_base
import socket


def fake_file_obj():
    obj = Mock()
    obj.read.return_value = 'read string'
    return obj


class ClientBaseTest(unittest.TestCase):

    def setUp(self):
        self.logger = Mock()
        self.obj_ut = client_base.ClientBase('testhost', 443, use_ssl=True)
        self.obj_ut.log = self.logger
        client_base.config = Mock()
        client_base.config.return_value = "testfilename.log"
        client_base.urllib = Mock()
        client_base.httplib = Mock()
        client_base.select = Mock()
        client_base.select.select.return_value = [[3], [2]]
        client_base.httplib.HTTPConnection = Mock()
        client_base.httplib.HTTPSConnection = Mock()

    def test_send_command_urllib(self):
        ffo = fake_file_obj()
        client_base.urllib.urlopen.return_value = ffo
        r = self.obj_ut.send_command_urllib('/foo', 'data')
        self.assertEqual(r, 'read string')
        ffo.read.assert_called_once_with()
        client_base.urllib.urlopen.assert_called_once_with(
            'https://testhost/foo', 'data')

    def test_send_command_urllib_no_ssl(self):
        ffo = fake_file_obj()
        client_base.urllib.urlopen.return_value = ffo
        self.obj_ut.use_ssl = False
        self.obj_ut.port = 80
        r = self.obj_ut.send_command_urllib('/foo', 'data')
        self.assertEqual(r, 'read string')
        ffo.read.assert_called_once_with()
        client_base.urllib.urlopen.assert_called_once_with(
            'http://testhost/foo', 'data')

    def test_send_command_httplib(self):
        fake_https_conn = Mock()
        fake_response = Mock()
        fake_response.read.return_value = 'crap'
        fake_response.status = 200
        fake_https_conn.getresponse.return_value = fake_response
        client_base.httplib.HTTPSConnection.return_value = fake_https_conn
        r = self.obj_ut.send_command_httplib('/foo', 'data')
        client_base.httplib.HTTPSConnection.assert_called_once_with(
            'testhost', 443)
        self.assertEqual(r, 'crap')
        fake_https_conn.connect.assert_called_once_with()
        fake_https_conn.close.assert_called_once_with()
        fake_https_conn.send.assert_called_once_with('data')
        fake_response.read.assert_called_once_with()
        fake_response.status = 500
        with self.assertRaises(client_base.ClientError):
            self.obj_ut.send_command_httplib('/foo', 'data')
        client_base.select.select.return_value = [[], [2]]
        with self.assertRaises(socket.timeout):
            self.obj_ut.send_command_httplib('/foo', 'data')

    def test_send_command_httplib_no_ssl(self):
        self.obj_ut.use_ssl = False
        self.obj_ut.port = 80
        fake_http_conn = Mock()
        fake_response = Mock()
        fake_response.read.return_value = 'crap'
        fake_response.status = 200
        fake_http_conn.getresponse.return_value = fake_response
        client_base.httplib.HTTPConnection.return_value = fake_http_conn
        r = self.obj_ut.send_command_httplib('/foo', 'data')
        self.assertEqual(r, 'crap')
        client_base.httplib.HTTPConnection.assert_called_once_with(
            'testhost', 80)

    def test_send_command(self):
        self.obj_ut.use_urllib = True
        self.obj_ut.send_command('/foo', 'data')
        client_base.urllib.urlopen.assert_called_once_with(
            'https://testhost/foo', 'data')
        fake_https_conn = Mock()
        fake_response = Mock()
        fake_response.read.return_value = 'crap'
        fake_response.status = 200
        fake_https_conn.getresponse.return_value = fake_response
        client_base.httplib.HTTPSConnection.return_value = fake_https_conn
        self.obj_ut.use_urllib = False
        self.obj_ut.send_command('/foo', 'data')
        client_base.httplib.HTTPSConnection.assert_called_once_with(
            'testhost', 443)


if __name__ == "__main__":
    unittest.main()
