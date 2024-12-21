# Use a base Python image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the backend code into the container
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose the port the Flask app will run on
EXPOSE 5002

# Command to run the backend Flask app
CMD ["python", "app.py"]
