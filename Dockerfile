FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       git \
       git-lfs \
       make \
       libgl1 \
       libglu1-mesa \
       libx11-6 \
       libxrender1 \
       libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY pyproject.toml requirements.lock README.md ./
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.lock
COPY . .
RUN python -m pip install --no-cache-dir --no-deps -e .

CMD ["make", "check"]

