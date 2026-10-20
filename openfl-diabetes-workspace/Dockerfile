FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

COPY requirements.txt /tmp/workspace-requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install "openfl==1.9" -r /tmp/workspace-requirements.txt

CMD ["bash"]
