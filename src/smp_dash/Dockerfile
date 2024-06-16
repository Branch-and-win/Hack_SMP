FROM python:3.10-slim

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
WORKDIR /app/

COPY . ./

CMD gunicorn -b 0.0.0.0:5020 src.smp_dash.app:app --timeout 90