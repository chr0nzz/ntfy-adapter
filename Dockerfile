FROM python:3.9-slim
WORKDIR /app
RUN pip install --no-cache-dir flask requests gunicorn emoji
COPY app.py .
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
