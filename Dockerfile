FROM ghcr.io/quarto-dev/quarto
WORKDIR /app
RUN apt-get update && apt-get install -y python3-pip
RUN pip install fastapi[all] fastcore uvicorn
COPY . .
CMD uvicorn main:app --host 0.0.0.0 --port $PORT

