# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application into the container
# COPY ../lib/ /app/lib
COPY ./src/ /app/

# Make port 5000 available
EXPOSE 5000
ENV PYTHONPATH=${PYTHONPATH}:/app/:/app/lib/
# TERM environment variable not set.
ENV TERM=xterm-256color

# Run app.py when the container launches
CMD ["python", "app.py"]
