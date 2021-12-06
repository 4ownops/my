import json
import yaml
from copy import deepcopy
from urllib.request import Request, urlopen
from datetime import datetime
from telegram.ext import Updater

class ConfigurationReader:
    def __init__(self, configuration_file: str) -> None:
        self._stream = open(configuration_file, 'r')
        self.configuration = yaml.safe_load(self._stream)
    
    def get_section(self, section_name: str) -> list:
        return deepcopy(self.configuration[section_name])

class Program:
    def __init__(self) -> None:
        self.zodiac_signs=['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        config = ConfigurationReader('config.yaml')
        self.bot_config = config.get_section('bot_config')

    def get_text(self, zodiac: str) -> str:
        post_fields={'query': zodiac, 'intro': 10, 'filter': 1}
        req = Request(self.bot_config['url'])
        jsondata = json.dumps(post_fields)
        jsondataasbytes = jsondata.encode('utf-8')
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Content-Length', len(jsondataasbytes))
        response = urlopen(req, jsondataasbytes)
        responsetext = (response.read().decode('unicode-escape'))
        datajs = json.loads(responsetext)
        return datajs['text']

    def send_message(self) -> None:
        updater = Updater(self.bot_config['token'])
        sender=updater.bot
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y")
        for zodiac_sign in self.zodiac_signs:
            raw_text = self.get_text(zodiac_sign)
            while 'единорог' in raw_text or 'лунная' in raw_text: # try to remove often expressions
                raw_text = self.get_text(zodiac_sign)
            copy_signs = deepcopy(self.zodiac_signs)
            copy_signs.remove(zodiac_sign)
            for copy_sign in copy_signs:
                if copy_sign in raw_text:
                    remove_text = copy_sign + ':'
                    print(remove_text)
                    raw_text.replace(remove_text, '')
            text = 'Гороскоп на '+dt_string
            text += ':\n'
            text += zodiac_sign + ": " + raw_text
            print(text)
            sender.send_message(chat_id=self.bot_config['channel_id'], text=text)

def lambda_handler(event, context):
    program = Program()
    program.send_message()