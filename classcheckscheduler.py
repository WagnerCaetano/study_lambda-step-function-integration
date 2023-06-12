import json
import boto3
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


REGION = os.getenv('REGION')
TABLE_NAME_CALENDARIO = os.getenv('TABLE_NAME_CALENDARIO')
AWS_ACCESS_KEY_ID = os.getenv('MY_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('MY_AWS_SECRET_ACCESS_KEY')
WEEK_DAYS_MAP = {
    "monday": "segunda",
    "tuesday": "terça",
    "wednesday": "quarta",
    "thursday": "quinta",
    "friday": "sexta",
    "saturday": "sábado",
    "sunday": "domingo"
}


class SchedulerBypassAttendanceToday(Exception):
    pass


def handler(event, context):
    # Retrieve the class schedule for today from the database
    dynamodb = boto3.resource('dynamodb', region_name=REGION, aws_access_key_id=AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    table = dynamodb.Table(TABLE_NAME_CALENDARIO)

    # Get the current day of the week
    today = datetime.now(pytz.timezone(
        'America/Sao_Paulo')).strftime('%A').lower()
    today = WEEK_DAYS_MAP[today]
    response = table.get_item(
        Key={
            'lista-dias-aulas': today
        }
    )
    class_schedule = response.get('Item')

    if class_schedule is None:
        # No class schedule found for today
        raise SchedulerBypassAttendanceToday(
            "No class schedule found for today")

    class_hour = class_schedule['horario']

    if not class_hour:
        # No class hour found for today
        raise SchedulerBypassAttendanceToday("No class hour found for today")

    class_time = datetime.strptime(class_hour, '%H:%M').replace(
        tzinfo=pytz.timezone('America/Sao_Paulo')).time()
    class_datetime = datetime.now().replace(
        hour=class_time.hour, minute=class_time.minute, second=0, microsecond=0)
    current_time = datetime.now(pytz.timezone('America/Sao_Paulo'))

    if class_datetime.replace(tzinfo=None) <= current_time.replace(tzinfo=None):
        # The class has already occurred today
        raise SchedulerBypassAttendanceToday(
            "No upcoming class found for today")

    wait_time_seconds = int((class_datetime.replace(
        tzinfo=pytz.timezone('America/Sao_Paulo')) - current_time.replace(tzinfo=pytz.timezone('America/Sao_Paulo'))).total_seconds())

    # Prepare the output with the class schedule and wait time
    output = {
        "classSchedule": class_schedule,
        "waitTime": wait_time_seconds + (30 * 60)
    }

    return output


print(handler(None, None))
