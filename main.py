import os
from datetime import datetime

import httpcore
import notion_client.errors
from dateutil.relativedelta import relativedelta
from notion_client import Client
from notion_client.errors import APIResponseError
import logging

secret = None
database_id = None
notion = None

sorting = [{"timestamp": "last_edited_time", "direction": "descending"}]
due_date_filter = {"and": [{"property": "Frequency", "select": {"is_not_empty": True}},
                           {"property": "Complete", "checkbox": {"equals": True}}]}

recursive_top_level_filter = {"and": [{"property": "Top Level Task", "relation": {"is_empty": True}},
                                      {"property": "Parent Top Level Task",
                                       "rollup": {"none": {"relation": {"is_empty": True}}}}]}

recursive_top_level_filter_buggy = {"and": [{"property": "Top Level Task", "relation": {"is_empty": True}},
                                            {"and": [{"property": "Parent Task", "relation": {"is_not_empty": True}},
                                                     {"property": "Parent Top Level Task",
                                                      "rollup": {"none": {"relation": {"is_empty": True}}}}]}]}
request_interval_in_seconds = int(os.environ["REQUEST_INTERVAL_IN_SECONDS"])

report_task_id = '0aadbb93-4803-4212-ab79-f22c23bc529e'

report_filter_task = {"and": [{"property": "Complete", "checkbox": {"equals": True}},
                              {"property": "Reported", "checkbox": {"equals": False}}]}


def get_tasks(request):
    tasks = []
    for page in request["results"]:
        tasks.append(page)
    return tasks


def update_date_from_frequency(date: datetime, frequency: str):
    if frequency == "Daily":
        new_date = datetime.strftime(date + relativedelta(days=1), "%Y-%m-%d")
    elif frequency == "Weekly":
        new_date = datetime.strftime(date + relativedelta(weeks=1), "%Y-%m-%d")
    elif frequency == "Biweekly":
        new_date = datetime.strftime(date + relativedelta(weeks=2), "%Y-%m-%d")
    elif frequency == "Monthly":
        new_date = datetime.strftime(date + relativedelta(months=1), "%Y-%m-%d")
    elif frequency == "Bimonthly":
        new_date = datetime.strftime(date + relativedelta(months=2), "%Y-%m-%d")
    elif frequency == "Quarterly":
        new_date = datetime.strftime(date + relativedelta(months=3), "%Y-%m-%d")
    elif frequency == "Semiannually":
        new_date = datetime.strftime(date + relativedelta(months=6), "%Y-%m-%d")
    elif frequency == "Annually":
        new_date = datetime.strftime(date + relativedelta(years=1), "%Y-%m-%d")
    return new_date


def calculate_new_due_date(task):
    frequency = task["properties"]["Frequency"]["select"]["name"]
    old_due_date = datetime.strptime(task["properties"]["Due Date"]["date"]["start"], "%Y-%m-%d")
    return update_date_from_frequency(old_due_date, frequency)


def is_do_date_empty(task):
    if task["properties"]["Deadline"]["date"] is None:
        return True
    return False


def is_due_date_empty(task):
    if task["properties"]["Due Date"]["date"] is None:
        return True
    return False


def calculate_new_do_date(task):
    frequency = task["properties"]["Frequency"]["select"]["name"]
    old_do_date = datetime.strptime(task["properties"]["Deadline"]["date"]["start"], "%Y-%m-%d")
    return update_date_from_frequency(old_do_date, frequency)


def update_page_dates(task):
    new_due_date = calculate_new_due_date(task)
    try:
        if is_due_date_empty(task):
            return
        elif is_do_date_empty(task):
            notion.pages.update(page_id=task["id"], properties={"Due Date": {"date": {"start": new_due_date}},
                                                                "Complete": {"checkbox": False}})
        else:
            new_do_date = calculate_new_do_date(task)
            notion.pages.update(page_id=task["id"], properties={"Due Date": {"date": {"start": new_due_date}},
                                                                "Deadline": {"date": {"start": new_do_date}},
                                                                "Complete": {"checkbox": False}})
        logging.info("Updated task: " + task["id"])
    except notion_client.errors as e:
        raise


def update_top_level_task_field(task):
    if task["properties"]["Parent Task"]["relation"]:
        parent_top_level_task_ids = []
        for parent_top_level_task in task["properties"]["Parent Top Level Task"]["rollup"]["array"]:
            for relation_field in parent_top_level_task["relation"]:
                parent_top_level_task_ids.append(relation_field)
        try:
            notion.pages.update(page_id=task["id"],
                                properties={"Top Level Task": {"relation": parent_top_level_task_ids}})
            logging.info("Updated top level task field: " + task["id"])
        except notion_client.errors as e:
            raise


def update_reported_field(task):
    try:
        notion.pages.update(page_id=task["id"], properties={"Reported": {"checkbox": True}})
        logging.info("Updated reported field: " + task["id"])
    except notion_client.errors as e:
        raise


def update_due_dates():
    request = notion.databases.query(database_id=database_id, sorts=sorting, filter=due_date_filter)
    tasks = get_tasks(request)
    for task in tasks:
        update_page_dates(task)
        if task["id"] == report_task_id:
            update_reported_fields()


def update_top_level_task_dates():
    request = notion.databases.query(database_id=database_id, sorts=sorting, filter=recursive_top_level_filter)
    tasks = get_tasks(request)
    for task in tasks:
        update_top_level_task_field(task)


def update_reported_fields():
    request = notion.databases.query(database_id=database_id, sorts=sorting, filter=report_filter_task)
    tasks = get_tasks(request)
    for task in tasks:
        update_reported_field(task)


def main():
    global secret
    secret = str(os.environ["NOTION_SECRET"])
    global database_id
    global notion
    notion = Client(auth=secret)
    database_id = (os.environ["NOTION_DATABASE_ID"])
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting script")
    while True:
        try:
            update_due_dates()
            update_top_level_task_dates()
            os.system("sleep {}".format(request_interval_in_seconds))
        except APIResponseError as e:
            logging.error(e)
            logging.error("Failed to update due dates")
            os.system("sleep {}".format(request_interval_in_seconds * 4))
        except notion_client.errors.HTTPResponseError as e:
            logging.error(e)
            logging.error("Failed to update due dates")
            os.system("sleep {}".format(request_interval_in_seconds * 4))
        except httpcore.RemoteProtocolError as e:
            logging.error(e)
            logging.error("Failed to update due dates")
            os.system("sleep {}".format(request_interval_in_seconds * 4))
        except e:
            logging.error(e)
            logging.error("Failed to update due dates")
            os.system("sleep {}".format(request_interval_in_seconds * 4))


if __name__ == "__main__":
    main()
