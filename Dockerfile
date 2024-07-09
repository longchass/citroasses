# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Expose port 5432 for PostgreSQL and 80 for the FastAPI application
EXPOSE 5432 80

# Set environment variables for PostgreSQL
ENV POSTGRES_USER="admin"
ENV POSTGRES_PASSWORD="admin"
ENV POSTGRES_DB="mydb"

# Create a script to initialize PostgreSQL, create user and database, and start the FastAPI app
RUN echo "#!/bin/bash\n\
set -e\n\
\n\
# Start PostgreSQL service\n\
service postgresql start\n\
\n\
# Wait for PostgreSQL to start\n\
until pg_isready; do\n\
  echo 'Waiting for PostgreSQL to start...'\n\
  sleep 1\n\
done\n\
\n\
# Create user and database\n\
su - postgres -c \"psql -c \\\"CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';\\\"\"\n\
su - postgres -c \"createdb -O $POSTGRES_USER $POSTGRES_DB\"\n\
\n\
# Start the FastAPI app\n\
uvicorn main:app --host 0.0.0.0 --port 80\n\
" > /start.sh && chmod +x /start.sh

# Run the start script
CMD ["/start.sh"]