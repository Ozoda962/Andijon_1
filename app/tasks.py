from celery import shared_task
from django.utils import timezone
from datetime import date
import os
from app.management.commands.csv_reader import read_all_csv_from_folder
from django.core.management import call_command

folder = "C:\\Users\\user\\Desktop\\ftp"
FILE_PATH = read_all_csv_from_folder(folder)

@shared_task()
def run_extract_data_from_csv_bp():
    call_command("extract_data_from_CSV_BP")
    return "extract_data_from_CSV_BP finished successfully"
