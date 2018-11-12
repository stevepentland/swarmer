FROM python:3.7-stretch
WORKDIR /app
COPY . /app/
RUN pip install -r ./requirements.txt
EXPOSE 8500

ENTRYPOINT ["python", "swarmer.py"]