from flask import request, render_template, send_from_directory
import multaichat.personas, multaichat.chat
import json

def index():
    personas = multaichat.personas.load()
    print(personas)
    return render_template('index.html', personas=personas)

def chat():
    personas = multaichat.personas.load()
    return render_template('chat.html', personas=personas)

def settings():
    return render_template('settings.html')

def persona():
    personas = multaichat.personas.load()
    persona = None
    persona_name = request.args.get('name')
    if persona_name in personas:
        persona = personas[persona_name]
    else:
        persona = multaichat.chat.ChatPersona(name=persona_name)
    return render_template('persona.html', persona=persona)

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
        if persona.save():
            return {'status': 'ok'}
        else:
            return {'status': 'failed'}
    
def api_personas_create():
    for name in personas:
        j[name] = personas[name].toJSON()
    return j
    
def serve_static_scripts(path):
    return send_from_directory('static/scripts', path)
def serve_static_css(path):
    return send_from_directory('static/css', path)

routes = {
  '/': chat,
  '/persona': persona,
  '/settings': settings,
  '/api/personas': { "view_func": api_personas_list, "methods": ['GET', 'POST'] },
  '/scripts/<path:path>': serve_static_scripts,
  '/css/<path:path>': serve_static_css,
}

def add_routes(app):
    #app.add_url_rule('/', view_func=index)
    #app.add_url_rule('/chat', view_func=chat)
    for url in routes:
        if callable(routes[url]):
            app.add_url_rule(url, view_func=routes[url])
        else:
            app.add_url_rule(url, **routes[url])
