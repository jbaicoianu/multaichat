from typing import Tuple
import os
import sys
import fire
import discord
import requests
import io
import json
from PIL import Image

from multaichat import ChatPersona, ChatConversation, ChatGenerator, load_config
from clip_interrogator import Config, Interrogator

cfg = load_config('config/multaichat.json')

def load_personas(model_name):
    personas = {}
    print('Loading personas:')
    for fname in os.listdir('personas'):
        if fname[-5:] == '.json':
            with open('personas/' + fname, encoding='utf-8') as f:
                pcfg = json.loads(f.read())
                if not 'model' in pcfg:
                    pcfg['model'] = model_name
                persona = ChatPersona(**pcfg)
                print(f' - {persona.icon} {persona.name}')
                personas[persona.name] = persona
    return personas

def main(
    model_name: str = 'stabilityai/stablelm-2-zephyr-1_6b',
    temperature: float = 0.95,
    top_p: float = 0.95,
    max_seq_len: int = 2048,
    max_reply_len: int = 1,
    active_persona='UnstableChat',
):

    personas = load_personas(model_name)

    persona = personas[active_persona]

    user_persona = personas['User']

    intents = discord.Intents(messages=True, message_content=True, guilds=True, typing=True)
    discord_client = discord.Client(intents=intents)

    convo = ChatConversation(max_seq_len, max_reply_len)

    #clip_interrogator = Interrogator(Config(clip_model_name="ViT-L-14/openai"))
    clip_interrogator = Interrogator(Config(clip_model_name="ViT-H-14/laion2b_s32b_b79k"))

    people = {}

    @discord_client.event
    async def on_ready():
        print(f'{discord_client.user} has connected to Discord!', persona)
        greeting = persona.on_join(convo)
        channel = discord_client.get_channel(cfg['discord']['channels'][0])
        chunks = split_string_into_chunks(greeting)
        for guild in discord_client.guilds:
            await guild.me.edit(nick=persona.name)
        for chunk in chunks:
            await channel.send(chunk)

    @discord_client.event
    async def on_message(message):
        # Check if the message was sent by a user, and not the bot itself
        if message.author == discord_client.user:
            return
        nonlocal active_persona
        nonlocal persona

        username = message.author.display_name
        channel = message.channel

        if not username in people:
            people[username] = ChatPersona(name=username, role='user', icon='🧍')

        user_persona = people[username]
        #print('MY PERSONA??', active_persona)
        #persona = personas[active_persona]


        if len(message.attachments) > 0:
            print('message had attachments', message.attachments)
            await channel.send('Ah, an image! Let\'s take a look...');
            persona.unload()
            for attachment in message.attachments:
                if '.png' in attachment.filename or '.jpg' in attachment.filename:
                    #await channel.send('oh wow, an image! Lemme check this out...' + attachment.filename)
                    async with channel.typing():
                        #urllib.request.urlopen(attachment.url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'})
                        response = requests.get(attachment.url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'})
                        image = Image.open(io.BytesIO(response.content)).convert('RGB')
                        text = clip_interrogator.interrogate(image)
                        convo.add(user_persona.create_message('Posted an image: %s - %s' % (attachment.filename, text)))
                        await channel.send('I see ' + text)

        if len(message.content) > 0:
            newmsg = people[username].create_message(message.content)
            convo.add(newmsg)
            newmsg.display()

            generate_response = True

            if message.content[0] == '!':
                cargs = message.content[1:].split(' ')
                if cargs[0] == 'p' or cargs[0] == 'prompt':
                    generate_response = False
                    #print('==== begin prompt ======')
                    #print(convo.get_next_prompt(persona))
                    #print('====  end prompt  ======')
                    await channel.send('Next prompt: ```' + convo.get_next_prompt(persona) + '```')
                if cargs[0] == 't':
                    generate_response = False
                    if len(cargs) > 1:
                        nonlocal temperature
                        temperature = float(cargs[1])
                        await channel.send(f'Temperature set to {temperature}')
                    else:
                        await channel.send(f'Temperature is {temperature}')
                if cargs[0] == 's':
                    generate_response = False
                    if len(cargs) > 1:
                        if cargs[1] in personas:
                            active_persona = cargs[1]
                            persona = personas[active_persona]
                            await message.guild.me.edit(nick=persona.name)
                            await channel.send(f'Set persona to `{persona.name}`')
                    else:
                        print('Current persona is', persona.name)
                        response = f'Current persona is {persona.name}\nAvailable personas are:\n\nn'
                        await channel.send(response)
                        for pname in personas:
                            p = personas[pname]
                            response = f'**{p.icon} {p.name}**\n{p.personality_prompt}\n\n'
                            await channel.send(response)


                        #print(response)
                        await channel.send('Use `!s <name>` to select a new persona')
                if cargs[0] == 'c' or cargs[0] == 'clear':
                    generate_response = False
                    convo.clear()
                    await channel.send('Ok, resetting conversation history')

                #if cargs[0] == 'peek':
                #    await channel.send(f'Last response: ```{lastresponse}```')
                

            if generate_response:
                async with channel.typing():
                    try:
                        '''
                        message_complete = False
                        message_start = None
                        message = None
                        while not message_complete:
                            fullprompt = convo.get_next_prompt(persona)
                            #print(fullprompt + '\n\n\n\n\n\n\n')
                            prompts = [
                                fullprompt,
                            ]

                            ### BEGIN GENERATOR ABSTRACT

                            # TODO - run this in a thread
                            #results = generator.generate(
                            #    prompts, max_gen_len=max_reply_len, temperature=temperature, top_p=top_p
                            #)
                            #result = results[0]
                            inputs = tokenizer(fullprompt, return_tensors="pt").to(generator.device)
                            tokens = generator.generate(
                              **inputs,
                              max_new_tokens=256,
                              temperature=0.70,
                              top_p=0.95,
                              do_sample=True,
                            )
                            result = (tokenizer.decode(tokens[0], skip_special_tokens=True))
                            if result:
                                #fullprompt = convo.get_next_prompt(persona)
                                #sep_start = '===== %s =====\n' % persona.name
                                #sep_end = '\n=====' #end message ====='
                                #sep_start = '<message user="%s">\n' % persona.name
                                #sep_end = '\n</message>'
                                sep_start = '<|im_start|>%s\n' % persona.role
                                sep_end = '<|im_end|>\n'
                                message_new = result[len(fullprompt):]
                                ### END GENERATOR ABSTRACT
                                start = 0
                                if not message:
                                    message_start = result.rfind('\n', 0, len(fullprompt))
                                    message_new = result[message_start:]
                                    message = persona.create_message('', True)
                                    convo.add(message)
                                    message.display()
                                #print(message_new + '\n\n\n\n\n\n\n')
                                message_full = message.content + message_new
                                end = message_full.find(sep_end)
                                if end >= 0:
                                    message_complete = True
                                    message.generating = False
                                    #end -= len(message.content)
                                    #print('done')
                                    message.update(message_full[0:end])
                                    await channel.send(message.content)
                                else:
                                    end = len(message_full)
                                    message.update(message_full[0:end])
                        '''
                        nextmsg = [persona.get_system_prompt()] + convo.get_lines()
                        print('hi', nextmsg)
                        foo = persona.generate(nextmsg)
                        #print('neh', foo)
                        message = persona.create_message(foo)
                        convo.add(message)
                        message.display()
                        #await channel.send(foo)
                        chunks = split_string_into_chunks(foo)
                        for chunk in chunks:
                            await channel.send(chunk)
                    except discord.errors.HTTPException as e:
                        await channel.send('Oops, something went wrong: ' + str(e))


    discord_client.run(cfg['discord']['token'])


    #except RuntimeError as e:
    #    print('\033[38;5;12m   │')
    #    print('\033[38;5;12m   └ \033[38;5;15mSession terminated (%s)' % str(e))
    #    print()
    #except torch.distributed.elastic.multiprocessing.api.SignalException:
    #    print('BLARGH')
    #except KeyboardInterrupt:
    #    print('Quitting')

def split_string_into_chunks(input_string):
    MAX_LENGTH = 2000
    chunks = []

    # Splitting string into chunks based on code blocks
    code_blocks = input_string.split("```")
    for i, block in enumerate(code_blocks):
        if i % 2 == 0:  # Non-code block
            current_chunk = ""
            for line in block.split("\n"):
                if len(current_chunk) + len(line) + 3 <= MAX_LENGTH:  # Account for newline and backticks
                    current_chunk += line + "\n"
                else:
                    chunks.append(current_chunk.strip())  # Strip the chunk
                    current_chunk = line + "\n"
            if current_chunk:
                chunks.append(current_chunk.strip())  # Strip the chunk
        else:  # Code block
            while block:
                chunk = "```" + block[:MAX_LENGTH - 6] + "```"  # Account for code block formatting
                chunks.append(chunk.strip())  # Strip the chunk
                block = block[MAX_LENGTH - 6:]

    # Remove chunks of length 0
    chunks = [chunk for chunk in chunks if len(chunk) > 0]

    return chunks

if __name__ == "__main__":
    fire.Fire(main)
