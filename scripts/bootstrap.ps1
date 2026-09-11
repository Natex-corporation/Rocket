$ErrorActionPreference = 'Stop'
$Python = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
if ($Python -eq 'py') {
    & py -3.13 -m venv .venv
} else {
    & python -m venv .venv
}
& .\.venv\Scripts\python -m pip install --upgrade pip
& .\.venv\Scripts\python -m pip install -e '.[dev]'
& .\.venv\Scripts\python -m pytest
