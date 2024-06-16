FROM python:3.10-alpine

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
WORKDIR /app/

COPY . ./

CMD gunicorn -b 0.0.0.0:5021 src.smp_scenario.app:app --worker-class uvicorn.workers.UvicornWorker --timeout 0