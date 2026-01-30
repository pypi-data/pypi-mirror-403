import pytest
import os
import tempfile
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from adaptive_harmony.runtime.runner import _load_and_run_recipe, _parse_script_metadata
from adaptive_harmony.runtime.context import RecipeContext, RecipeConfig
from adaptive_harmony.runtime.data import InputConfig


@pytest.fixture
def mock_context():
    ctx = Mock(spec=RecipeContext)

    ctx.config = Mock(spec=RecipeConfig)
    ctx.config.job_id = "test-job-123"
    ctx.config.use_case = "test-use-case"
    ctx.config.user_input_file = None

    ctx.file_storage = Mock()
    ctx.file_storage.mk_url = Mock(return_value="file://test_path")

    ctx.job = Mock()
    ctx.job.report_error = Mock()

    return ctx


@pytest.fixture
def temp_recipe_file():
    content = """
from adaptive_harmony.runtime.decorators import recipe_main
from adaptive_harmony.runtime.context import RecipeContext

@recipe_main
def test_recipe(context: RecipeContext):
    print(f"Test recipe executed with job_id: {context.config.job_id}")
    return "test_success"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_user_input_file():
    input_data = {"name": "test_user", "value": 42}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name

    yield temp_path
    os.unlink(temp_path)


class TestLoadAndRunRecipe:
    def test_load_nonexistent_file(self, mock_context):
        with pytest.raises(FileNotFoundError, match="No such file or directory"):
            _load_and_run_recipe(mock_context, "/nonexistent/recipe.py")

    def test_load_recipe_with_temp_file(self, mock_context, temp_recipe_file):
        with patch("builtins.print") as mock_print:
            _load_and_run_recipe(mock_context, temp_recipe_file)
            mock_print.assert_any_call(f"Test recipe executed with job_id: {mock_context.config.job_id}")


class DummyInputConfig(InputConfig):
    name: str = "default"
    value: int = 0


class TestRunnerIntegration:

    @patch("adaptive_harmony.runtime.runner.RecipeContext.from_config")
    def test_main_with_recipe_file(self, mock_from_config, mock_context, temp_recipe_file):
        mock_from_config.return_value = mock_context

        test_argv = [
            "runner.py",
            "--recipe-file",
            str(temp_recipe_file),
            "--job-id",
            "test-main-job",
            "--harmony-url",
            "ws://localhost:12345",
        ]

        with patch.object(sys, "argv", test_argv):
            with patch("builtins.print") as _:
                from adaptive_harmony.runtime.runner import main

                try:
                    main()
                except SystemExit:
                    pass

                mock_from_config.assert_called_once()

    @patch("adaptive_harmony.runtime.runner.RecipeContext.from_config")
    def test_main_with_recipe_file_url_s3(self, mock_from_config, mock_context):
        import zipfile

        mock_from_config.return_value = mock_context

        # Create a temporary zip file with main.py
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.py content
            main_py_content = """
from adaptive_harmony.runtime.decorators import recipe_main
from adaptive_harmony.runtime.context import RecipeContext

@recipe_main
def main_recipe(context: RecipeContext):
    print(f"S3 recipe executed with job_id: {context.config.job_id}")
    return "s3_success"
"""

            # Create the zip file
            zip_path = os.path.join(temp_dir, "recipe.zip")
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("main.py", main_py_content)

            # Mock file storage download_locally to copy our zip file
            def mock_download(file_url, destination_path, use_raw_path=False):
                import shutil

                shutil.copy2(zip_path, destination_path)

            mock_context.file_storage.download_locally.side_effect = mock_download

            test_argv = [
                "runner.py",
                "--recipe-file-url",
                "s3://my-bucket/recipes/my-recipe.zip",
                "--job-id",
                "test-s3-job",
                "--harmony-url",
                "ws://localhost:12345",
            ]

            with patch.object(sys, "argv", test_argv):
                with patch("builtins.print") as _:
                    from adaptive_harmony.runtime.runner import main

                    try:
                        main()
                    except SystemExit:
                        pass

                    mock_from_config.assert_called_once()
                    mock_context.file_storage.download_locally.assert_called_once_with(
                        "s3://my-bucket/recipes/my-recipe.zip",
                        mock_context.file_storage.download_locally.call_args[0][1],
                        use_raw_path=True,
                    )

    @patch("adaptive_harmony.runtime.runner.RecipeContext.from_config")
    def test_main_with_recipe_file_url_s3_multiple_files(self, mock_from_config, mock_context):
        import zipfile

        mock_from_config.return_value = mock_context

        # Create a temporary zip file with main.py and a.py
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a.py content (dependency file)
            a_py_content = """
