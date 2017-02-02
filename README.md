# pingo-survey-bot.py

Python3 script to reply to http://pingo.upb.de surveys, as many times as you like :)

It supports all survey types and is able to figure out the type by itself.

## Usage

Clone the repository and install the dependencies:

```bash
$ pip3 install requests recordclass PyYaml
```

Now you can run the script to set all options, they are stored in `prefs.yaml` by default.

## Options on running the script

```json
1: Text/TagCloud survey:                    shrek'd
2: Single/Multiple Choice survey (0-max):   1
3: Numeric survey:                          42
4: The amount of times to send:             25

5: Access number                            1001
6: Start sending!
7: Exit
```
