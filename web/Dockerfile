FROM python:3
WORKDIR /usr/src/app
COPY requiremets.txt .
RUN pip install --no-cache-dir -r requiremets.txt
COPY . .
CMD ["python", "app.py"]
