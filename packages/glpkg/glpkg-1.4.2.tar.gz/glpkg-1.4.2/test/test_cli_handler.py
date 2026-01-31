from unittest.mock import patch

import pytest

from gitlab import __version__, Packages
from gitlab.cli_handler import CLIHandler
import sys

from utils import mock_empty_response, mock_one_response


class TestCliHandler:

    def test_no_args(self):
        args = ["glpkg"]
        with patch.object(sys, "argv", args):
            with pytest.raises(SystemExit) as exit:
                CLIHandler()
            assert exit.value.code == 2
            # Assume prints instructions

    def test_version(self, capsys):
        args = ["glpkg", "-v"]
        with patch.object(sys, "argv", args):
            with pytest.raises(SystemExit) as exit:
                CLIHandler()
            assert exit.value.code == 0
            out, err = capsys.readouterr()
            assert out == __version__ + "\n"
            assert err == ""

    def test_help(self):
        args = ["glpkg", "-h"]
        with patch.object(sys, "argv", args):
            with pytest.raises(SystemExit) as exit:
                CLIHandler()
            assert exit.value.code == 0
            # Assume prints help

    def test_list_empty(self, mock_empty_response, capsys):
        args = ["glpkg", "list", "--project", "18105942", "--name", "AABCComponent"]
        with patch.object(sys, "argv", args):
            with patch.object(Packages, "_get", return_value=mock_empty_response):
                handler = CLIHandler()
                handler.do_it()
                out, err = capsys.readouterr()
                assert out == "Name\t\tVersion\n"
                assert err == ""

    def test_list_one(self, mock_one_response, capsys):
        args = ["glpkg", "list", "--project", "18105942", "--name", "ABCComponent"]
        with patch.object(sys, "argv", args):
            with patch.object(Packages, "_get", return_value=mock_one_response):
                handler = CLIHandler()
                handler.do_it()
                out, err = capsys.readouterr()
                assert out == "Name\t\tVersion\nABCComponent\t0.0.1\n"
                assert err == ""
