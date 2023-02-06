FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=secret,id=xlwnjlq93dru3lakgbpit7f7l
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]