# Video worker for Railway. Licensed fonts are not in git: mount or download them into /app/fonts at start.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg libegl1 libgles2 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY trialreels ./trialreels
COPY fonts ./fonts
RUN pip install --no-cache-dir .
# Fetch the face/hand models at build time so runs don't depend on the network.
RUN python -c "from trialreels import face; face._model('face'); face._model('hand')"

ENTRYPOINT ["trialreels"]
