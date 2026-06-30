FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=True
ENV PIP_NO_CACHE_DIR=1

WORKDIR /Statschat

# copy subset of files as specified by dockerignore
COPY . ./

RUN python -m pip install --upgrade pip \
    && python -m pip install ".[backend]"

EXPOSE 8080
CMD ["uvicorn", "fast-api.main_api_cloud:app", "--host", "0.0.0.0", "--port", "8080"]
