import os
import random
from json import loads, dumps
from pathlib import Path

from celery import group, chain, chord
from flask import Flask, jsonify
from werkzeug.utils import secure_filename

from forms import BlurImagesForm, SubscribeForm
from tasks import archive_files_task, blur_image_task, celery_app, send_email_task, remove_files_task
from redis_client import client

ORDER_COUNTER = 1

UPLOAD_FOLDER = Path('downloads/')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/blur', methods=['POST'])
def blur():
    global ORDER_COUNTER

    form = BlurImagesForm()
    if not form.validate_on_submit():
        return f"Invalid input, {form.errors}", 400

    if not app.config['UPLOAD_FOLDER'].exists() or not app.config['UPLOAD_FOLDER'].is_dir():
        os.mkdir(app.config['UPLOAD_FOLDER'])

    user_email = form.email.data
    username = user_email.split('@')[0]
    user_dir = app.config['UPLOAD_FOLDER'] / username
    if user_dir.exists() and user_dir.is_dir():
        user_dir = app.config['UPLOAD_FOLDER'] / f'{random.randint(1, 10 ** 10)}_{username}'
    os.mkdir(user_dir)

    tasks = tuple()
    for index, file in enumerate(form.files.data):

        if file.filename == '':
            return jsonify({'Error': f'No selected file with index {index + 1}'}), 400

        filename = secure_filename(file.filename)
        file.save(user_dir / filename)

        tasks = (
            *tasks,
            blur_image_task.si(f'{user_dir}/{filename}')
        )

    task_group = group(tasks)

    archive_path = str(user_dir)

    task_pipe = chain(
        archive_files_task.si(archive_path, 'zip') |
        send_email_task.si(ORDER_COUNTER, user_email, archive_path + '.zip') |
        remove_files_task.si(archive_path)
    )
    result = chord(task_group)(task_pipe)

    ORDER_COUNTER = ORDER_COUNTER + 1
    return jsonify({'group_id': result.id}), 202


@app.route('/status/<group_id>', methods=['GET'])
def get_group_status(group_id):
    result = celery_app.GroupResult.restore(group_id)

    if result:
        status = {
            'group_id': group_id,
            'completed': f'{result.completed_count()} of {len(result)}',
            'tasks_statuses': [
                {'name': task.id, 'status': task.status.lower()}
                for task in result.children
            ]
        }

        return jsonify(status), 200
    else:
        return jsonify({'error': 'Invalid group_id'}), 404


@app.route('/subscribe', methods=['POST'])
def subscribe():
    form = SubscribeForm()
    if not form.validate_on_submit():
        return f"Invalid input, {form.errors}", 400

    subscribe_data = client.get('subscribes')

    if subscribe_data:

        subscribe_dict = loads(subscribe_data)
        subscribe_dict[form.email.data] = True
    else:
        subscribe_dict = {form.email.data: True}

    client.set('subscribes', dumps(subscribe_dict))

    return 'You have successfully subscribed to the newsletter!', 200


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    form = SubscribeForm()
    if not form.validate_on_submit():
        return f"Invalid input, {form.errors}", 400

    subscribe_data = client.get('subscribes')

    if subscribe_data:
        str_data = str(subscribe_data)
        subscribe_dict = loads(str_data)
        subscribe_dict[form.email.data] = False
    else:
        subscribe_dict = {form.email.data: False}

    client.set('subscribes', dumps(subscribe_dict))

    return 'You have successfully unsubscribed to the newsletter!', 200


if __name__ == '__main__':
    app.config["WTF_CSRF_ENABLED"] = False
    app.run(debug=True, port=8080)
