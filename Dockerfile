# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn
RUN pip install gunicorn

# Copy SSL certificates
COPY selfsigned.crt /usr/src/app/selfsigned.crt
COPY selfsigned.key /usr/src/app/selfsigned.key

# Expose port 443 for SSL traffic
EXPOSE 443

# Define environment variable
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run app.py using Gunicorn with SSL when the container launches
# CMD is overridden by docker-compose.yml
