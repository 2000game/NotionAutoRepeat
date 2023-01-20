FROM python:3.9
WORKDIR /app
ENV NOTION_SECRET secret
ENV NOTION_DATABASE_ID database_id
ENV REQUEST_INTERVAL_IN_SECONDS 60
COPY . .
RUN pip3 install -r requirements.txt
CMD ["python", "./main.py"]