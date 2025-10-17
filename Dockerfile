# Use a slim Python image
FROM python:3.10-slim

# Prevent Python from writing pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install OS dependencies and clean up to save space
RUN apt update && apt install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama (CLI only)
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy only requirements first for caching
COPY requirements.txt /app/

# Install Python dependencies (no cache)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app code
COPY . /app/

# Expose Streamlit port
EXPOSE 8501

# Pull Ollama models at container runtime (not during build)
CMD ["sh", "-c", "ollama pull znbang/bge:small-en-v1.5-q8_0 && ollama pull deepseek-r1:1.5b && ollama serve & streamlit run app_ui.py --server.port 8501 --server.address 0.0.0.0"]