def get_message():
    return "Hello from a.py"

def get_multiplier():
    return 10
"""

            # Create main.py content that imports from a.py
            main_py_content = """
from adaptive_harmony.runtime.decorators import recipe_main
from adaptive_harmony.runtime.context import RecipeContext
from .a import get_message, get_multiplier

@recipe_main
def main_recipe(context: RecipeContext):
    message = get_message()
    multiplier = get_multiplier()
    print(f"S3 multi-file recipe executed with job_id: {context.config.job_id}")
    print(f"Message from a.py: {message}")
    print(f"Multiplier from a.py: {multiplier}")
    return f"multi_file_success_{multiplier}"
"""

            # Create the zip file with both files
            zip_path = os.path.join(temp_dir, "recipe_multi.zip")
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("main.py", main_py_content)
                zf.writestr("a.py", a_py_content)

            def mock_download(file_url, destination_path, use_raw_path=False):
                import shutil

                shutil.copy2(zip_path, destination_path)

            mock_context.file_storage.download_locally.side_effect = mock_download

            test_argv = [
                "runner.py",
                "--recipe-file-url",
                "s3://my-bucket/recipes/multi-file-recipe.zip",
                "--job-id",
                "test-s3-multi-job",
                "--harmony-url",
                "ws://localhost:12345",
            ]

            with patch.object(sys, "argv", test_argv):
                with patch("builtins.print") as mock_print:
                    # Clear any previously cached modules to avoid interference

                    modules_to_clear = ["main", "a"]
                    for module_name in modules_to_clear:
                        if module_name in sys.modules:
                            del sys.modules[module_name]

                    from adaptive_harmony.runtime.runner import main

                    try:
                        main()
                    except SystemExit:
                        pass

                    mock_from_config.assert_called_once()
                    mock_context.file_storage.download_locally.assert_called_once_with(
                        "s3://my-bucket/recipes/multi-file-recipe.zip",
                        mock_context.file_storage.download_locally.call_args[0][1],
                        use_raw_path=True,
                    )

                    # Verify that both files were correctly loaded and the dependency worked
                    mock_print.assert_any_call("S3 multi-file recipe executed with job_id: test-job-123")
                    mock_print.assert_any_call("Message from a.py: Hello from a.py")
                    mock_print.assert_any_call("Multiplier from a.py: 10")


class TestParseScriptMetadata:
    """Tests for _parse_script_metadata function."""

    def test_parse_script_metadata_with_valid_metadata(self):
        """Test parsing a script with valid adaptive metadata block."""
        content = """
# /// adaptive
# dependencies = [
#   "numpy>=1.20.0",
#   "pandas>=1.3.0",
#   "requests",
# ]
# ///

from adaptive_harmony.runtime.decorators import recipe_main

@recipe_main
def main():
    print("Hello, world!")
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            result = _parse_script_metadata(Path(temp_path))
            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 3
            assert "numpy>=1.20.0" in result
            assert "pandas>=1.3.0" in result
            assert "requests" in result
        finally:
            os.unlink(temp_path)

    def test_parse_script_metadata_without_metadata(self):
        """Test parsing a script without metadata block."""
        content = """from adaptive_harmony.runtime.decorators import recipe_main

@recipe_main
def main():
    print("Hello, world!")
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            result = _parse_script_metadata(Path(temp_path))
            assert result is None
        finally:
            os.unlink(temp_path)

    def test_parse_script_metadata_with_no_dependencies_field(self):
        """Test parsing a script with metadata but no dependencies field."""
        content = """
# /// adaptive
# version = "1.0.0"
# ///

from adaptive_harmony.runtime.decorators import recipe_main

@recipe_main
def main():
    print("Hello, world!")
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            result = _parse_script_metadata(Path(temp_path))
            assert result is None
        finally:
            os.unlink(temp_path)

    def test_parse_script_metadata_with_complex_dependencies(self):
        """Test parsing a script with complex dependency specifications."""
        content = """
# /// adaptive
# dependencies = [
#   "numpy>=1.20.0,<2.0.0",
#   "pandas[excel]>=1.3.0",
#   "requests~=2.28.0",
#   "scipy==1.7.3",
# ]
# ///

from adaptive_harmony.runtime.decorators import recipe_main

@recipe_main
def main():
    print("Hello, world!")
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            result = _parse_script_metadata(Path(temp_path))
            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 4
            assert "numpy>=1.20.0,<2.0.0" in result
            assert "pandas[excel]>=1.3.0" in result
            assert "requests~=2.28.0" in result
            assert "scipy==1.7.3" in result
        finally:
            os.unlink(temp_path)
