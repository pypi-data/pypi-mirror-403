FROM python:3.11-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the package
COPY . .

# Use build arg for versioning if provided (avoids needing git in the image)
ARG VERSION
ENV SETUPTOOLS_SCM_PRETEND_VERSION=$VERSION

# Install the package
RUN pip install .

ENTRYPOINT ["norm-findings"]
