import logging
import os
import datetime
import socket
import json
import time
import re

## GLOBAL DEBUG FLAG ##
debug_mode = False
#######################

# logging configuration
def configure_logger():
    logfile_path = 'logs'
    if not os.path.exists(logfile_path):
        os.makedirs(logfile_path)
    logfile_timestamp = int(datetime.datetime.now().timestamp())
    logfile_name = f'{os.path.splitext(os.path.basename(__file__))[0]}_{logfile_timestamp}.log'
    logging.basicConfig(
        filename=f'{logfile_path}/{logfile_name}',
        encoding='utf-8',
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %H:%M:%S%z'
        )
    logging.info(f'START')

def prettyPrint(msg):
    print(f'[>] {msg}')
    logging.info(msg)

def stayAlive(socket, action):
    if action == 'jiggle':
        sendMsg(socket, '>')
        time.sleep(1)
        sendMsg(socket, '<')

def readMsg(socket):
    message = b''
    while True:
        data = socket.recv(1)
        if not data:
            pass
        if data == b'\n':
            return message
        message += data

def sendMsg(socket, msg):
    print_exclusions = [
        '>',
        '<',
        'm 1',
        'm 3',
        'm 7',
        'm 9',
        'lie',
        'sit',
        'stand'
    ]
    if type(msg) == str:
        if msg not in print_exclusions:
            print(f'[SEND] {msg}')
        logging.info(msg)
        msg = msg.encode('iso-8859-1')
    socket.send(msg + b'\n')

def parseWhispers(socket, string):
    quitting = False

    whisperer = re.search(r'\<name[^\>]+\>([^\<]+)\<\/name\>', string)
    whisperer = whisperer.group(1)
    message = re.search(r'\"([^\"]+)\"', string)
    message = message.group(1)

    formatted = f'{whisperer} (whisper) {message}'
    prettyPrint(formatted)

    if whisperer == owner:
        cmd = re.match('cmd\:(.*)', message)
        if cmd:
            cmd_string = cmd.group(1)
            if cmd_string == 'quit':
                sendMsg(socket, f'\"Disconnecting...')
                time.sleep(5)
                quitting = True
            if quitting:
                sendMsg(socket, cmd_string)
                socket.close()
            else:
                sendMsg(socket, cmd_string)

        move = re.match('move\:(.*)', message)
        if move:
            move_string = move.group(1).split(',')
            for m in move_string:
                sendMsg(socket, m)
                time.sleep(0.75)
        
        say = re.match('say:(.*)', message)
        if say:
            say_string = say.group(1)
            say_string = f'\"{say_string}'
            sendMsg(socket, say_string)

    return

def parseSaying(socket, string):
    saying = re.search(r'\(\<name\sshortname\=\'[^\']+\'\>([^\<]+)\<\/name\>\:\s(.*)', string)
    sayer = saying.group(1)
    said = saying.group(2)
    
    formatted = f'{sayer}: {said}'
    prettyPrint(formatted)

def parseEmotes(socket, string):
    emote = re.search(r'\(\<font\scolor\=\'emote\'\>\<name\sshortname\=\'[^\']+\'\>([^\<]+)\<\/name\>\s(.*)\<\/font\>', string)
    emoter = emote.group(1)
    emoted = emote.group(2)
    
    formatted = f'{emoter} {emoted}'
    prettyPrint(formatted)

def removeTags(string):
    tag_re = re.compile(r'<[^>]+>')
    cleaned_string = tag_re.sub('', string)
    return cleaned_string

def removeParen(string):
    paren_re = re.compile(r'\(')
    cleaned_string = paren_re.sub('', string)
    return cleaned_string

def parseFurc(socket, msg):
    if msg == 'Dragonroar':
        sendMsg(socket, f'account {email} {character} {password}')
        sendMsg(socket, f'color {colors}')
        sendMsg(socket, f'desc {desc}')

    if msg == '&&&&&&&&&&&&&':
        sendMsg(socket, 'vascodagama')

    # SUMMONING - would need to figure out to format the owner name appropriately; this could also be hardcoded.
    # summoned = re.compile(r'\(<font color=\'query\'><name shortname=\'owner_name\'>owner_name<\/name> asks you to join their company.*')
    # if summoned.match(msg):
    #    sendMsg(socket, 'join')

    load_dream = re.compile(r'^]q')
    if load_dream.match(msg):
        sendMsg(socket, 'vascodagama')

    whispers = re.compile(r'\(<font color=\'whisper\'>')
    if whispers.match(msg):
        parseWhispers(socket, msg)

    emotes = re.compile(r'\(<font color=\'emote\'>')
    if emotes.match(msg):
        parseEmotes(socket, msg)

    saying = re.compile(r'\(\<name\sshortname\=\'[^\']+\'\>[^\<]+\<\/name\>\:\s(.*)')
    if saying.match(msg):
        parseSaying(socket, msg)


configure_logger()

# load configuration
conf = open('bot.conf', "r")
conf = json.load(conf)
if debug_mode:
    logging.debug(conf)

# global declarations
hostname = conf['connection'][0]['server']
port = conf['connection'][0]['port']
app_name = os.path.splitext(os.path.basename(__file__))[0]
app_vers = '0.6.0-alpha'

# account info
email = conf['account'][0]['email']
character = conf['account'][0]['character']
password = conf['account'][0]['password']
colors = conf['account'][0]['colors']
desc = conf['account'][0]['desc']
owner = conf['account'][0]['owner']
# append desc with script info
desc = desc + f' [{app_name} {app_vers}]'

# socket declarations
furc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    furc.connect((hostname, port))
    connected = True
    logging.info(f'Connected to {hostname}:{port}')
except:
    logging.error(f'Failed connection to {hostname}:{port}')

t0 = time.time()
while furc._closed == False:
    t1 = time.time()
    if (t1 - t0) >= 300.0:
        stayAlive(furc, 'jiggle')
        t0 = t1
    try:
        msg = readMsg(furc).decode('iso-8859-1')
        if debug_mode:
            print(f'[>] {msg}')
        parseFurc(furc, msg)
    except TimeoutError:
        furc.close()
        logging.warning(f'Connection has timed out.')

if furc._closed == True:
    logging.info(f'Connection has closed.')