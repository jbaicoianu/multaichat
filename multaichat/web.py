from flask import request, render_template
import multaichat.personas, multaichat.chat
import json

def index():
    personas = multaichat.personas.load()
    print(personas)
    return render_template('index.html', personas=personas)

def chat():
    personas = multaichat.personas.load()
    return render_template('chat.html', personas=personas)

def persona():
    return render_template('persona.html')

def api_personas_list():
    print(request.method)
    if request.method == 'GET':
        personas = multaichat.personas.load()
        j = {}
        for name in personas:
            j[name] = personas[name].toJSON()
        return j
    elif request.method == 'POST':
        persona = multaichat.chat.ChatPersona(**request.json)
        print(persona.toJSON())
        persona.save()
        return {'status': 'ok'}
    
def api_personas_create():
    for name in personas:
        j[name] = personas[name].toJSON()
    return j
    

routes = {
  '/': index,
  '/chat': chat,
  '/persona': persona,
  '/api/personas': { "view_func": api_personas_list, "methods": ['GET', 'POST'] }
}

def add_routes(app):
    #app.add_url_rule('/', view_func=index)
    #app.add_url_rule('/chat', view_func=chat)
    for url in routes:
        if callable(routes[url]):
            app.add_url_rule(url, view_func=routes[url])
        else:
            app.add_url_rule(url, **routes[url])
