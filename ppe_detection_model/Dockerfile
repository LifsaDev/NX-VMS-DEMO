# Base image with Python and CUDA support
FROM nvidia/cuda:12.4-cudnn8-runtime-ubuntu22.04

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the PPE detection model code
COPY . .

# Command to run the PPE detection script
CMD ["python", "ppe_detection.py"]
