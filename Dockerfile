# Stage 1: Build TDLib
# We use a specific version of Ubuntu for compatibility
FROM ubuntu:22.04 as builder

# Install build dependencies for TDLib
RUN apt-get update && apt-get install --no-install-recommends -y \
  build-essential=12.9ubuntu3 \
  git=1:2.34.1-1ubuntu1.12 \
  cmake=3.22.1-1ubuntu1.22.04.2 \
  libssl-dev=3.0.2-0ubuntu1.19 \
  zlib1g-dev=1:1.2.11.dfsg-2ubuntu9 \
  gperf=3.1-1build1

# Clone and build TDLib
# Cloning a specific, stable version is recommended
RUN git clone --depth 1 --branch v1.8.46 https://github.com/tdlib/td.git
WORKDIR /td && \
  cmake -DCMAKE_BUILD_TYPE=Release . && \
  cmake --build . --target install

# Stage 2: Build the final application image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the built TDLib library from the builder stage
COPY --from=builder /usr/local/lib/libtd* /usr/local/lib/

# Install Poetry
RUN pip install --no-cache-dir poetry==2.1.3

# Copy the project files
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry config virtualenvs.create false && \
  poetry install --no-dev --no-root

# Copy the rest of the application code
COPY . .

# Command to run your application
CMD ["python", "-m", "tg_tui.main.py"]
