import boto3
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv('REGION')
TABLE_NAME_ALUNO = os.getenv('TABLE_NAME_ALUNO')
AWS_ACCESS_KEY_ID = os.getenv('MY_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('MY_AWS_SECRET_ACCESS_KEY')


class StudentsNotFoundException(Exception):
    pass


def handler(event, context):
    # Retrieve the list of students from the database or any other source
    dynamodb = boto3.resource('dynamodb', region_name=REGION, aws_access_key_id=AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    table = dynamodb.Table(TABLE_NAME_ALUNO)
    response = table.scan()
    students = response['Items']

    if not students:
        # No students found
        raise StudentsNotFoundException("No students found")

    # Perform attendance check for each student
    for student in students:
        history = student['historico']
        today = datetime.now(pytz.timezone(
            'America/Sao_Paulo')).strftime('%d/%m/%Y')

        # Check if attendance record exists for today
        attendance_exists = False
        for entry in history:
            if entry['data'] == today:
                attendance_exists = True
                break

        # Update attendance record if absent
        if not attendance_exists:
            new_entry = {
                "data": today,
                "dia": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%A').lower(),
                "hora": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%H:%M'),
                "id_historico": str(len(history) + 1),
                "presente": False
            }
            history.append(new_entry)

            # Update the student's attendance record in the database
            table.update_item(
                Key={
                    'matricula': student['matricula']
                },
                UpdateExpression="SET historico = :h",
                ExpressionAttributeValues={
                    ":h": history
                }
            )

    return {
        "message": "Attendance check completed"
    }


print(handler(None, None))
