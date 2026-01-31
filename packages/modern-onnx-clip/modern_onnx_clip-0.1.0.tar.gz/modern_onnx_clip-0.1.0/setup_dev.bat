@echo off
echo Installing dependencies with uv...
uv sync --all-extras

echo.
echo Setting up pre-commit hooks...
uv run pre-commit install

echo.
echo Setup complete! You can now use 'check.bat' to verify your code.
