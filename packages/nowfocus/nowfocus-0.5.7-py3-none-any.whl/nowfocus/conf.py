import os.path
import json
import importlib
from datetime import datetime, timezone
from pathlib import Path
import copy

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

# Set working dir to file location 
os.chdir(os.path.dirname(os.path.realpath(__file__)))
app_id = "nowfocus" # Folder name for xdg config and data locations 
app_name = "nowfocus" # What shows up with pidof and in window titles etc

user_data_dir = GLib.get_user_data_dir()+"/"+app_id
Path(user_data_dir).mkdir(parents=True, exist_ok=True)

user_settings_dir = GLib.get_user_config_dir()+"/"+app_id
''' Depreciated. use user_data_dir instead '''

db_file = user_data_dir+"/data.db"
settings_file = user_data_dir+"/nowfocus-settings.json"
debug_level = 1 # dev value 
debug_systems = []
pipe = "/tmp/"+app_id+"-pipe"
is_first_load = False

# key and type must be the same, (Seems redundant but it's is quite helpful) 
connectors = {
    "todolists":{
        'txt':{'id':'txt','type':'txt','label':'','file':'', "watch_file":True, "status":True,'timetracker':''},

        'trello':{'id':'trello','type':'trello','label':'Trello','APIKey':'aecf1d7791b4f1a4bb7d6ca5827ba0d3', 'token':'',"status":True,'timetracker':''},

        'vikunja':{'id':'vikunja','type':'vikunja','label':'Vikunja','url':'http://localhost:3456/', 'token':'',"username":"","status":True,'timetracker':''},
        
        'caldav':{'id':'caldav','type':'caldav','label':'CalDav Todo','url':'http://localhost:3456/','password': "",'username': '',"status":True,'timetracker':''},
        
        'psc_timetracker':{'id':'psc_timetracker','type':'psc_timetracker','label':'Timetracker','url':'https://photosynth.ca/timetracker/','key':'',"status":True,'timetracker':'Timetracker'},
        
        'taskwarrior':{'id':'taskwarrior','type':'taskwarrior','label':'TaskWarrior',"status":True,'timetracker':''},
        
        'todotxt':{'id':'todotxt','type':'todotxt','label':'','file':"", "watch_file":True, "status":True,'timetracker':''},
    },
    "timetrackers":{
        'csv':{'id':'csv','type':'csv','label':'CSV file','file':'sessions.csv',"status":True}, 
        'activitywatch':{'id':'activitywatch','type':'activitywatch','label':'ActivityWatch','url':'http://localhost:5600/',"status":True}, 
        'psc_timetracker':{'id':'psc_timetracker','type':'psc_timetracker','label':'Timetracker','url':'https://photosynth.ca/timetracker/','key':'',"status":True},
        'timewarrior':{'id':'timewarrior','type':'timewarrior','label':'TimeWarrior',"status":True}, 
    }
}

todo_sync_time = datetime.now() 
todo_sync_times = {}

todo_file_change_times = {}
timers = {}

prototype_settings = {
        "pomodoro_interval": 40,
        "open_task_window_fullscreen": True,
        "show_task_window_sidebars": False,
        "randomness_interrupt_interval":7, #minutes
        "device_not_in_use_threshold":3.5, #minutes
        "default_text": "What am I doing?",
        "todolist_refresh_interval":1,    #hours
        "version":0.4,
        "display_todolist_as_top_level_list":'auto',
        'max_top_level_menu_items':10,
        'hours_search_timeframe':'this year',
        'invoice_hourly_rate':0,
        'default_list_for_new_tasks':'Most recently used list',

        "custom_pomodoro_intervals": {
            "email":7  #minutes
        },

        'prompts':'What am I doing?\nWhy am I here?\nWhat could I do?\nWhat do I wish to accomplish?\nWhat is my aim?\nWhat\'s next',

        'time_targets':{
            'tasks':{},
            'lists':{}
        },

        'task_commands':{
            'task_id':{'status': True, "command":"firefox"},
        },

        "todolists": {
            "Nowfocus Todo":{
                "id":"Nowfocus Todo",
                "type": "txt",
                "label": "Nowfocus Todo",
                "file": user_data_dir+'/nowfocus-todo.txt',
                "timetracker":"Example CSV",
                "status":True
            }
        },
        "timetrackers":{
            "Example CSV":{
                "id": "Example CSV",
                "label": "Example CSV",
                "type":"csv",
                "file":user_data_dir+'/nowfocus-timetracking-spreadsheet.csv',
                "status":True
            }
        }
    }

if os.path.isfile(settings_file):
    with open(settings_file, "r") as file:
        settings = json.load(file)

# Backward compatibility, check in old settings dir 
elif os.path.isfile(user_settings_dir+"/user_settings.json"):
    with open(user_settings_dir+"/user_settings.json", "r") as file:
        settings = json.load(file)
else:

    print("Setting up initial settings file")
    is_first_load = True
    settings = {}


user = {}

# Merge settings with prototype settings
for key, val in prototype_settings.items():

    if settings and key in connectors:
        user[key] = {}

        # merge and validate todolist and timetracker settings against connector prototypes 
        for c_key, c_val in settings[key].items():
            
            if c_val['type'] in connectors[key]:
                proto = copy.copy(connectors[key][c_val['type']])
                user[key][c_key] = proto
            else:
                print('ERROR: no connector for type '+c_val['type']+' in settings_file','skipping that connector',c_val)
                continue

            # print('validate user_settings connector against prototype.','user',c_val,'proto',proto)

            for p_field, p_value in proto.items():
                
                if p_field in c_val: 
                    if type(c_val[p_field]) == type(p_value):
                        user[key][c_key][p_field] = c_val[p_field]
                    else:
                        print(p_field+" is the wrong type "+str(type(c_val[p_field]))+"("+str(c_val[p_field])+") in user conf for connector "+c_key+" using fallback: "+str(p_value))
                else:
                    print("Adding missing: connection field "+p_field+")") 

    elif key in settings and type(settings[key]) == type(val):
        user[key] = settings[key]
    else:
        user[key] = val
        
# print(json.dumps(user, indent=4))
# print(json.dumps(connectors['todolists'], indent=4))


with open(settings_file,"w") as file:
    json.dump(user, file)

todo_connectors = {}
timetracker_connectors = {}

try:

    for id, todolist in user['todolists'].items(): 
        todo_connectors[todolist['type']] = importlib.import_module('connectors.'+todolist['type'])
        
    for id, timetracker in user['timetrackers'].items(): 
        timetracker_connectors[timetracker['type']] = importlib.import_module('connectors.'+timetracker['type'])
except Exception as e:
    print("error loading connector")
    print(e)