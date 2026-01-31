from gitlab.packages import *
from unittest.mock import mock_open, patch

from utils import (
    test_gitlab,
    mock_empty_response,
    mock_one_response,
    mock_five_response,
    mock_paginate_1,
    mock_paginate_2,
)


class TestPackages:

    def test_api_url(self, test_gitlab):
        url = "https://gl-host/api/v4/"
        assert url == test_gitlab._url()

    def test_project_path(self, test_gitlab):
        url = "projects/24"
        assert url == test_gitlab._build_path("projects", "24")

    def test_build_query_empty(self, test_gitlab):
        args = ""
        assert args == test_gitlab.build_query()

    def test_build_query_one(self, test_gitlab):
        args = "?package_name=name"
        assert args == test_gitlab.build_query(package_name="name")

    def test_build_query_two(self, test_gitlab):
        args = "?package_name=name&package_version=version"
        assert args == test_gitlab.build_query(
            package_name="name", package_version="version"
        )

    def test_project_path_name(self, test_gitlab):
        url = "projects/namespace%2Fpath"
        assert url == test_gitlab._build_path(
            "projects", parse.quote_plus("namespace/path")
        )

    def test_get_headers(self, test_gitlab):
        assert test_gitlab._get_headers() == {"token-name": "token-value"}

    def test_get_headers_no_name(self):
        test_gitlab = Packages("gl-host", "", "token-value")
        assert test_gitlab._get_headers() == {}

    def test_get_headers_no_value(self):
        test_gitlab = Packages("gl-host", "token-name", "")
        assert test_gitlab._get_headers() == {}

    def test_get_headers_no_name_no_value(self):
        test_gitlab = Packages("gl-host", "", "")
        assert test_gitlab._get_headers() == {}

    def test_list_packages_none(self, test_gitlab, mock_empty_response):
        url = "https://gl-host/api/v4/projects/24/packages?package_name=package-name&package_type=generic"
        headers = {"token-name": "token-value"}
        with patch.object(Packages, "_get", return_value=mock_empty_response) as _get:
            packages = test_gitlab.get_versions("24", "package-name")
            assert len(packages) == 0
            _get.assert_called_once_with(url, headers)

    def test_list_packages_one(self, test_gitlab, mock_one_response):
        url = "https://gl-host/api/v4/projects/18105942/packages?package_name=ABCComponent&package_type=generic"
        headers = {"token-name": "token-value"}
        with patch.object(Packages, "_get", return_value=mock_one_response) as _get:
            packages = test_gitlab.get_versions("18105942", "ABCComponent")
            assert len(packages) == 1
            _get.assert_called_once_with(url, headers)

    def test_list_packages_paginate(
        self, test_gitlab, mock_paginate_1, mock_paginate_2
    ):
        url1 = "https://gl-host/api/v4/projects/18105942/packages?package_name=ABCComponent&package_type=generic"
        url2 = "https://gl-host/api/v4/projects/18105942/packages?id=18105942&order_by=created_at&page=2&per_page=10&sort=asc"
        headers = {"token-name": "token-value"}
        side_effects = [mock_paginate_1, mock_paginate_2]
        with patch.object(Packages, "_get", side_effect=side_effects) as _get:
            packages = test_gitlab.get_versions("18105942", "ABCComponent")
            assert len(packages) == 18
            _get.assert_any_call(url1, headers)
            _get.assert_called_with(url2, headers)

    def test_list_name_packages_filter(self, test_gitlab):
        data = (
            200,
            '[{"name": "package-name", "version": "0.1.2"}, {"name": "package-name-something", "version": "0.1.2"}]',
            {},
        )
        url = "https://gl-host/api/v4/projects/24/packages?package_name=package-name&package_type=generic"
        headers = {"token-name": "token-value"}
        with patch.object(Packages, "_get", return_value=data) as _get:
            packages = test_gitlab.get_versions("24", "package-name")
            assert len(packages) == 1
            _get.assert_called_once_with(url, headers)

    def test_list_name_packages_five(self, test_gitlab, mock_five_response):
        url = "https://gl-host/api/v4/projects/18105942/packages?package_name=ABCComponent&package_type=generic"
        headers = {"token-name": "token-value"}
        with patch.object(Packages, "_get", return_value=mock_five_response) as _get:
            packages = test_gitlab.get_versions("18105942", "ABCComponent")
            assert len(packages) == 5
            _get.assert_called_once_with(url, headers)

    def test_list_files_none(self, test_gitlab, mock_empty_response):
        url = "https://gl-host/api/v4/projects/24/packages/123/package_files"
        headers = {"token-name": "token-value"}
        with patch.object(Packages, "_get", return_value=mock_empty_response) as _get:
            packages = test_gitlab.get_files("24", "123").keys()
            assert len(packages) == 0
            _get.assert_called_once_with(url, headers)

    def test_list_files_one(self, test_gitlab):
        data = (200, '[{"id": 1, "file_name": "filea.txt"}]', {})
        with patch.object(Packages, "_get", return_value=data):
            packages = test_gitlab.get_files("24", "123").keys()
            assert len(packages) == 1

    def test_list_files_five(self, test_gitlab):
        data = (
            200,
            '[{"id": 1, "file_name": "filea.txt"}, {"id": 2, "file_name": "fileb.txt"}, {"id": 3, "file_name": "filec.txt"}, {"id": 4, "file_name": "filed.txt"}, {"id": 5, "file_name": "filee.txt"}]',
            {},
        )
        with patch.object(Packages, "_get", return_value=data):
            packages = test_gitlab.get_files("24", "123").keys()
            assert len(packages) == 5

    def test_package_id_none(self, test_gitlab, mock_empty_response):
        url = "https://gl-host/api/v4/projects/24/packages?package_name=package-name&package_version=0.1&package_type=generic"
        headers = {"token-name": "token-value"}
        with patch.object(Packages, "_get", return_value=mock_empty_response) as _get:
            packages = test_gitlab.get_id("24", "package-name", "0.1")
            assert packages == -1
            _get.assert_called_once_with(url, headers)

    def test_package_id_one(self, test_gitlab):
        data = (200, '[{"id": 123}]', {})
        with patch.object(Packages, "_get", return_value=data):
            packages = test_gitlab.get_id("24", "package-name", "0.1")
            assert packages == 123

    def test_upload_file(self, test_gitlab):
        data = (201, "[]", {})
        file = "Data"
        url = (
            "https://gl-host/api/v4/projects/24/packages/generic/package-name/0.1/file"
        )
        headers = {"token-name": "token-value"}
        with patch("builtins.open", mock_open(read_data=file)):
            with patch.object(Packages, "_put", return_value=data) as _put:
                success = test_gitlab.upload_file(
                    "24", "package-name", "0.1", "file", ""
                )
                assert success == 0
                _put.assert_called_once_with(url, file, headers)

    def test_upload_files(self, test_gitlab):
        data = (201, "[]", {})
        file = "Data"
        url = "https://gl-host/api/v4/projects/24/packages/generic/package-name/0.1/packages_empty.body"
        headers = {"token-name": "token-value"}
        with patch("builtins.open", mock_open(read_data=file)) as p_open:
            with patch.object(Packages, "_put", return_value=data) as _put:
                success = test_gitlab.upload_file(
                    "24", "package-name", "0.1", "", "test/data"
                )
                # This magic number is just the number of files in test/data folder.
                # In case files are added or removed... This should be updated.
                assert p_open.call_count == 10
                assert success == 0
                _put.assert_any_call(url, file, headers)

    def test_download_file(self, test_gitlab):
        data = (200, "file-content", {})
        url = "https://gl-host/api/v4/projects/24/packages/generic/package-name/0.1/file.txt"
        headers = {"token-name": "token-value"}
        with patch("builtins.open", mock_open()) as file_mock:
            # mock_open.write.return_value = 0
            with patch.object(Packages, "_get", return_value=data) as _get:
                ret = test_gitlab.download_file("24", "package-name", "0.1", "file.txt")
                assert ret == 0
                _get.assert_called_once_with(url, headers)
            file_mock.assert_called_once_with("file.txt", "wb")
            file_mock().write.assert_called_once_with("file-content")

    def test_delete_file(self, test_gitlab):
        packages = (200, '[{"id": 123}]', {})
        files = (200, '[{"id": 2, "file_name": "file.txt"}]', {})
        data = (204, None, {})
        side_effects = [packages, files]
        url = "https://gl-host/api/v4/projects/24/packages/123/package_files/2"
        headers = {"token-name": "token-value"}
        # mock_open.write.return_value = 0
        with patch.object(Packages, "_get", side_effect=side_effects):
            with patch.object(Packages, "_delete", return_value=data) as _delete:
                ret = test_gitlab.delete_file("24", "package-name", "0.1", "file.txt")
                assert ret == 0
                _delete.assert_called_once_with(url, headers)

    def test_delete_package(self, test_gitlab):
        packages = (200, '[{"id": 123}]', {})
        data = (204, None, {})
        url = "https://gl-host/api/v4/projects/24/packages/123"
        headers = {"token-name": "token-value"}
        # mock_open.write.return_value = 0
        with patch.object(Packages, "_get", return_value=packages):
            with patch.object(Packages, "_delete", return_value=data) as _delete:
                ret = test_gitlab.delete_package("24", "package-name", "0.1")
                assert ret == 0
                _delete.assert_called_once_with(url, headers)
