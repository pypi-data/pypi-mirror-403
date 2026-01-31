from unittest.mock import MagicMock
import pytest

@pytest.fixture
def mock_os_listdir_patch(monkeypatch):
    """
    Fixture que mockea `os.listdir` para tests, permitiendo devolver una lista
    fija o usar un side_effect personalizado.

    Uso:
        def test_xxx(mock_os_listdir_patch):
            mock_listdir = mock_os_listdir_patch(listdir_return=["file1.csv", "file2.csv"])
            assert os.listdir("cualquier_ruta") == ["file1.csv", "file2.csv"]
    """
    def _patch(listdir_return=None, listdir_side_effect=None):
        if listdir_return is None:
            listdir_return = []

        mock_listdir = MagicMock()
        mock_listdir.return_value = listdir_return

        if listdir_side_effect is not None:
            mock_listdir.side_effect = listdir_side_effect

        monkeypatch.setattr("os.listdir", mock_listdir)
        return mock_listdir

    return _patch

        



