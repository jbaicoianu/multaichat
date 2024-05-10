import re
import regex
import datetime
import time
import json
import tty, termios
import sys
import torch

from pylatexenc.latex2text import LatexNodes2Text
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

latex_re = re.compile(r'\\\w+\{')

class ChatPersona:
    def __init__(self, name=None, personality_prompt=None, situational_prompt=None, initial_prompt=None, icon=None, role=None, generator=None, model=None, discord_key=None):
        self.name = name or "DefaultChatPersona"
        self.role = role or 'assistant'
        self.personality_prompt = personality_prompt or "You are a chat bot built using the StableLM Large Language Model."
        self.situational_prompt = situational_prompt or "You are currently having a conversation with a user. The user asks you questions, and you answer them to the best of your knowledge."
        self.initial_prompt = initial_prompt or "Hello. My name is DefaultChatPersona. I am here to help you. Say whatever is in your mind freely, our conversation will be kept in strict confidence. Memory contents will be wiped off after you leave.\n\nSo, tell me about your problems."
        self.icon = icon or '🤖'
        self.discord_key = discord_key or ''
        self.generator = generator
        self.model = model

    def toJSON(self):
        return {
            "name": self.name,
            "role": self.role,
            "personality_prompt": self.personality_prompt,
            "situational_prompt": self.situational_prompt,
            "initial_prompt": self.initial_prompt,
            "icon": self.icon,
            "model": self.model,
            }
    def save(self, path=None):
        if not path:
            path = 'personas/' + self.name + '.json'
        try:
            with open(path, 'w') as fd:
                fd.write(json.dumps(self.toJSON(), indent=2))
                return True
        except Exception as e:
            pass
        return False

    def get_initial_prompt(self):
        return '\n'.join([
            self.personality_prompt,
            self.situational_prompt,
            '',
        ])
    def get_temporal_prompt(self, ts=None):
        now = datetime.datetime.now()
        return 'Today is ' + now.strftime('%A, %B %d, %Y') + '. The time is ' + now.strftime('%H:%M:%S %Z') + '.\n'
    def get_greeting_prompt(self):
        return '\n'.join([
            '<|im_start|>system',
            self.personality_prompt,
            self.situational_prompt,
            self.get_temporal_prompt() + '<|im_end|>',
            '<|im_start|>user',
            'Generate a fun and unique greeting to get a conversation started. Let your real personality shine through!<|im_end|>',
            '<|im_start|>assistant',
            #'<message user="%s">' % self.name
            ])
    def get_tool_prompt(self):
        tools = [
                    {
                        "role": "function",
                        "content": {
                            "name": "TestFunction",
                            "description": "This function is used to perform basic math",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "equation": {
                                        "type": "string",
                                        "description": "The math equation to solve"
                                    }
                                }
                            }
                        }
                    }
                ]
        return f'You have access to the following functions. Use them if required - {str(tools)}'

    def get_system_prompt(self):
        return {
                'role': 'system',
                'content': '\n'.join([
                    self.personality_prompt,
                    self.situational_prompt,
                    self.get_temporal_prompt(),
                    self.get_tool_prompt()
                    ])
                }

    def create_message(self, content, generating=False):
        #print(content)
        return ChatMessage(self, content, generating)

    def on_join(self, conversation):
        msgs = [
                #self.get_system_prompt(),
                {'role': 'system', 'content': 'Generate a short but fun and unique greeting to get a conversation started. Let your real personality shine through!'}
                #{'role': 'user', 'content': 'Generate a short but fun and unique greeting to get a conversation started. Let your real personality shine through!'}
               ]
        greeting = self.generate(msgs)
        conversation.add(ChatMessage(self, greeting))
        return greeting

    def unload(self):
        if (self.generator):
            print('unloading...')
            self.generator.unload()
            print('done')

    def generate(self, prompt):
        if not self.generator and self.model:
            self.generator = ChatGenerator(self.model)
        return self.generator.generate(prompt)


class ChatPlugin:
    def __init__(self):
        pass

class ChatPluginEcho:
    def __init__(self):
        self.instruction = '!echo <string> : echoes the string'
    def exec(self, payload):
        return 'ECHO! ' + payload

class ChatPluginSearch:
    def __init__(self):
        self.instruction = '!search <query> : search Google for web results'
    def exec(self, payload):
        print('BEEP BOOP, SEARCHING FOR DATA: %s' % payload)
        return ['hey, got something', 'yeah, multiple results!', 'here they are']

