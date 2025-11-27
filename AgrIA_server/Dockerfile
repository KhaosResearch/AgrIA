# Use a base image that already has Python and Miniconda (recommended since you use Conda)
# We use a slim Python image for smaller size, but add Conda/Mamba for environment management
FROM condaforge/mambaforge:latest

# -----------------------
# System dependencies
# -----------------------
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# -----------------------
# Set working directory
# -----------------------
WORKDIR /app

# -----------------------
# Install Python/Conda deps
# -----------------------

# Copy the Conda environment file
COPY environment-docker.yml .
# COPY install_docker_deps.sh .
# COPY start.sh .

# Make the script executable
# RUN chmod +x install_docker_deps.sh
# RUN chmod +x start.sh
# RUN sed -i 's/\r$//' start.sh

# Create the Conda environment using Mamba (faster than Conda)
# This installs all your dependencies defined in environment-docker.yml
# RUN ./install_docker_deps.sh 
RUN mamba env update --file environment-docker.yml && \
    mamba clean -afy

# Make environment detected globally
ENV CONDA_DEFAULT_ENV=agria_server_env
ENV PATH="/opt/conda/envs/agria_server_env/bin:$PATH"

# -----------------------
# Copy code AFTER env build for caching
# -----------------------
COPY . .

# -----------------------
# Expose API port
# -----------------------
EXPOSE 5000

# -----------------------
# CMD for runtime
# -----------------------
# CMD mamba run -n agria_server_env gunicorn -w 4 -b 0.0.0.0:5000 run:app
CMD ["/bin/bash", "./start.sh"]