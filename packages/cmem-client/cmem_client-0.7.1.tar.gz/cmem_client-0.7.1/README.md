<!-- markdownlint-disable MD012 MD013 MD024 MD033 -->
# cmem-client

Next generation eccenca Corporate Memory client library.

  
[![poetry][poetry-shield]][poetry-link] [![ruff][ruff-shield]][ruff-link] [![mypy][mypy-shield]][mypy-link] [![copier][copier-shield]][copier]

## Development

- Run [task](https://taskfile.dev/) to see all major development tasks.
- Use [pre-commit](https://pre-commit.com/) to avoid errors before commit.
- This repository was created with [this copier template](https://github.com/eccenca/cmem-plugin-template).

## Goals

Compared to [cmem-cmempy](https://pypi.org/project/cmem-cmempy/), this package was started to have the following advantages:

- Better logging:
  - ?
- Validation of incoming data:
  - This is done using [pydantic](https://github.com/pydantic/pydantic).
  - See the `models` subdirectory for details.
- Availability of data objects and proper typing:
  - In addition to pydantic models, we use [mypy](https://www.mypy-lang.org/) to complain about untyped code.
- Async capabilities:
  - Switching from requests to [httpx](https://www.python-httpx.org/) allows for using asynchronous calls as well as HTTP/2 sessions, if needed.
- Documentation:
  - [MkDocs](https://www.mkdocs.org/) together with [mkdocstrings](https://mkdocstrings.github.io/) build the foundation for nice developer documentation.

[poetry-link]: https://python-poetry.org/
[poetry-shield]: https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json
[ruff-link]: https://docs.astral.sh/ruff/
[ruff-shield]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&label=Code%20Style
[mypy-link]: https://mypy-lang.org/
[mypy-shield]: https://www.mypy-lang.org/static/mypy_badge.svg
[copier]: https://copier.readthedocs.io/
[copier-shield]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json

