# Use uv image from ghcr.io
# Avoid using image from dockerhub to prevent rate limiting
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Install git as it's required for setuptools-scm to generate the version
# Curl is used by some k8s liveness probe
RUN apt-get update && apt-get install --no-install-recommends -y \
  libomniorb4-2 \
  libzmq5 \
  git curl \
  && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /tangogql

# Copy only the requirements so this layer can be cached
# and updated only when they change
COPY requirements.txt /requirements.txt
# uv uses $HOME/.cache/uv to cache downloads
# We don't want to store that in the docker image
# Use a cache mount to specify a persistent location (on the host) to be used during builds
RUN --mount=type=cache,target=/root/.cache \
    uv venv && uv pip install -r /requirements.txt

# Copy all files from the current directory to the working directory in the container
COPY . .

# Install application
RUN --mount=type=cache,target=/root/.cache \
    uv pip install -e .

# Expose port 5004 to allow external access to the application
EXPOSE 5004

ENV PYTHONUNBUFFERED 1

ENV PATH=/tangogql/.venv/bin:$PATH

# Use CMD to run uvicorn with the required arguments
# using the recommended exec form
# See https://docs.docker.com/reference/build-checks/json-args-recommended/
CMD ["uvicorn", "tangogql.main:app", "--host", "0.0.0.0", "--port", "5004"]
