FROM python:3.11.4-slim-buster AS python-base
WORKDIR /app
ARG VIRTUAL_ENV=/opt/venv
RUN addgroup --gid 1001 app && adduser --uid 1000 --gid 1001 app
ENV VIRTUAL_ENV=$VIRTUAL_ENV \
    PATH=$VIRTUAL_ENV/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONBUFFERED=1 \
    PYTHONPATH=/app/src:$PYTHONPATH

FROM python-base AS dependencies-base
ARG PIP_VERSION=23.2.1
ARG POETRY_VERSION=1.6.1
RUN python -m pip install --no-cache-dir -U \
    "pip==$PIP_VERSION" \
    "poetry==$POETRY_VERSION" && \
    virtualenv "$VIRTUAL_ENV"
COPY --link pyproject.toml poetry.lock ./
RUN poetry install --without dev

FROM dependencies-base AS dependencies-release
COPY --link src .
COPY --link examples/tomodachi_app.py .
RUN poetry install --without dev

FROM dependencies-base AS development
RUN poetry install --with dev
COPY --link . .
RUN poetry install
CMD ["tomodachi", "run", "tomodachi_app.py"]

FROM python-base AS release
COPY --link --from=dependencies-release --chown=app:app /opt/venv /opt/venv
COPY --link --from=dependencies-release --chown=app:app /app .
USER app
CMD ["tomodachi", "run", "tomodachi_app.py", "--production"]
