FROM phidata/python:3.12

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    ffmpeg \
    libsm6 \
    libxext6 \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    graphviz \
    pandoc \
    imagemagick \
    fonts-liberation \
    gconf-service \
    libappindicator1 \
    libasound2 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libfontconfig1 \
    libgbm-dev \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Add dockerize for service readiness
RUN wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-v0.6.1.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-v0.6.1.tar.gz \
    && rm dockerize-linux-amd64-v0.6.1.tar.gz

ARG USER=app
ARG APP_DIR=/app
ENV APP_DIR=${APP_DIR}
ENV PYTHONPATH=${APP_DIR}:${PYTHONPATH}

# Create user and home directory
RUN groupadd -g 61000 ${USER} \
  && useradd -g 61000 -u 61000 -ms /bin/bash -d ${APP_DIR} ${USER}

WORKDIR ${APP_DIR}

# Copy requirements.txt
COPY requirements_windows.txt ./requirements.txt

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Convert line endings and make entrypoint executable
RUN apt-get update && apt-get install -y dos2unix \
    && dos2unix /app/scripts/entrypoint.sh \
    && chmod +x /app/scripts/entrypoint.sh \
    && apt-get remove -y dos2unix && apt-get autoremove -y

# Create necessary directories with correct permissions
RUN mkdir -p /app/data/cache /app/data/downloads /app/logs /app/data/knowledge \
    && chown -R ${USER}:${USER} ${APP_DIR} /app/data /app/logs

# Configure ImageMagick policy to allow PDF operations
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml

# Switch to non-root user
USER ${USER}

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["streamlit", "run", "app/Home.py"]
