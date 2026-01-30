from __future__ import annotations

from airflow.models import BaseOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.context import Context
from typing import Any, Sequence
import fnmatch
import re


class OzoneListFilesOperator(BaseOperator):
    """
    Operator to list files in Apache Ozone bucket with optional wildcard pattern support.

    Ozone uses S3-compatible API, so we leverage S3Hook for connectivity.
    Supports FS (file system) mode for on-prem BigData environments.

    :param bucket_name: The Ozone bucket name or link name
    :param prefix: Optional prefix to filter keys (folder path)
    :param pattern: Optional wildcard pattern for filtering files (supports *, ?, [seq], [!seq])
                   Examples: 'data_202501*_for_source', 'data_for_source_202501*', '*_202501_*'
    :param aws_conn_id: The Airflow connection ID for Ozone (S3-compatible)
    :param delimiter: Delimiter for folder hierarchy (default: '/')
    :param recursive: If True, list files recursively in all subfolders (default: True)
    """

    template_fields: Sequence[str] = (
        "bucket_name",
        "prefix",
        "pattern",
        "aws_conn_id",
    )

    def __init__(
        self,
        *,
        bucket_name: str,
        prefix: str | None = None,
        pattern: str | None = None,
        aws_conn_id: str = "ozone_default",
        delimiter: str = "/",
        recursive: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.bucket_name = bucket_name
        self.prefix = prefix or ""
        self.pattern = pattern
        self.aws_conn_id = aws_conn_id
        self.delimiter = delimiter
        self.recursive = recursive

    def _convert_pattern_to_regex(self, pattern: str) -> re.Pattern:
        """
        Convert a wildcard pattern to a regex pattern.
        Supports:
            - * : matches any sequence of characters
            - ? : matches any single character
            - [seq] : matches any character in seq
            - [!seq] : matches any character not in seq
        """
        return re.compile(fnmatch.translate(pattern))

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """
        Check if a key matches the given wildcard pattern.
        The pattern can have wildcards at the beginning, middle, or end.

        Examples:
            - 'data_202501*_for_source' matches 'data_20250115_for_source'
            - 'data_for_source_202501*' matches 'data_for_source_20250131.csv'
            - '*_202501_*' matches 'prefix_202501_suffix.txt'
        """
        # Extract just the filename from the full key path for matching
        filename = key.split(self.delimiter)[-1] if self.delimiter in key else key

        # Use fnmatch for wildcard matching (handles *, ?, [seq], [!seq])
        return fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(key, pattern)

    def execute(self, context: Context) -> list[str]:
        hook = S3Hook(aws_conn_id=self.aws_conn_id)

        self.log.info(f"Listing files in bucket '{self.bucket_name}' with prefix '{self.prefix}'")

        if self.recursive:
            # List all keys recursively
            keys = hook.list_keys(
                bucket_name=self.bucket_name,
                prefix=self.prefix,
            )
        else:
            # List only immediate children (non-recursive)
            keys = hook.list_keys(
                bucket_name=self.bucket_name,
                prefix=self.prefix,
                delimiter=self.delimiter,
            )

        if not keys:
            self.log.info("No files found in the specified location.")
            return []

        # Apply pattern filtering if specified
        if self.pattern:
            self.log.info(f"Applying wildcard pattern filter: '{self.pattern}'")
            filtered_keys = [key for key in keys if self._match_pattern(key, self.pattern)]
            self.log.info(f"Found {len(filtered_keys)} files matching pattern '{self.pattern}' out of {len(keys)} total files")

            for key in filtered_keys:
                self.log.info(f"  - {key}")

            return filtered_keys
        else:
            self.log.info(f"Found {len(keys)} files:")
            for key in keys:
                self.log.info(f"  - {key}")

            return keys


class OzoneMoveObjectsOperator(BaseOperator):
    """
    Operator to move objects (with their folder structure) from one Ozone bucket to another.

    This operator copies objects from source to destination and then deletes
    the source objects. Supports moving entire folder hierarchies.

    For FS (file system) mode in on-prem BigData environments, this preserves
    the directory structure when moving files.

    :param source_bucket: Source Ozone bucket name
    :param dest_bucket: Destination Ozone bucket name
    :param source_prefix: Source prefix/folder path to move from
    :param dest_prefix: Destination prefix/folder path to move to (default: same as source)
    :param pattern: Optional wildcard pattern to filter which files to move
    :param aws_conn_id: The Airflow connection ID for Ozone (S3-compatible)
    :param preserve_structure: If True, preserve folder structure relative to source_prefix (default: True)
    :param delete_source: If True, delete source files after successful copy (default: True)
    :param batch_size: Number of objects to process in each batch for deletion (default: 1000)
    """

    template_fields: Sequence[str] = (
        "source_bucket",
        "dest_bucket",
        "source_prefix",
        "dest_prefix",
        "pattern",
        "aws_conn_id",
    )

    def __init__(
        self,
        *,
        source_bucket: str,
        dest_bucket: str,
        source_prefix: str | None = None,
        dest_prefix: str | None = None,
        pattern: str | None = None,
        aws_conn_id: str = "ozone_default",
        preserve_structure: bool = True,
        delete_source: bool = True,
        batch_size: int = 1000,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.source_bucket = source_bucket
        self.dest_bucket = dest_bucket
        self.source_prefix = source_prefix or ""
        self.dest_prefix = dest_prefix if dest_prefix is not None else self.source_prefix
        self.pattern = pattern
        self.aws_conn_id = aws_conn_id
        self.preserve_structure = preserve_structure
        self.delete_source = delete_source
        self.batch_size = batch_size

    def _match_pattern(self, key: str, pattern: str, delimiter: str = "/") -> bool:
        """Check if a key matches the wildcard pattern."""
        filename = key.split(delimiter)[-1] if delimiter in key else key
        return fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(key, pattern)

    def _get_dest_key(self, source_key: str) -> str:
        """
        Calculate the destination key for a source key.
        Preserves folder structure relative to source_prefix.
        """
        if self.preserve_structure:
            # Remove source prefix and add destination prefix
            if self.source_prefix and source_key.startswith(self.source_prefix):
                relative_path = source_key[len(self.source_prefix):].lstrip("/")
            else:
                relative_path = source_key

            if self.dest_prefix:
                dest_prefix = self.dest_prefix.rstrip("/")
                return f"{dest_prefix}/{relative_path}"
            return relative_path
        else:
            # Just use the filename
            filename = source_key.split("/")[-1]
            if self.dest_prefix:
                dest_prefix = self.dest_prefix.rstrip("/")
                return f"{dest_prefix}/{filename}"
            return filename

    def execute(self, context: Context) -> dict[str, Any]:
        hook = S3Hook(aws_conn_id=self.aws_conn_id)
        client = hook.get_conn()

        self.log.info(
            f"Moving objects from '{self.source_bucket}/{self.source_prefix}' "
            f"to '{self.dest_bucket}/{self.dest_prefix}'"
        )

        # List all source keys
        source_keys = hook.list_keys(
            bucket_name=self.source_bucket,
            prefix=self.source_prefix,
        )

        if not source_keys:
            self.log.info("No files found in source location.")
            return {"moved_count": 0, "moved_files": []}

        # Apply pattern filtering if specified
        if self.pattern:
            self.log.info(f"Applying wildcard pattern filter: '{self.pattern}'")
            source_keys = [key for key in source_keys if self._match_pattern(key, self.pattern)]
            self.log.info(f"Found {len(source_keys)} files matching pattern")

        moved_files = []
        failed_files = []

        for source_key in source_keys:
            dest_key = self._get_dest_key(source_key)

            try:
                # Copy object to destination
                self.log.info(f"Copying: {self.source_bucket}/{source_key} -> {self.dest_bucket}/{dest_key}")

                copy_source = {"Bucket": self.source_bucket, "Key": source_key}
                client.copy_object(
                    CopySource=copy_source,
                    Bucket=self.dest_bucket,
                    Key=dest_key,
                )

                moved_files.append({
                    "source": f"{self.source_bucket}/{source_key}",
                    "destination": f"{self.dest_bucket}/{dest_key}",
                })

            except Exception as e:
                self.log.error(f"Failed to copy {source_key}: {str(e)}")
                failed_files.append({"key": source_key, "error": str(e)})

        # Delete source files if requested and copy was successful
        if self.delete_source and moved_files:
            self.log.info(f"Deleting {len(moved_files)} source files...")

            keys_to_delete = [
                source_key for source_key in source_keys
                if any(m["source"].endswith(source_key) for m in moved_files)
            ]

            # Delete in batches
            for i in range(0, len(keys_to_delete), self.batch_size):
                batch = keys_to_delete[i:i + self.batch_size]
                try:
                    hook.delete_objects(bucket=self.source_bucket, keys=batch)
                    self.log.info(f"Deleted batch of {len(batch)} files")
                except Exception as e:
                    self.log.error(f"Failed to delete batch: {str(e)}")

        result = {
            "moved_count": len(moved_files),
            "failed_count": len(failed_files),
            "moved_files": moved_files,
            "failed_files": failed_files,
        }

        self.log.info(f"Move operation complete. Moved: {len(moved_files)}, Failed: {len(failed_files)}")

        return result


class OzoneFileExistsOperator(BaseOperator):
    """
    Operator to check if files exist in Ozone bucket matching a pattern.

    Useful for conditional workflows where subsequent tasks depend on
    the presence of specific files.

    :param bucket_name: The Ozone bucket name
    :param prefix: Prefix/folder path to search in
    :param pattern: Wildcard pattern to match files
    :param aws_conn_id: The Airflow connection ID for Ozone
    :param min_count: Minimum number of files required (default: 1)
    :param fail_if_not_found: If True, fail the task if files not found (default: False)
    """

    template_fields: Sequence[str] = (
        "bucket_name",
        "prefix",
        "pattern",
        "aws_conn_id",
    )

    def __init__(
        self,
        *,
        bucket_name: str,
        prefix: str | None = None,
        pattern: str | None = None,
        aws_conn_id: str = "ozone_default",
        min_count: int = 1,
        fail_if_not_found: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.bucket_name = bucket_name
        self.prefix = prefix or ""
        self.pattern = pattern
        self.aws_conn_id = aws_conn_id
        self.min_count = min_count
        self.fail_if_not_found = fail_if_not_found

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Check if a key matches the wildcard pattern."""
        filename = key.split("/")[-1] if "/" in key else key
        return fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(key, pattern)

    def execute(self, context: Context) -> bool:
        hook = S3Hook(aws_conn_id=self.aws_conn_id)

        self.log.info(f"Checking for files in '{self.bucket_name}/{self.prefix}'")

        keys = hook.list_keys(
            bucket_name=self.bucket_name,
            prefix=self.prefix,
        )

        if not keys:
            keys = []

        # Apply pattern filtering if specified
        if self.pattern:
            keys = [key for key in keys if self._match_pattern(key, self.pattern)]
            self.log.info(f"Found {len(keys)} files matching pattern '{self.pattern}'")
        else:
            self.log.info(f"Found {len(keys)} files")

        exists = len(keys) >= self.min_count

        if not exists and self.fail_if_not_found:
            raise FileNotFoundError(
                f"Expected at least {self.min_count} files matching pattern "
                f"'{self.pattern}' in '{self.bucket_name}/{self.prefix}', "
                f"but found {len(keys)}"
            )

        return exists
