from flask import Flask
from multaichat import web, discord
from multiprocessing import Process
import fire
import torch
torch.multiprocessing.set_start_method('spawn')

app = Flask('multaichat', static_folder='./static')
app.config['TEMPLATES_AUTO_RELOAD'] = True
web.add_routes(app)

#fire.Fire(discord.main)
#discord.main(False)
p = Process(target=discord.main)
p.start()
