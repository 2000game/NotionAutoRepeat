FROM python:3.9
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt
ENV NOTION_SECRET secret
ENV NOTION_DATABASE_ID id
ENV REQUEST_INTERVAL_IN_SECONDS 60

CMD ["python", "./main.py"]