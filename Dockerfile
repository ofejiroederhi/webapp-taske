# 1. Use an official, lightweight Python image
FROM python:3.11-slim

# 2. Create a non-root user for security (avoid running as root)
RUN useradd -m secureuser

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 6. Initialise the database
RUN python init_db.py

# 7. Transfer ownership of the app directory to the non-root user
RUN chown -R secureuser:secureuser /app

# 8. Switch to the non-root user before running the app
USER secureuser

# 9. Expose the port Flask runs on
EXPOSE 5000

# 10. Start the application
CMD ["python", "app.py"]
