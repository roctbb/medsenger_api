"""
medsenger_api.
Python SDK for Medsenger.AI
"""

__version__ = "0.1.18"
__author__ = 'Rostislav Borodin'
__credits__ = 'TelePat LLC'

import base64
import uuid
from copy import copy
import requests
from datetime import datetime


class AgentApiClient:
    def __init__(self, api_key, host="https://medsenger.ru", agent_id=None, debug=False):
        self.host = host
        self.api_key = api_key
        self.debug = debug
        self.agent_id = agent_id

    def __gts__(self):
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S - ")

    def __send_request__(self, page, json_params):
        target = self.host + page
        try:
            if self.debug:
                if len(str(json_params)) > 400:
                    print(self.__gts__(), "Sending request to {} with params {}".format(target, str(json_params)[:200]))
                else:
                    print(self.__gts__(), "Sending request to {} with params {}".format(target, json_params))

            result = requests.post(target, json=json_params)

            if result.status_code != 200:
                raise Exception('status code - {}'.format(result.status_code))

            if self.debug:
                if len(result.text) > 400:
                    print(self.__gts__(), "Result - {}...".format(result.text[:200]))
                else:
                    print(self.__gts__(), "Result - {}".format(result.text))

            try:
                return result.json()
            except:
                return result.text
        except Exception as e:
            print(self.__gts__(), "Error in {} - {}".format(target, e))
            return None

    def get_categories(self):
        data = {
            "api_key": self.api_key,
        }

        return self.__send_request__('/api/agents/records/categories', data) or []

    def get_available_categories(self, contract_id):
        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
        }

        return self.__send_request__('/api/agents/records/available_categories', data) or []

    def get_patient_info(self, contract_id):
        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
        }

        return self.__send_request__('/api/agents/patient/info', data) or {
            'name': '',
            'sex': '',
            'birthday': ''
        }

    def get_clinics_info(self):
        data = {
            "api_key": self.api_key,
        }

        return self.__send_request__('/api/agents/clinics', data) or []

    def get_records(self, contract_id, category_name=None, time_from=None, time_to=None, limit=None, offset=None, group=False, return_count=False, inner_list=False):

        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
        }

        if category_name:
            data["category_name"] = category_name

        if limit:
            data['limit'] = limit
        if offset:
            data['offset'] = offset
        if time_from:
            data['from'] = time_from
        if time_to:
            data['to'] = time_to
        if group:
            data['last_group'] = True
        if return_count:
            data['return_count'] = True

        if not category_name or ',' in category_name or inner_list:
            url = "/api/agents/records/get/all"
        else:
            url = "/api/agents/records/get"

        return self.__send_request__(url, data) or None

    def add_hooks(self, contract_id, names):
        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
            "categories": names
        }

        return self.__send_request__("/api/agents/hooks/add", data)

    def remove_hooks(self, contract_id, names):
        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
            "categories": names
        }

        return self.__send_request__("/api/agents/hooks/remove", data)

    def send_addition(self, contract_id, record_id, addition):
        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
            "record_id": record_id,
            "addition": addition,
        }

        return self.__send_request__('/api/agents/records/addition', data)

    def add_record(self, contract_id, category_name, value, record_time=None, params=None, files=None):
        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
            "category_name": category_name,
            "value": value,
        }

        if params:
            data['params'] = params

        if record_time:
            data['time'] = record_time

        if files:
            data['files'] = files

        return self.__send_request__('/api/agents/records/add', data)

    def add_records(self, contract_id, values, record_time=None, params={}):
        data = {"contract_id": contract_id, "api_key": self.api_key, 'values': []}

        for record in values:
            record_params = copy(params)
            files = []

            if isinstance(record, (list, tuple)):
                if len(record) == 2:
                    category_name, value = record
                else:
                    category_name, value, custom_params = record
                    record_params.update(custom_params)
            elif isinstance(record, dict):
                category_name = record['category_name']
                value = record['value']
                custom_params = record.get('params', {})
                record_params.update(custom_params)
                files = record.get('files', [])

            data['values'].append(
                {"category_name": category_name, "value": value, "params": record_params, "files": files, "time": record_time})

        return self.__send_request__('/api/agents/records/add', data)

    def send_message(self, contract_id, text, action_link=None, action_name=None, action_onetime=True,
                     only_doctor=False,
                     only_patient=False, action_deadline=None, is_urgent=False, need_answer=False,
                     attachments=None, action_big=True, send_from=None, forward_to_doctor=True):
        message = {
            "text": text,
            "forward_to_doctor": forward_to_doctor
        }

        if action_link:
            message['action_link'] = action_link

        if send_from:
            message['send_from'] = send_from

        if action_name:
            message['action_name'] = action_name

        if action_onetime:
            message['action_onetime'] = action_onetime

        if action_big:
            message['action_big'] = action_big

        if only_doctor:
            message['only_doctor'] = only_doctor

        if need_answer:
            message['need_answer'] = need_answer

        if only_patient:
            message['only_patient'] = only_patient

        if action_deadline:
            message['action_deadline'] = action_deadline

        if is_urgent:
            message['is_urgent'] = is_urgent

        if attachments:
            message['attachments'] = []

            for attachment in attachments:
                if isinstance(attachment, (list, tuple)):
                    message['attachments'].append({
                        "name": attachment[0],
                        "type": attachment[1],
                        "base64": attachment[2],
                    })
                elif isinstance(attachment, (dict)):
                    message['attachments'].append(attachment)

        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
            "message": message
        }

        return self.__send_request__('/api/agents/message', data)

    def finish_task(self, contract_id, task_id):
        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
            "task_id": task_id,
        }

        return self.__send_request__('/api/agents/tasks/done', data)

    def delete_task(self, contract_id, task_id):
        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
            "task_id": task_id,
        }

        return self.__send_request__('/api/agents/tasks/delete', data)

    def add_task(self, contract_id, text, target_number=1, date=None, important=False, action_link=None):
        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
            "text": text,
            "number": target_number,
            "important": important
        }

        if date:
            data['date'] = date

        if action_link:
            data['action_link'] = action_link

        return self.__send_request__('/api/agents/tasks/add', data)

    def send_order(self, contract_id, order, receiver_id=None, params=None):
        data = {
            "contract_id": contract_id,
            "api_key": self.api_key,
            "order": order,
        }

        if receiver_id:
            data['receiver_id'] = receiver_id

        if params:
            data['params'] = params

        return self.__send_request__('/api/agents/order', data)

    def get_agent_token(self, contract_id):
        data = {
            "api_key": self.api_key,
            "contract_id": contract_id
        }

        return self.__send_request__('/api/agents/token', data)

    def ajax_url(self, action, contract_id, agent_token):
        # TODO fix
        return self.host.replace('8001',
                                 '8000') + "/api/client/agents/{agent_id}/?action={action}&contract_id={contract_id}&agent_token={agent_token}".format(
            agent_id=self.agent_id, action=action, contract_id=contract_id, agent_token=agent_token
        )

    def download_file(self, *args, **kwargs):
        return self.get_file(*args, **kwargs)

    def download_attachment(self, *args, **kwargs):
        return self.get_attachment(*args, **kwargs)

    def download_image(self, *args, **kwargs):
        return self.get_image(*args, **kwargs)

    def get_file(self, contract_id, file_id):
        data = {
            "api_key": self.api_key,
            "file_id": file_id,
            "contract_id": contract_id
        }

        return self.__send_request__('/api/agents/records/file', data)

    def get_attachment(self, attachment_id):
        data = {
            "api_key": self.api_key,
            "attachment_id": attachment_id
        }

        return self.__send_request__('/api/agents/attachment', data)

    def get_image(self, image_id, size):
        data = {
            "api_key": self.api_key,
            "attachment_id": image_id,
            "size": size
        }

        return self.__send_request__('/api/agents/image', data)

    def update_cache(self, contract_id):
        data = {
            "api_key": self.api_key,
            "contract_id": contract_id
        }

        return self.__send_request__('/api/agents/cache', data)

    def set_info_materials(self, contract_id, materials):
        data = {
            "api_key": self.api_key,
            "contract_id": contract_id,
            "info_materials": materials
        }

        return self.__send_request__('/api/agents/info_materials/set', data)


def prepare_binary(name, data):
    import magic
    type = magic.from_buffer(data, mime=True)

    return {
        "name": name,
        "base64": base64.b64encode(data).decode('utf-8'),
        "type": type
    }


def prepare_file(filename):
    import magic
    import os

    type = magic.from_file(filename, mime=True)

    with open(filename, 'rb') as file:
        answer = {
            "name": filename.split(os.sep)[-1],
            "base64": base64.b64encode(file.read()).decode('utf-8'),
            "type": type
        }

    return answer
