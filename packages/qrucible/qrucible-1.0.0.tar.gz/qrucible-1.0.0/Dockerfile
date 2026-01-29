FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python -m pip install -U pip

# Install from PyPI (fast path). Requires that a wheel exists for your platform.
# NOTE: This installs the published PyPI version, not the local repo code.
# For builds that match repo code, use Dockerfile.dev or pin a specific version:
#   ARG QRUCIBLE_VERSION=0.1.0
#   RUN python -m pip install qrucible==${QRUCIBLE_VERSION}
RUN python -m pip install qrucible

WORKDIR /work

CMD ["python", "-c", "import qrucible; print('qrucible import ok')"]
