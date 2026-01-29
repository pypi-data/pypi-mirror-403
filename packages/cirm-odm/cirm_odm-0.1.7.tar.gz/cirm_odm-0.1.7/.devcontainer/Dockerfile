FROM mcr.microsoft.com/devcontainers/python:3.8

RUN python -m pip install --upgrade pip \
    && python -m pip install 'flit>=3.8.0' pre-commit

ENV FLIT_ROOT_INSTALL=1

COPY pyproject.toml .
RUN touch README.md \
    && mkdir -p src/cirm_odm \
    && python -m flit install --only-deps --deps develop \
    && rm -r pyproject.toml README.md src
