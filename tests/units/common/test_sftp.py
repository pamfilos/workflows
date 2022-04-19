from unittest.mock import MagicMock, patch

from common.sftp_service import DirectoryNotFoundException, SFTPService
from pysftp import Connection
from pytest import raises


@patch.object(Connection, attribute="__init__", return_value=None)
@patch.object(Connection, attribute="__del__", return_value=None)
@patch.object(Connection, attribute="chdir")
@patch.object(Connection, attribute="isdir", return_value=True)
def test_connect(connection_mock: MagicMock, *args):
    assert SFTPService()._SFTPService__connect() is not None


@patch.object(Connection, attribute="__init__", return_value=None)
@patch.object(Connection, attribute="__del__", return_value=None)
@patch.object(Connection, attribute="chdir")
@patch.object(Connection, attribute="isdir", return_value=False)
def test_connect_should_crash(connection_mock: MagicMock, *args):
    raises(DirectoryNotFoundException, SFTPService()._SFTPService__connect)
