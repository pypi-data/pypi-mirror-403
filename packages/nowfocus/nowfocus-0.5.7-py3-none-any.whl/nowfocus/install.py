import os.path
import json
import importlib
from datetime import datetime, timezone
from pathlib import Path
import copy
import subprocess, sys
import shutil

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, Gio

# Set working dir to file location 
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Add working dir to path
sys.path.append(os.path.dirname(__file__))

import conf
from utils import *

def run_first_load_actions():
    db_init()
    create_default_timetracking_csv()
    create_default_todo()
    copy_desktop_integration_files()


def create_default_timetracking_csv():
    target_file = conf.user_data_dir+'/nowfocus-timetracking-spreadsheet.csv'
    
    data = 'date,duration,project,task,start time'

    if not os.path.isfile(target_file):
        with open(target_file, 'w') as file:
            file.writelines(data)
        print("Created default timetracker at "+target_file)
    else:
        print("Default timetracker already exists at "+target_file)


def create_default_todo():
    source_file = 'example-todo.txt'
    target_file = conf.user_data_dir+'/nowfocus-todo.txt'

    if not os.path.isfile(target_file):
        with open(source_file, 'r') as file:
            data = file.readlines()

            with open(target_file, 'w') as file:
                file.writelines(data)


def db_init():
    if not os.path.isfile(conf.db_file):
        print('initializing database')

        db_query("CREATE TABLE lists (id TEXT, label TEXT DEFAULT '', parent_id TEXT DEFAULT '', parent_label TEXT DEFAULT '', todolist TEXT DEFAULT '', priority INTEGER DEFAULT 0, status INTEGER DEFAULT 1, extended_label TEXT DEFAULT '', data TEXT DEFAULT '{}');")

        db_query("CREATE TABLE tasks (id TEXT, label TEXT DEFAULT '', parent_id TEXT DEFAULT '', parent_label TEXT  DEFAULT '', todolist TEXT DEFAULT '', priority INTEGER DEFAULT 0, status INTEGER DEFAULT 1, extended_label TEXT, data TEXT DEFAULT '{}');")

        # , tags TEXT
        
        db_query("CREATE TABLE sessions (start_time TEXT, duration INTEGER, task_id TEXT, parent_id TEXT, todolist TEXT, extended_label TEXT, notes TEXT, priority INTEGER DEFAULT 0, timetracker TEXT);")

        db_query("CREATE TABLE system (field TEXT PRIMARY KEY NOT NULL, value TEXT);")

        db_query("INSERT INTO system(field, value) VALUES('db_schema_version', '0.5')")
     

def copy_desktop_integration_files():

    home = GLib.get_home_dir()

    files = (
        (home+'/.local/share/icons/hicolor/scalable/apps','nowfocus.svg'),
        (home+'/.local/share/icons','nowfocus.png'),
        (home+'/.local/share/applications/','nowfocus.desktop'),
        (home+'/.config/autostart/','nowfocus.desktop')
    )

    for file in files:
        try:
            Path(file[0]).mkdir(parents=True, exist_ok=True)
            shutil.copy("desktop-extras/"+file[1],file[0])
            print("Copied "+file[1]+" to "+file[0])

        except Exception as e:
            print("Error Copying "+file[1]+" to "+file[0],e)

