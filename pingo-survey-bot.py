# -*- coding: utf-8 -*-

import os
import re
import sys
import yaml
from concurrent import futures

import requests
from recordclass import recordclass

# all tuple values are integers
Config = recordclass('Config', 'session text choice amount numeric')
prefs_file = "prefs.yaml"


def set_session_number(c):
    """Print the current session number and change it to the user input"""
    print('Current session number: {}'.format(c.session))
    print('New: ', end='')
    new = input('')
    if new.isnumeric():
        c.session = int(new)
        persist_config_to_filesystem(c)
    else:
        print('Not an integer! Session number not changed!\n')


def set_text_to_send(c):
    """Print the current text and change it to the user input"""
    print('Current text which will be sent: {}'.format(c.text))
    print('New: ', end='')
    t = input('')
    if t is "":
        print('Empty text not permitted!\n')
    else:
        c.text = t
        persist_config_to_filesystem(c)


def set_multiple_choice_option(c):
    print('Current single choice (from 0 which corresponds to A): {}'
          .format(c.choice))
    print('New: ', end='')
    new = input('')
    if new.isnumeric():
        c.choice = int(new)
        persist_config_to_filesystem(c)
    else:
        print('Not an integer! Multiple choice option not changed!\n')


def set_send_amount(c):
    """Print the current packet send amount and change it to the user input"""
    print('Current send amount: {}'.format(c.amount))
    print('New: ', end='')
    new = input('')
    if new.isnumeric():
        c.amount = int(new)
        persist_config_to_filesystem(c)
    else:
        print('Not an integer! Send amount not changed!\n')


def set_numeric_value(c):
    print('Current numeric value to send: {}'.format(c.numeric))
    print('New: ', end='')
    new = input('')
    if new.isnumeric():
        c.numeric = int(new)
        persist_config_to_filesystem(c)
    else:
        print('Not an integer! Numeric value not changed!\n')


def get_default_config():
    return Config(session=1001,
                  text="shrek'd",
                  choice=1,
                  amount=25,
                  numeric=42)


def persist_config_to_filesystem(c):
    with open(prefs_file, "w") as f:
        f.write(yaml.dump({
            "sessionId": c.session,
            "sendAmount": c.amount,
            "valueText": c.text,
            "valueSingleChoice": c.choice,
            "valueNumeric": c.numeric}))


def extract_config_from_yaml(string):
    y = yaml.load(string)

    def get_yaml_def(key, d):
        try:
            return y[key]
        except KeyError:
            print("keyerror on: {}".format(key))
            return d

    default = get_default_config()
    return Config(session=get_yaml_def("sessionId", default.session),
                  text=get_yaml_def("valueText", default.text),
                  choice=get_yaml_def("valueSingleChoice", default.choice),
                  amount=get_yaml_def("sendAmount", default.amount),
                  numeric=get_yaml_def("valueNumeric", default.numeric))


def prepare_settings():
    """Return Config object from prefs file

    If the files are not existing, they will be created and pre-initialized, but
    if the existing config file contains invalid input, we terminate here.
    """
    if not os.path.exists(prefs_file):
        persist_config_to_filesystem(get_default_config())
    with open(prefs_file) as f:
        return extract_config_from_yaml(f.read())


def generate_fake_headers(c):
    return {
        'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Host': 'pingo.upb.de',
        'Referer': 'http://pingo.upb.de/{}'.format(c.session),
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:25.0) Gecko/20100101 '
            'Firefox/25.0',
        'Content-Type': 'application/x-www-form-urlencoded'}


def get_basic_payload(auth_token, pid):
    return {'utf8': '✓',
            'authenticity_token': auth_token,
            'id': pid,
            'commit': 'Vote!'}


def send(c):
    """Initiate the network requests thread to send the options"""
    r = requests.get('http://pingo.upb.de/{}'.format(c.session))
    if 'id="not_running"' in r.text or 'data-dismiss="alert">' in r.text:
        print('Survey with ID: {id} is not running?\n'
              .format(id=c.session))
        return
    authenticity_token = re.findall('(?<=content=").*(?=" name)', r.text)[1]
    pid = re.findall(
        '(?<=<input id="id" name="id" type="hidden" value=").*(?=")', r.text)[0]
    print('  authenticity_token: {}\n  id: {}'.format(authenticity_token, pid))
    payload = get_basic_payload(authenticity_token, pid)

    is_numeric = 'required="required" step="0.00001"' in r.text
    if is_numeric:
        payload['option'] = c.numeric
        print(" sending to a numeric survey...", end='')
    else:
        # need to fetch option[] ids from the radio values for POSTing
        o = re.findall('(?<=name="option" type="radio" value=").*(?=")', r.text)
        if len(o) != 0:
            payload['option[]'] = o[c.choice]
            print(" sending to single/multiple choice survey...", end='')
        else:
            payload['option[]'] = c.text
            print("  sending to a text/tagcloud survey...", end='')

    def post(i):
        """Post the vote packet and print the passed ID once done"""
        requests.post('http://pingo.upb.de/vote',
                      headers=generate_fake_headers(c), data=payload,
                      stream=True)

    print('  ', end='')
    with futures.ThreadPoolExecutor(max_workers=100) as executor:
        executor.map(post, range(c.amount))
    print("done!\n")


def print_options(c):
    def l(i):
        return i.ljust(40)

    print('1 - {} {}'.format(l('Text/TagCloud survey: '), c.text))
    print('2 - {} {}'.format(l('Single/Multiple Choice survey (0-max):'),
        c.choice))
    print('3 - {} {}'.format(l('Numeric survey: '), c.numeric))
    print('4 - {} {}'.format(l('The amount of times to send: '), c.amount))
    print('\n5 - {} {}'.format(l('Access number'), c.session))
    print('6 - Start sending!')
    print('7 - Exit')


if __name__ == '__main__':
    s = prepare_settings()
    print_options(s)
    while True:
        try:
            choice = input('\nChoice (1-7): ')
        except KeyboardInterrupt:
            sys.exit(0)
        print()
        if choice == '1':
            set_text_to_send(s)
            print_options(s)
        elif choice == '2':
            set_multiple_choice_option(s)
            print_options(s)
        elif choice == '3':
            set_numeric_value(s)
            print_options(s)
        elif choice == '4':
            set_send_amount(s)
            print_options(s)
        elif choice == '5':
            set_session_number(s)
            print_options(s)
        elif choice == '6':
            send(s)
            print_options(s)
        elif choice == '7':
            sys.exit(0)