class ChatPluginWikipedia:
    def __init__(self):
        self.instruction = '!wiki <subject> : look something up on Wikipedia'
    def exec(self, payload):
        print('WIKIPEDIA LOOKUP: %s' % payload)
        return '{here is a wiki page about %s}' % (payload)

class ChatMessage:
    def __init__(self, user, content, generating=False):
        self.ts = time.time()
        self.user = user
        self.content = content.strip()
        self.generating = generating
    def get_string(self, max_len=None):
        #return '[%s] <%s> %s\n' % (datetime.datetime.fromtimestamp(self.ts).strftime('%H:%M:%S'), self.user.name, self.content.strip())
        if not max_len:
            max_len = len(self.content)
        #print(max_len, len(self.content))
        #string = '===== %s =====\n%s' % (self.user.name, self.content.strip())
        string = '<|im_start|>%s\n%s' % (self.user.role, self.content.strip())
        if not self.generating:
            #string += '\n===== end message =====\n'
            #string += '\n</message>\n'
            #string += '\n####\n'
            string += '<|im_end|>\n'
        return string
    def wrap_lines(self, width=76):
        wrappedlines = []
        content = self.content

        if latex_re.search(content):
            content = LatexNodes2Text().latex_to_text(content)

        lines = content.split('\n')
        for line in lines:
            words = line.split(' ')
            newline = ''
            for word in words:
                if len(newline) + len(word) + 1 > width:
                    wrappedlines.append(newline)
                    newline = word
                elif newline == '':
                    newline = word
                else:
                    newline += ' ' + word
            if len(newline) > 0:
                wrappedlines.append(newline)
        if len(wrappedlines) == 0:
            wrappedlines.append('')
        return wrappedlines

    def update(self, newtxt):
        old_lines = self.wrap_lines()
        self.content = newtxt
        print('\033[%dF' % (len(old_lines) + 2), end='')
        self.display()

    def append(self, newtxt):
        self.update(self.content + newtxt)

    def finish(self):
        if self.generating:
            self.generating = false

    def display(self, pos=None):
        lines = self.content.split('\n') #self.wrap_lines()
        print('\033[1G\033[38;5;12m       ╭ \033[38;5;15m\033[K')
        firstline = True
        for line in lines:
            if firstline:
                unicode_combiners = len(regex.findall(r'\w\p{M}*', self.user.icon))
                print('\033[1G %s%s \033[38;5;12m┤ \033[38;5;15m%s\033[K' % (' ' * (4 - len(self.user.icon) + unicode_combiners), self.user.icon, line))
                firstline = False
            else:
                print('\033[1G       \033[38;5;12m│ \033[38;5;15m%s\033[K' % (line))
        print('\033[38;5;12m       ╰ \033[38;5;15m\033[K')
    def input(self):
        self.content = ''
        self.display()
        print('\033[2F\033[10G', end='')
        input = ''
        while not input:
            #print('\033[38;5;10m %s ┘ \033[38;5;15m'% (user_persona.icon), end='')
            #input = sys.stdin.readline()
            ch = '' 
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            linecount = 1
            try:
                while ch != '\n' and ch != 0:
                    tty.setraw(fd)
                    ch = sys.stdin.read(1)
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    code = ord(ch)
                    if code == 3 or code == 4:
                        input = self.content = ''
                        break
                    elif code == 13:
                        if len(input) > 0:
                            wrappedlines = self.wrap_lines()
                            print('\033[%dF' % (len(wrappedlines)), end='')
                            self.display()
                            break
                    elif code == 127:
                        if len(input) > 0:
                            input = input[0:-1]
                    else:
                        #input += str(ord(ch))
                        input += ch[0]
                    self.content = input
                    wrappedlines = self.wrap_lines()
                    if len(wrappedlines) > linecount:
                        print()
                        linecount = len(wrappedlines)
                    print('\033[%dF' % (linecount), end='')
                    self.display()
                    offset = 2
                    if len(wrappedlines) < linecount:
                        for i in range(len(wrappedlines), linecount):
                            print('\033[K')
                            offset += 1
                        linecount = len(wrappedlines)
                    print('\033[%dF\033[%dG' % (offset, 10 + len(wrappedlines[-1])), end='')

            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            if input == '':
                print('bye')
                print()
                sys.exit()
            else:
                input = input.strip()
        #self.content = input

        return input


