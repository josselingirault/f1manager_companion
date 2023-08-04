# Intermediate image to setup the install
FROM python:3.11.4-slim as intermediate

ENV HOME=/usr/home \
    POETRY_VERSION=1.5.1

ENV POETRY_HOME=${HOME}/.poetry
ENV PROJECT_HOME=${HOME}/project

ENV PATH=${POETRY_HOME}/bin:${PATH}

RUN apt-get update && apt-get install -y curl
RUN curl -sSL https://install.python-poetry.org | python3 -

# poetry checks readme exists for some reason
COPY pyproject.toml poetry.lock ${PROJECT_HOME}/
COPY f1m_buddy/ ${PROJECT_HOME}/f1m_buddy/

RUN cd ${PROJECT_HOME} && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-root --only main


# Final image without garbage
FROM python:3.11.4-slim

ENV PROJECT_HOME=/usr/home/project

COPY --from=intermediate ${PROJECT_HOME} ${PROJECT_HOME}

ENV PATH=${PROJECT_HOME}/.venv/bin:${PATH}

WORKDIR ${PROJECT_HOME}
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "f1m_buddy/Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
