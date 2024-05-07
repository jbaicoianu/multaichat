import os
import time
import json
from multaichat.chat import ChatPersona

personas = None
personas_load_time = 0

default_model_name = None

def load():
    global personas
    global personas_load_time
    printed_msg = False
    if not personas:
        personas = {}
        print('Loading personas:')
        printed_msg = True
    for fname in os.listdir('personas'):
        if fname[-5:] == '.json':
            fullpath = 'personas/' + fname
            stat = os.stat(fullpath)
            if stat.st_mtime > personas_load_time:
                if not printed_msg:
                    print('Reloading personas:');
                    printed_msg = True
                with open(fullpath, encoding='utf-8') as f:
                    pcfg = json.loads(f.read())
                    if not 'model' in pcfg and default_model_name:
                        pcfg['model'] = default_model_name
                    print(pcfg)
                    persona = ChatPersona(**pcfg)
                    print(f' - {persona.icon} {persona.name}')
                    personas[persona.name] = persona

    personas_load_time = time.time()
    return personas

