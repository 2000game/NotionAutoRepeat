import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
from notion_client import Client

secret = str(os.environ["NOTION_SECRET"])
database_id = (os.environ["NOTION_DATABASE_ID"])

print(secret)
print(type(secret))

notion = Client(auth=secret)
sorting = [{"timestamp": "last_edited_time", "direction": "descending"}]
filter = {"and": [{"property": "Frequency", "select": {"is_not_empty": True}},
                  {"property": "Complete", "checkbox": {"equals": True}}]}

request_interval_in_seconds = int(os.environ["REQUEST_INTERVAL_IN_SECONDS"])


def get_tasks(request):
    tasks = []
    for page in request["results"]:
        tasks.append(page)
    return tasks

def update_date_from_frequency(date, frequency):
    if frequency == "Daily":
        new_date = datetime.strftime(date + relativedelta(days=1), "%Y-%m-%d")
    elif frequency == "Weekly":
        new_date = datetime.strftime(date + relativedelta(weeks=1), "%Y-%m-%d")
    elif frequency == "Biweekly":
        new_date = datetime.strftime(date + relativedelta(weeks=2), "%Y-%m-%d")
    elif frequency == "Monthly":
        new_date = datetime.strftime(date + relativedelta(month=1), "%Y-%m-%d")
    elif frequency == "Bimonthly":
        new_date = datetime.strftime(date + relativedelta(month=2), "%Y-%m-%d")
    elif frequency == "Quarterly":
        new_date = datetime.strftime(date + relativedelta(month=3), "%Y-%m-%d")
    elif frequency == "Semiannually":
        new_date = datetime.strftime(date + relativedelta(month=6), "%Y-%m-%d")
    elif frequency == "Annually":
        new_date = datetime.strftime(date + relativedelta(year=1), "%Y-%m-%d")
    return new_date



def calculate_new_due_date(task):
    frequency = task["properties"]["Frequency"]["select"]["name"]
    old_due_date = datetime.strptime(task["properties"]["Due Date"]["date"]["start"], "%Y-%m-%d")

    return update_date_from_frequency(old_due_date, frequency)




def is_do_date_empty(task):
    if task["properties"]["Do Date"]["date"] == {}:
        return True
    else:
        return False

def is_due_date_empty(task):
    if task["properties"]["Due Date"]["date"] == {}:
        return True
    else:
        return False


def calculate_new_do_date(task):
    frequency = task["properties"]["Frequency"]["select"]["name"]
    old_do_date = datetime.strptime(task["properties"]["Do Date"]["date"]["start"], "%Y-%m-%d")

    return update_date_from_frequency(old_do_date, frequency)


def update_page(task):
    new_due_date = calculate_new_due_date(task)
    if is_due_date_empty(task):
        return
    elif is_do_date_empty(task):
        notion.pages.update(page_id=task["id"], properties={"Due Date": {"date": {"start": new_due_date}},
                                                            "Complete": {"checkbox": False}})
    else:
        new_do_date = calculate_new_do_date(task)
        notion.pages.update(page_id=task["id"], properties={"Due Date": {"date": {"start": new_due_date}},
                                                            "Do Date": {"date": {"start": new_do_date}},
                                                            "Complete": {"checkbox": False}})


def main():
    while True:
        request = notion.databases.query(database_id=database_id, sorts=sorting, filter=filter)
        tasks = get_tasks(request)
        for task in tasks:
            update_page(task)
        os.system("sleep {}".format(request_interval_in_seconds))


if __name__ == "__main__":
    main()
