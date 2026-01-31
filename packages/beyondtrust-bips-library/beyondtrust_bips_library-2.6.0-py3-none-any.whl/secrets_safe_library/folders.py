"""Folders module, all the logic to manage folders from PS API"""

import logging

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import DeleteByIdMixin, GetByIdMixin
from secrets_safe_library.validators.base import CustomValidator


class Folder(APIObject, GetByIdMixin, DeleteByIdMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/secrets-safe/folders")

        # Schema rules used for validations
        self._schema = {
            "description": {"type": "string", "maxlength": 256, "nullable": True},
            "folder_id": {"type": "string", "is_uuid": True, "nullable": False},
            "destination_folder_id": {
                "type": "string",
                "is_uuid": True,
                "nullable": False,
            },
            "duplicate_name_action": {
                "type": "string",
                "allowed": ["Rename", "Stop", "Skip"],
                "nullable": False,
            },
        }
        self._validator = CustomValidator(self._schema)

    def list_folders(
        self,
        folder_name: str = None,
        folder_path: str = None,
        include_subfolders: bool = True,
        root_only: bool = False,
        folder_owner_id: str = None,
        limit: int = None,
        offset: int = None,
    ) -> list:
        """
        Returns a list of folders with the option to filter the list using query
        parameters.

        API: GET Secrets-Safe/Folders/

        Args:
            folder_name (str, optional): The partial name of the folder. Defaults to
            None.
            folder_path (str, optional): Child folders are also included. Separator is
            '/'. Defaults to None.
            include_subfolders (bool, optional): Indicate whether to include the
            subfolder. Defaults to True.
            root_only (bool, optional): The results only include those folders at the
            root level. Defaults to False.
            folder_owner_id (str, optional): Filter results by the folders which are
            owned by the given FolderOwnerId. Defaults to None.
            limit (int, optional): limit the results.
            offset (int, optional): skip the first (offset) number of folders.

        Returns:
            list: List of folders matching specified arguments.
        """

        params = {
            "folderName": folder_name,
            "folderPath": folder_path,
            "includeSubfolders": include_subfolders,
            "rootOnly": root_only,
            "folderOwnerId": folder_owner_id,
            "limit": limit,
            "offset": offset,
        }
        query_string = self.make_query_string(params)
        endpoint = f"{self.endpoint}?{query_string}"

        utils.print_log(self._logger, "Calling list_folders endpoint", logging.DEBUG)
        response = self._run_get_request(endpoint)

        return response.json()

    def create_folder(
        self,
        name: str,
        parent_id: str,
        description: str = "",
        user_group_id: int = None,
    ) -> dict:
        """
        Creates a new Secrets Safe folder for the given user group.

        API: POST Secrets-Safe/Folders/

        Args:
            name (str): The folder name.
            parent_id (str): The parent folder/safe ID (GUID).
            description (str, optional): The folder description.
            user_group_id (int, optional): The user group ID.

        Returns:
            dict: Created Folder object.
        """

        attributes = {"description": description}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Name": name,
            "Description": description,
            "ParentId": parent_id,
            "UserGroupId": user_group_id,
        }

        utils.print_log(
            self._logger,
            f"Calling create folder endpoint: {self.endpoint}",
            logging.DEBUG,
        )
        response = self._run_post_request(
            self.endpoint, payload, include_api_version=False
        )

        return response.json()

    def import_csv(self, folder_id: str, csv_file_path: str) -> dict:
        """
        Imports a CSV secrets file into the specified folder.

        API: POST Secrets-Safe/Folders/{id}/upload

        Args:
            folder_id (str): The folder ID (GUID) where the secrets will be imported.
            csv_file_path (str): The path to the CSV file to be uploaded.

        Returns:
            dict: Import result with the following structure:
                {
                    "totalNumber": int,  # Number of credentials processed
                                          # (includes failures)
                    "errors": [{         # List of errors
                        "lineNumber": int,
                        "error": str
                    }],
                    "successfulImport": int  # Number of credentials
                                              # successfully imported
                }

        Raises:
            exceptions.OptionsError: If folder_id is not a valid UUID.
            exceptions.CreationError: If the import fails.
            FileNotFoundError: If the CSV file does not exist.
        """
        attributes = {"folder_id": folder_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"{self.endpoint}/{folder_id}/upload"

        utils.print_log(
            self._logger,
            f"Importing CSV file into folder {folder_id}",
            logging.DEBUG,
        )

        response = self._run_post_file_request(
            endpoint=endpoint,
            payload=None,
            file_path=csv_file_path,
            include_api_version=False,
            file_field_name="form-data",
            content_type="text/csv",
        )

        return response.json()

    def move_folder(
        self,
        folder_id: str,
        destination_folder_id: str,
        duplicate_name_action: str,
    ) -> dict:
        """
        Moves a folder to a new parent folder.

        API: PUT Secrets-Safe/Folders/{folderid}/Move

        Args:
            folder_id (str): The UUID of the folder to move.
            destination_folder_id (str): The UUID of the destination parent folder.
            duplicate_name_action (str, optional): Action to take if a folder with
            the same name exists in the destination folder. Possible values are
            "Rename", "Stop", or "Skip".

        Returns:
            dict: Moved Folder object.
        """

        attributes = {
            "folder_id": folder_id,
            "destination_folder_id": destination_folder_id,
            "duplicate_name_action": duplicate_name_action,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "DestinationFolderId": destination_folder_id,
            "DuplicateNameAction": duplicate_name_action,
        }

        endpoint = f"{self.endpoint}/{folder_id}/move"

        utils.print_log(
            self._logger,
            f"Calling move folder endpoint: {endpoint}",
            logging.DEBUG,
        )
        response = self._run_put_request(endpoint, payload, include_api_version=False)

        return response.json()
