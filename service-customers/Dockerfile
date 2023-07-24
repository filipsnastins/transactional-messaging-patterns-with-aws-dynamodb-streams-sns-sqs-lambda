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
ARG PIP_VERSION=23.2
ARG POETRY_VERSION=1.5.1
RUN python -m pip install --no-cache-dir -U \
  "pip==$PIP_VERSION" \
  "poetry==$POETRY_VERSION" && \
  virtualenv "$VIRTUAL_ENV"
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev

FROM dependencies-base AS dependencies-release
COPY src ./src
RUN poetry install --without dev

FROM dependencies-base AS development
RUN poetry install --with dev
COPY . .
RUN poetry install

FROM python-base AS release
COPY --from=dependencies-release --chown=app:app /opt/venv /opt/venv
COPY --from=dependencies-release --chown=app:app /app .
USER app
CMD ["tomodachi", "run", "entrypoints/tomodachi_app.py", "--production"]