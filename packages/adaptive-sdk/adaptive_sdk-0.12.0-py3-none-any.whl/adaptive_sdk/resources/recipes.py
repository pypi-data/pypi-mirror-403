from __future__ import annotations
import os
import io
import zipfile
import mimetypes
from contextlib import contextmanager
from loguru import logger
from hypothesis_jsonschema import from_schema
from typing import TYPE_CHECKING, Sequence, Any
from pathlib import Path

from adaptive_sdk.graphql_client.fragments import JobData
from adaptive_sdk.graphql_client.input_types import JobInput

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource
from adaptive_sdk.graphql_client import (
    CustomRecipeData,
    CustomRecipeFilterInput,
    CreateRecipeInput,
    UpdateRecipeInput,
    LabelInput,
    Upload,
)

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class Recipes(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with custom scripts.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def list(self, use_case: str | None = None) -> Sequence[CustomRecipeData]:
        filter = CustomRecipeFilterInput()
        return self._gql_client.list_custom_recipes(use_case=self.use_case_key(use_case), filter=filter).custom_recipes

    def upload(
        self,
        path: str,
        recipe_key: str | None = None,
        entrypoint: str | None = None,
        name: str | None = None,
        description: str | None = None,
        labels: dict[str, str] | None = None,
        use_case: str | None = None,
    ) -> CustomRecipeData:
        """
        Upload a recipe from either a single Python file or a directory (path).

        Args:
            path: Path to a Python file or directory containing the recipe
            recipe_key: Optional unique key for the recipe. If not provided, inferred from:
                - File name (without .py) if path is a file
                - "dir_name/entrypoint_name" if path is a directory and custom entrypoint is specified
                - Directory name if path is a directory and no custom entrypoint is specified
            entrypoint: Optional relative path to the entrypoint file within a directory.
                If specified, this file will be used as main.py. Cannot be used if
                main.py already exists in the directory, or if path is a file.
            name: Optional display name for the recipe
            description: Optional description
            labels: Optional key-value labels
            use_case: Optional use case identifier
        """
        p = Path(path)
        if recipe_key is None:
            recipe_key = _get_recipe_key(p, entrypoint=entrypoint)

        inferred_name = name or recipe_key
        label_inputs = [LabelInput(key=k, value=v) for k, v in labels.items()] if labels else None
        input = CreateRecipeInput(
            key=recipe_key,
            name=inferred_name,
            description=description,
            labels=label_inputs,
        )

        with _upload_from_path(path, entrypoint=entrypoint) as file_upload:
            new_recipe = self._gql_client.create_custom_recipe(
                use_case=self.use_case_key(use_case), input=input, file=file_upload
            ).create_custom_recipe
        logger.info(f"New recipe created with key `{new_recipe.key}`")
        return new_recipe

    def get(
        self,
        recipe_key: str,
        use_case: str | None = None,
    ) -> CustomRecipeData | None:
        return self._gql_client.get_custom_recipe(
            id_or_key=recipe_key, use_case=self.use_case_key(use_case)
        ).custom_recipe

    def update(
        self,
        recipe_key: str,
        path: str | None = None,
        entrypoint: str | None = None,
        name: str | None = None,
        description: str | None = None,
        labels: Sequence[tuple[str, str]] | None = None,
        use_case: str | None = None,
    ) -> CustomRecipeData:
        label_inputs = [LabelInput(key=k, value=v) for k, v in labels] if labels else None
        input = UpdateRecipeInput(
            name=name,
            description=description,
            labels=label_inputs,
        )

        if path:
            with _upload_from_path(path, entrypoint=entrypoint) as file_upload:
                return self._gql_client.update_custom_recipe(
                    use_case=self.use_case_key(use_case),
                    id=recipe_key,
                    input=input,
                    file=file_upload,
                ).update_custom_recipe
        else:
            return self._gql_client.update_custom_recipe(
                use_case=self.use_case_key(use_case),
                id=recipe_key,
                input=input,
                file=None,
            ).update_custom_recipe

    def delete(
        self,
        recipe_key: str,
        use_case: str | None = None,
    ) -> bool:
        return self._gql_client.delete_custom_recipe(
            use_case=self.use_case_key(use_case), id=recipe_key
        ).delete_custom_recipe

    def generate_sample_input(self, recipe_key: str, use_case: str | None = None) -> dict:
        recipe_details = self.get(recipe_key=recipe_key, use_case=self.use_case_key(use_case))
        if recipe_details is None:
            raise ValueError(f"Recipe {recipe_key} was not found")
        strategy = from_schema(recipe_details.json_schema)

        best_example = None
        max_key_count = -1

        for _ in range(10):
            try:
                example = strategy.example()
                current_key_count = _count_keys_recursively(example)

                if current_key_count > max_key_count:
                    max_key_count = current_key_count
                    best_example = example
            except Exception as e:
                print(f"Warning: Failed to generate an example due to: {e}")
                # Continue to next iteration even if one example fails

        if best_example is None:
            print("A valid sample could not be generated. Returning an empty dict.")
            best_example = {}
        return dict(best_example)  # type: ignore


class AsyncRecipes(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with custom scripts.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def list(self, use_case: str | None = None) -> Sequence[CustomRecipeData]:
        filter = CustomRecipeFilterInput()
        return (
            await self._gql_client.list_custom_recipes(use_case=self.use_case_key(use_case), filter=filter)
        ).custom_recipes

    async def upload(
        self,
        path: str,
        recipe_key: str | None = None,
        entrypoint: str | None = None,
        name: str | None = None,
        description: str | None = None,
        labels: Sequence[tuple[str, str]] | None = None,
        use_case: str | None = None,
    ) -> CustomRecipeData:
        """
        Upload a recipe from either a single Python file or a directory (path).

        Args:
            path: Path to a Python file or directory containing the recipe
            recipe_key: Optional unique key for the recipe. If not provided, inferred from:
                - File name (without .py) if path is a file
                - "dir_name/entrypoint_name" if path is a directory and custom entrypoint is specified
                - Directory name if path is a directory and no custom entrypoint is specified
            entrypoint: Optional relative path to the entrypoint file within a directory.
                If specified, this file will be used as main.py. Cannot be used if
                main.py already exists in the directory, or if path is a file.
            name: Optional display name for the recipe
            description: Optional description
            labels: Optional key-value labels
            use_case: Optional use case identifier
        """
        p = Path(path)
        if recipe_key is None:
            recipe_key = _get_recipe_key(p, entrypoint=entrypoint)

        inferred_name = name or recipe_key
        label_inputs = [LabelInput(key=k, value=v) for k, v in labels] if labels else None
        input = CreateRecipeInput(
            key=recipe_key,
            name=inferred_name,
            description=description,
            labels=label_inputs,
        )
        with _upload_from_path(path, entrypoint=entrypoint) as file_upload:
            new_recipe = (
                await self._gql_client.create_custom_recipe(
                    use_case=self.use_case_key(use_case), input=input, file=file_upload
                )
            ).create_custom_recipe
            logger.info(f"New recipe create with key {new_recipe.key}")
            return new_recipe

    async def get(
        self,
        recipe_key: str,
        use_case: str | None = None,
    ) -> CustomRecipeData | None:
        return (
            await self._gql_client.get_custom_recipe(id_or_key=recipe_key, use_case=self.use_case_key(use_case))
        ).custom_recipe

    async def update(
        self,
        recipe_key: str,
        path: str | None = None,
        entrypoint: str | None = None,
        name: str | None = None,
        description: str | None = None,
        labels: Sequence[tuple[str, str]] | None = None,
        use_case: str | None = None,
    ) -> CustomRecipeData:
        label_inputs = [LabelInput(key=k, value=v) for k, v in labels] if labels else None
        input = UpdateRecipeInput(
            name=name,
            description=description,
            labels=label_inputs,
        )

        if path:
            with _upload_from_path(path, entrypoint=entrypoint) as file_upload:
                return (
                    await self._gql_client.update_custom_recipe(
                        use_case=self.use_case_key(use_case),
                        id=recipe_key,
                        input=input,
                        file=file_upload,
                    )
                ).update_custom_recipe
        else:
            return (
                await self._gql_client.update_custom_recipe(
                    use_case=self.use_case_key(use_case),
                    id=recipe_key,
                    input=input,
                    file=None,
                )
            ).update_custom_recipe

    async def delete(
        self,
        recipe_key: str,
        use_case: str | None = None,
    ) -> bool:
        return (
            await self._gql_client.delete_custom_recipe(use_case=self.use_case_key(use_case), id=recipe_key)
        ).delete_custom_recipe

    async def generate_sample_input(self, recipe_key: str, use_case: str | None = None) -> dict:
        recipe_details = await self.get(recipe_key=recipe_key, use_case=self.use_case_key(use_case))
        if recipe_details is None:
            raise ValueError(f"Recipe {recipe_key} was not found")
        strategy = from_schema(recipe_details.json_schema)

        best_example = None
        max_key_count = -1

        for _ in range(10):
            try:
                example = strategy.example()
                current_key_count = _count_keys_recursively(example)

                if current_key_count > max_key_count:
                    max_key_count = current_key_count
                    best_example = example
            except Exception as e:
                print(f"Warning: Failed to generate an example due to: {e}")
                # Continue to next iteration even if one example fails

        if best_example is None:
            print("A valid sample could not be generated. Returning an empty dict.")
            best_example = {}
        return dict(best_example)  # type: ignore


def _count_keys_recursively(data: Any) -> int:
    """Recursively counts the total number of keys in dictionaries within the data."""
    count = 0
    if isinstance(data, dict):
        count += len(data)
        for value in data.values():
            count += _count_keys_recursively(value)
    elif isinstance(data, list):
        for item in data:
            count += _count_keys_recursively(item)
    return count


def _get_recipe_key(path: Path, entrypoint: str | None = None) -> str:
    if path.is_file():
        recipe_key = path.stem
    elif path.is_dir():
        if entrypoint:
            entrypoint_stem = Path(entrypoint).stem
            recipe_key = f"{path.name}/{entrypoint_stem}"
        else:
            recipe_key = path.name
    else:
        raise ValueError(f"Path must be a Python file or directory: {path}")

    return recipe_key


def _validate_python_file(path: Path) -> None:
    """Validate that the path exists, is a file and has a .py extension."""
    if not path.exists():
        raise FileNotFoundError(f"Python file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Expected a file path, got a directory or non-file: {path}")
    if path.suffix.lower() != ".py":
        raise ValueError(f"Expected a Python file with .py extension, got: {path}")


def _validate_recipe_directory(dir_path: Path, entrypoint: str | None = None) -> None:
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not dir_path.is_dir():
        raise ValueError(f"Expected a directory path, got a file: {dir_path}")

    main_py = dir_path / "main.py"
    main_py_exists = main_py.exists() and main_py.is_file()

    if entrypoint:
        if main_py_exists:
            raise ValueError(
                f"Cannot specify entrypoint when main.py already exists in directory: {dir_path}. "
                f"Either remove/rename main.py or use it directly without specifying an entrypoint."
            )
        entrypoint_path = dir_path / entrypoint
        if not entrypoint_path.exists() or not entrypoint_path.is_file():
            raise FileNotFoundError(f"Specified entrypoint file not found: {entrypoint} in directory {dir_path}")
    else:
        if not main_py_exists:
            raise FileNotFoundError(
                f"Directory must contain a 'main.py' file, or in alternative you must specify an `entrypoint` file"
            )


def _zip_directory_to_bytes_io(dir_path: Path, entrypoint: str | None = None) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dir_path):
            for file_name in files:
                file_path = Path(root) / file_name
                arcname = file_path.relative_to(dir_path)
                if entrypoint and arcname.as_posix() == entrypoint:
                    arcname = Path("main.py")

                zf.write(file_path, arcname.as_posix())
    buffer.seek(0)
    return buffer


@contextmanager
def _upload_from_path(path: str, entrypoint: str | None = None):
    p = Path(path)

    if p.is_file():
        if entrypoint:
            raise ValueError(f"Entrypoint parameter is not supported for single file recipe uploads")
        _validate_python_file(p)
        filename = p.name
        content_type = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        f = open(p, "rb")
        try:
            yield Upload(filename=filename, content=f, content_type=content_type)
        finally:
            f.close()
    elif p.is_dir():
        _validate_recipe_directory(p, entrypoint=entrypoint)
        zip_buffer = None
        try:
            zip_buffer = _zip_directory_to_bytes_io(p, entrypoint=entrypoint)
        except Exception:
            logger.error(f"Failed to create in-memory zip for directory upload.")
            raise
        filename = f"{p.name}.zip"
        try:
            yield Upload(filename=filename, content=zip_buffer, content_type="application/zip")
        finally:
            zip_buffer.close()
    else:
        if not p.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        raise ValueError(f"Path must be a Python file or a directory: {path}")
