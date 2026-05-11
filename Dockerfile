# HF Spaces root Dockerfile
FROM python:3.10-slim

# HF Spaces requires a non-root user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Install dependencies from backend folder
COPY --chown=user backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Copy all application files from backend directory to /app
COPY --chown=user backend/ .

# HF Spaces must expose port 7860
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
