import os
import shutil
from json import loads
from pathlib import Path
from typing import Optional

from celery import Celery, group
from celery.schedules import crontab

from image import blur_image
from mail import send_email
from redis_client import client

celery_app = Celery(
    'celery',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
)


@celery_app.task
def blur_image_task(src_filepath: str, dst_filepath: Optional[str] = None):
    blur_image(src_filename=src_filepath, dst_filename=dst_filepath)
    return f'{src_filepath}\nImage blured'


@celery_app.task
def archive_files_task(arch_name: str, file_format: str):
    shutil.make_archive(base_name=arch_name, format=file_format, root_dir=arch_name)
    return 'File has been archived successfully'


@celery_app.task
def send_email_task(order_id: str, user_email: str, file_path: str):
    body = ('Вас приветствует сервис Processing Images. '
            'Обработанные фото по вашему заказу находятся в прикрепленном файле!')
    send_email(order_id=order_id, receiver=user_email, body=body, filename=file_path)
    return 'Email has been sent successfully'


@celery_app.task
def remove_files_task(data_path: str):
    if Path(data_path).exists() and Path(data_path).is_dir():
        shutil.rmtree(data_path)

    if Path(data_path + '.zip').exists():
        os.remove(data_path + '.zip')

    return 'All files has been removed successfully'


@celery_app.task
def send_subscribe_email_task(user_email: str):
    body = ('Вас приветствует сервис Processing Images. '
            'Пришлите нам фотографии для обработки!')
    send_email(receiver=user_email, body=body)
    return f'Subscribe email for {user_email} has been sent successfully'


@celery_app.task
def weekly_mailing():
    subscribes = client.get('subscribes')

    if subscribes:
        subscribe_dict = loads(subscribes)

        subscribes_emails_tasks = (
            send_subscribe_email_task.si(email)
            for email, value in subscribe_dict.items()
            if value
        )

        task_group = group(subscribes_emails_tasks)
        result = task_group.apply_async()
        return f'group_id {result.id}'


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour='10', minute='00', day_of_week='1'),
        weekly_mailing.s()
    )
