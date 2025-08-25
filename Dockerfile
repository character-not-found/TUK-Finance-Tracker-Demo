FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for some Python packages
# This includes curl for downloading rustup
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -r demotuk && useradd -r -g demotuk demotuk

# Install Rust toolchain using rustup
# This command downloads and installs Rust, including cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Set the PATH environment variable globally for all subsequent commands
# This ensures that Rust binaries (like rustc and cargo) are found
ENV PATH="/root/.cargo/bin:$PATH"

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Create the logs directory if it doesn't exist (important for volume mounting)
RUN mkdir -p /logs && chown -R demotuk:demotuk /logs && chown -R demotuk:demotuk /app

# Switch to the non-root user
USER demotuk

# Expose the port that FastAPI will run on
EXPOSE 12000

# Define the command to run your application using Uvicorn
# 'main:app' refers to the 'app' object in 'main.py'
# --host 0.0.0.0 makes the server accessible from outside the container
# --port 9000 specifies the port
# --reload is good for development, but remove it for production for better performance
CMD ["uvicorn", "app.api.routes:app", "--host", "0.0.0.0", "--port", "12000"]
