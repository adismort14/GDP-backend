FROM python:3.8-slim

ENV FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=8080 \
    GITHUB_CLIENT_ID=<enter_your_client_id> \
    GITHUB_CLIENT_SECRET=<enter_your_client_secret>

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["flask", "run"]

# Build the above: docker build -t flask-backend .
# Run the above built image: docker run -p 8080:8080 flask-backend

