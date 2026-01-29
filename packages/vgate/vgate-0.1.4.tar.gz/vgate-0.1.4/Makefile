fmt:
	@uv tool run ruff check --select I --fix
	@uv tool run ruff format

# used by ci
check:
	uv tool run ruff check --select I
	uv tool run ruff format --check