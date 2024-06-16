# Instructions copied from - https://hub.docker.com/_/python/
FROM python:3.10-alpine

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
WORKDIR /app/

COPY . ./

# tell the port number the container should expose
#EXPOSE 6027

#RUN python3 -m pytest .

# run the command
# CMD ["gunicorn", "-b", "0.0.0.0:6027", "-t", "600", "app_flask:create_app()"]
# CMD ["python3", "app_flask.py", "-d", "True"]
#CMD ["gunicorn", "-b", "0.0.0.0:6027", "--log-level=debug", "-t", "600", "--worker-class", "uvicorn.workers.UvicornWorker", "app_fastapi:create_app()"]
# CMD ["python3", "app_flask.py", "-d", "True"]
#CMD ["fastapi", "run", "src/smp_scenario/app.py", "--proxy-headers", "--port", "5021"]
#CMD ls src/smp_scenario
#CMD uvicorn app.app_fastapi:app --reload --host 0.0.0.0 --port 8000
# RUN apk add --no-cache bash

#CMD gunicorn -b 0.0.0.0:5021 src.smp_scenario.app:app
CMD gunicorn -b 0.0.0.0:5021 src.smp_scenario.app:app --worker-class uvicorn.workers.UvicornWorker --timeout 0