class ChatConversation:
    def __init__(self, context_length=2048, gen_length=768):
        self.context_length = context_length
        self.gen_length = gen_length
        self.plugins = []
        self.messages = []

    def add(self, content):
        #print('add message', content.get_string())
        self.messages.append(content)

    def summarize(self):
        prompt = '' 
        for i in range(len(self.messages)-1, -1, -1):
            maxlen = self.context_length - self.gen_length - len(prompt)
            msgstr = self.messages[i].get_string()
            if len(msgstr) + len(prompt) > self.context_length - self.gen_length:
                break
            if len(prompt) == 0:
                prompt = msgstr
            else:
                prompt = msgstr + prompt
        #print(prompt + '\n\n\n\n\n\n\n')
        return prompt

    def add_plugin(self, plugin):
        self.plugins.append(plugin)

    def summarize_plugins(self):
        summary = ''
        if len(self.plugins) > 0:
            summary = 'I have access to the following special commands, and can use them at any time:\n\n'

            for plugin in self.plugins:
                summary += plugin.instruction + '\n'
            summary += '\n'
        return summary

    def get_temporal_prompt(self):
        now = datetime.datetime.now()
        return 'Today is ' + now.strftime('%A, %B %d, %Y') + '. The time is ' + now.strftime('%H:%M:%S %Z') + '.'

    def get_next_prompt(self, user):
        prompt = '<|im_start|>system\n'
        prompt += user.get_initial_prompt()
        prompt += self.get_temporal_prompt()
        #prompt += self.summarize_plugins()
        prompt += '<|im_end|>\n'
        prompt += self.summarize()
        if not self.messages[-1].generating:
            #prompt += '===== ' + user.name + '=='
            #prompt += '<message user="' + user.name + '">\n'
            prompt += '<|im_start|>%s\n' % user.role
        #print(prompt)
        return prompt
    def get_lines(self):
        msgs = []
        for msg in self.messages:
            msgs.append({
                'role': msg.user.role,
                'content': msg.content
            })
        return msgs
    def clear(self):
        self.messages = []

class ChatGenerator:
    def __init__(self, model_name):
        self.use_pipeline = True
        self.load(model_name)
    def load(self, model_name):
        if self.use_pipeline:
            #self.pipe = pipeline('text-generation', model_name, device=0)
            self.pipe = get_pipeline(model_name)
        else:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
              model_name,
              torch_dtype="auto",
            )
            model.cuda()
            self.model = model
            self.tokenizer = tokenizer
            return model, tokenizer

    def generate(self, messages):
        print('eh', messages)
        '''inputs = self.tokenizer(messages, return_tensors="pt").to(generator.device)
        tokens = self.model.generate(
          **inputs,
          max_new_tokens=256,
          temperature=temperature,
          top_p=top_p,
          do_sample=True,
        )
        prompt_results = (self.tokenizer.decode(tokens[0], skip_special_tokens=True))
        '''
        if self.use_pipeline:
            print('generating....')
            #print(messages)
            result = self.pipe(messages, max_new_tokens=1024, temperature=0.75)
            print(result)
            return result[0]['generated_text'][-1]['content']
        else:
            tokenized_chat = self.tokenizer.apply_chat_template(messages, tokenize=True, return_tensors="pt", add_generation_prompt=True)
            tokenized_chat_str = self.tokenizer.decode(tokenized_chat[0])
            nt = tokenized_chat.to('cuda')
            output = self.model.generate(nt, max_new_tokens=512, temperature=0.75)
            result = self.tokenizer.decode(output[0])
            #print('EEEEEEEEEEEEE')
            #print(result)

            return result[len(tokenized_chat_str):]
    async def generate_async(self, messages):
        result = self.pipe(messages, msx_new_tokens=16)[0]['generated_text'][-1]


def test_callback(pipe, step_index, timestep, callback_kwargs, model_kwargs):
    print('huh?')

pipelines = {}
def get_pipeline(model_name):
    if not model_name in pipelines:
        pipelines[model_name] = pipeline('text-generation', model_name, device=0, torch_dtype=torch.float16)
        #pipelines[model_name] = pipeline('text-generation', model_name, device='cpu')
    return pipelines[model_name]

def load_config(path):
    try:
        with open(path) as f:
            cfg = json.load(f)
            return cfg
    except FileNotFoundError:
        return {}
