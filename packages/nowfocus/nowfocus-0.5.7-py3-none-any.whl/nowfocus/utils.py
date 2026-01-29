import os
import time
import json
import webbrowser
import subprocess, sys
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import copy
import threading
import sqlite3 
from contextlib import closing
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
gi.require_version('Notify', '0.7')
from gi.repository import Notify as notify


# TODO: only import the following if dbg level is ... 2? or system is 'performance'? IDK
import inspect 
import traceback


import conf
notify.init(conf.app_name)

lists = {}


def dbg(*data, s="", l=2, e=None, notification=None):
    ''' Any number of positional args optionally
    l: level {-1: Default output, 0:Error, 1:Warning, 2:Info, 3:Details}  
    s: system (Debuggable systems: 'taskwindow','signals','todoloading','user_settings', 'targets', 'performance')
    notification: Show a notification with the content of notification.
    e (Exception object) traceback will be printed
    
    '''

    levels = {-1:'', 0:'Error', 1:'Warning', 2:'Info', 3:'Details'}

    system = s
    level = int(l)


    if "all" in conf.debug_systems or system in conf.debug_systems or level <= conf.debug_level: 

        if notification:
            notify.Notification.new(conf.app_name+" "+levels[level], str(notification), None).show()

        filter(None,data)
        if len(data) == 1:
            data = data[0]
        if system:
            system = "- "+system

        try:
            print(json.dumps(data,indent=2), system+" "+levels[level])
        except:
            print(data)


    # else:
    #     print("Not displaying dbg s:",system,'conf.debug_systems',conf.debug_systems)
    #     pretty_print(data)

    if e and isinstance(e,Exception): 
        traceback.print_tb(e.__traceback__)
        print(e,"\n")

def error_notice(title, details = None, e = None):
    print('ERROR',title,details,e)
    notify.Notification.new(str(title),str(details), None).show()


def pretty_dict(i, item_sep = ", ", use_indents=True, indent=''):
    o = ''
    if use_indents:
        o += indent

    if isinstance(i,dict):
        for key, val in i.items():

            o += str(key).capitalize() + ": "
            if isinstance(val,(dict,list,tuple)): 
                o += "\n" + pretty_dict(val, item_sep, use_indents, indent + '  ')
            else: 
                o += str(val) + item_sep

    elif isinstance(i,(list,tuple)):
        for val in i:
            if isinstance(val,(dict,list,tuple)): 
                o += "\n" + pretty_dict(val, item_sep, use_indents, indent + '  ')
            else: 
                o += str(val) + item_sep
    else:
        o += str(i) + item_sep

    return o


def pretty_print(i):
    print(pretty_dict(i))


def timeit(process=None):
    # if 'performance' in conf.debug_systems or conf.debug_level >= 2:
    if not process:
        process = inspect.currentframe().f_back.f_code.co_name

    if process in conf.timers.keys():
        timer = time.time() - conf.timers[process]
        dbg(process, 'took', timer, 'seconds', s='performance',l=2)
        del conf.timers[process]
        return timer
    else:
        dbg(process, 'performance timer started',s='performance',l=3)
        conf.timers[process] = time.time()
        return process


def time_to_sec(time=None):
    if not time:
        return 0
    sec = 0
    for k, v in enumerate(reversed(time.split(':'))):
        sec += int(v) * 60 ** k
    return sec


def sec_to_time(sec):

    try:
        int(sec)
    except Exception as e:
        print("sec to time error", e)
        sec = 0

    time = str("{:02d}".format(int(sec // 3600))) + ':' + str("{:02d}".format(int((sec % 3600) // 60))) + ':' + str("{:02d}".format(int(sec % 60)))
    return time.lstrip('0').lstrip(':')


def now():
    return datetime.now()
    # return datetime.now(timezone.utc).astimezone().tzinfo


def start_of_day():
    return now().replace(hour=0,minute=0,second=0,microsecond=0)


def time_difference(earlier, later = None):
    ''' Return seconds (float), later defaults to now'''
    # date_format = "%Y-%m-%dT%H:%M:%S.%f%z" # This can probably be updated / tossed (ActivityWatch format )
    if type(earlier) == str:
        earlier = datetime.strptime(earlier,'%Y-%m-%dT %H:%M:%S')

    if not later:
        later = now() 

    difference = later - earlier

    return difference.total_seconds()


def validate_start_time_str(start_time_string):
    try:
        return datetime.strptime(start_time_string,'%Y-%m-%d %H:%M:%S')

    except Exception as e:
        error_notice('Incorrect Start Time Format', start_time_string+" does no match %Y-%m-%d %H:%M:%S", e)
        return False


def open_todo(w=None, i=None, item_type = 'tasks'):
    ''' run the launch() function from the todo connector for the provided i(tem) '''
    if not isinstance(i, dict): 
        i = db_get_item_by_id(i,item_type)

    todo = conf.user['todolists'][i['todolist']]

    try:
        conf.todo_connectors[todo['type']].launch(todo,i,item_type)
    
    except Exception as e:
        # error_notice('Bonk', "error with "+ c['type']+ " open function ")
        dbg('open_todo excption, falling back to get_connector_openable ',e,s=todo['type'],l=1)

        get_connector_openable(None,todo)
    

def get_connector_openable(widget = None, connector_dict = None, open_it = True):

    for option in ['file','front_end_url','url','uri','open_command']:

        if option in connector_dict:
            if open_it:
                open_external(connector_dict[option])
                return True
            else:
                return connector_dict[option]

    dbg('get_connector_openable failed for',l=1,s=connector_dict['type'])
    dbg('connector_dict passed to get_connector_openable',connector_dict,l=3,s=connector_dict['type'])
    return False


def open_external(i):
    # if platform.system() == "Windows":
    #     os.startfile(folder_path)
    # else:
    if(i.startswith('http')):
        webbrowser.open(i,1,True)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, i])


def get_lists_for_item(i): 
    ''' i can be a task or a list
    Returns {'ids':['l_1','l_12','l_123],'labels':['todolist label','project','sub project']}'''

    lists = lists_cache()
    # pretty_print(lists)

    ids = []
    labels = []

    if i and 'parent_id' in i and i['parent_id'] and i['parent_id'] in lists:

        l = lists[i['parent_id']]

        while l:
            ids.insert(0, l['id'])
            labels.insert(0, l['label'])
            if l['parent_id'] in lists:
                l = lists[l['parent_id']]
            else: 
                break

    # This may need empty val filtering . see: https://stackoverflow.com/a/3845449/4692205

    output = {'ids':ids,'labels':labels}

    # print('get_lists_for_item',i['label'])
    # pretty_print(output)

    return output


def extended_label(i):
    if not i:
        dbg('emptiness passed to extended_label',i)
        return ''

    lists = get_lists_for_item(i)
    l = lists['labels']
    l_ids = lists['ids']

    if conf.user['display_todolist_as_top_level_list'] != 'always':
        if l_ids and l_ids[0] == i['todolist']:
            del l[0]

    l.append(i['label'])
    o = ' > '.join(l)
    return o

# TODO cleanup this
def lists_cache(new_lists = None, reset = False):
    '''Set or get a dict of (all) lists. If new_lists is supplied it will exclusively use that (until it is replaced or the global lists var is emptied) This is useful (because it can be used wih input when the values are not yet available in the databse) but wonky. '''

    global lists
    
    if(new_lists):
        lists = new_lists
        # TODO: add a param to append to the existing lists rather than overwriting...
    
    elif reset or lists == {}:
        lists = db_query('SELECT * FROM lists WHERE status = 1 ORDER BY extended_label DESC',None, 'id') 

        for id, l in lists.items():
            lists[l['id']] = proc_db_item(l,'lists')

    return lists 


def first(i, default = None):

    if isinstance(i, (tuple,list)):
        return i[0]

    elif isinstance(i,dict):
        return  next(iter(i.values()))


def save_user_settings():
    print("Save updated user_settings")
    dbg(conf.user)
    with open(conf.settings_file,"w") as settings_file:
        json.dump(conf.user, settings_file)


def db_query(sql,parameters=None,key=None,error_handling=1):
    '''error_handling: 2 = raise error, 1 = notify error, 0 = ignore errors '''
    # print('db_query parameters type: ',type(parameters))
    # print('first(parameters)',first(parameters))
    c = sqlite3.connect(conf.db_file)
    c.row_factory = sqlite3.Row
    try:
        with c:
            if parameters:
                
                if isinstance(parameters, (dict,list)) and isinstance(first(parameters), (dict)):
                    if isinstance(parameters, dict):
                        parameters = list(parameters.values())
                    
                    rows = c.executemany(sql,parameters).fetchall()
                        
                else: 
                    rows = c.execute(sql,parameters).fetchall()

            else:
                rows = c.execute(sql).fetchall()

            result = [dict(row) for row in rows]

            if key and result and key in result[0]:
                o = {}
                for row in result:
                    o[row[key]] = row
                result = o
            # print("db_query result",result)
        c.close()
        return result

    except Exception as e:
        dbg("sql",sql,'parameters',parameters,s="db",l=0,e=e)
        if error_handling > 0:
            error_notice("database error",str(e))
            if error_handling > 1:
                raise e
        if key: 
            return {}
        else:
            return []


def reindex(t=None):
    if t:
        thread = threading.Thread(target=reindex_one,args=(t,))
    else:
        thread = threading.Thread(target=reindex_all)
    thread.start()


def reindex_all():
    timeit()
    # print('reindex start')
    db_query("DROP TABLE IF EXISTS taskindex",None,None,0)
    db_query("CREATE VIRTUAL TABLE taskindex USING fts5(id, extended_label, priority, status)")
    db_query("INSERT INTO taskindex(id, extended_label, priority, status) SELECT id, extended_label, priority, status FROM tasks WHERE tasks.status IS NOT '-1' ")

    for tid, t in get_timetarget_priority_tasks().items():
        db_query("UPDATE taskindex set priority = ? WHERE id = ?",(t['priority'],t['id']))

    
    set_system_db_value('taskindex_update_time', now().strftime("%Y-%m-%d %H:%M:%S"))
    # db_query("REPLACE INTO system(field, value) VALUES(?,?)",('taskindex_update_time',now().strftime("%Y-%m-%d %H:%M:%S")))
    # print('reindex done')
    timeit()

    return True


def reindex_one(t):
    ''' t must be a task object'''

    # print("before reindex one")
    # print(db_query("SELECT * FROM taskindex where id = ?",(t['id'],)))

    db_query("DELETE FROM taskindex where id = ?",(t['id'],))

    db_query("INSERT INTO taskindex(id, extended_label, priority, status) SELECT id, extended_label, ?, status FROM tasks WHERE id = ? ",(time_target_priority(t),t['id'],))

    dbg("reindexed",t['label'])
    # print(db_query("SELECT * FROM taskindex where id = ?",(t['id'],)))
    # db_query("REPLACE INTO system(field, value) VALUES(?,?)",('taskindex_update_time',now().strftime("%Y-%m-%d %H:%M:%S")))
    set_system_db_value('taskindex_update_time', now().strftime("%Y-%m-%d %H:%M:%S"))

    return True


def taskindex_updated_time():
    ''' returns system db taskindex_update_time string formatted as %Y-%m-%d %H:%M:%S '''
    get_system_db_value('taskindex_update_time')

    update_time = db_query("SELECT value FROM system WHERE field = 'taskindex_update_time'")[0]['value']
    
    # print('taskindex_updated_time',update_time)
    # return datetime.strptime(update_time,'%Y-%m-%d %H:%M:%S')
    return update_time


def taskindex_search(i):
    #dbg({"task search":i},s='taskwindow')

    params = ('"'+i+'"*',)
    conditions = ' WHERE extended_label MATCH ?'
    limit = ''
    order_by = 'taskindex.status DESC, taskindex.priority=0 ASC, taskindex.priority ASC, sessions.start_time DESC, rank ASC' 

    if len(i) == 0:
        # Default Tasks
        params = None
        # limit = 'LIMIT 25'
        conditions = ''
        order_by = 'taskindex.status DESC, taskindex.priority=0 ASC, taskindex.priority ASC, sessions.start_time DESC'
        
    elif  i == '*':
        params = None
        conditions = ''

    elif '"' in i or '>' in i:
        # exact substring match 
        conditions = ' WHERE extended_label LIKE ? '
        params = ('%'+i.replace('"','')+'%',)
        
    # elif len(i) == 1:
        # limit = 'LIMIT 25'

    # TODO: Fix sort by last session when session_timeframe is short  

    tasks = db_query("SELECT id, extended_label, status, priority, sessions.duration as duration FROM taskindex LEFT JOIN (SELECT SUM(sessions.duration) as duration, start_time, task_id FROM sessions WHERE "+sessions_timeframe_sql()+" GROUP BY task_id ORDER BY MAX(sessions.start_time) DESC) as sessions ON sessions.task_id = taskindex.id "+conditions+" ORDER BY "+order_by+" "+limit, params, 'id')
    
    # dbg('task_window search tasks',tasks,s='taskwindow',l=1)

    return tasks


def db_to_py_type_map(db_type, value=None):
    types = {
        'INTEGER':int,
        'BOOLEAN':bool,
        'REAL':float,
        'TEXT':str,
        'BLOB':bytes,
    }

    if isinstance(value, (dict,list,tuple)) and db_type in ['TEXT','BLOB']:
        return json.dumps(value)

    if db_type in types: 
        if value:
            return types[db_type](value)
        else:
            types[db_type]


def db_columns(table, cache = {}):
    ''' Returns the PRAGMA query, from cache '''

    if table not in cache: 

        if table not in ['lists','tasks','sessions','system']:
            raise ValueError("bad table passed to db_columns!")
        else:
            fields = db_query("PRAGMA table_info("+table+")")

            # sadly "Parameter markers can be used only for expressions, i.e., values. You cannot use them for identifiers like table and column names." 
            # fields = db_query("PRAGMA table_info(?)",(table,)) 
            
            cache[table] = fields

    return cache[table]


def time_target_priority(i, table = "tasks"):

    # NOTE: this will overwrite any list-level priority with 0 or 1 if the item or its list has a minimum time target, 
    # alternatives 
    #   (re)querying the database -- doesn't seem worth the overhead
    #   cache an initial priority in item data anytime that a tt priority is applied

    time_target_ballance = check_time_target(i, table, 'min')
    if time_target_ballance:
        if time_target_ballance > 0:
            # This could have more ... nuance...
            return 1

    else: 
        # pass through existing priority
        if 'priority' in i and i['priority'] and int(i['priority']) > 0:
            return i['priority']

    return 0 


def db_prepare_item(i,table = "tasks"):
    if table not in ['lists','tasks']:
        raise ValueError("bad table passed to db_prepare!")

    fields = db_columns(table)

    o = {}

    if not 'status' in i:
        i['status'] = 1

    if not 'extended_label' in i:
        i['extended_label'] = extended_label(i)

    # print('fields',fields)
    for f in fields:
        if f['name'] in i:
            o[f['name']] = db_to_py_type_map(f['type'],i[f['name']])
        else:
            o[f['name']] = f['dflt_value']
    
    return o


def db_set_item(i,table = "tasks"):
    raw = copy.copy(i)
    i = db_prepare_item(i,table)

    columns = ', '.join(i.keys())
    placeholders = ':'+', :'.join(i.keys())

    db_query('INSERT INTO '+table+' (%s) VALUES (%s)' % (columns, placeholders),[i])
    if table == 'tasks':
        reindex(raw)

# def db_edit_session(session, column, new_value):
#     dbg("db_edit_session", session, 'column', column, 'new value', new_value)
    
#     db_query("UPDATE session set ? = ? WHERE start_time = ? AND extended_Label = ? LIMIT 1",(column, new_value, session['start_time'], session['extended_label']))
    
#     db_query("select * FROM sessions WHERE start_time = ? AND extended_Label = ? ",(session['start_time'], session['extended_label']))

def db_set_todolist(todolist_id,lists,tasks):
    # print('db_set_todolist params: \ntodolist_id: ',todolist_id,'lists: ',lists,'tasks: ',tasks)

    insert_tasks = {}
    insert_lists = {}

    # use the parameter-provided lists for extended label instead of the existing (db) lists
    lists_cache(lists)
        
    for id, i in lists.items():
        insert_lists[id] = db_prepare_item(i,'lists')
    
    for id, i in tasks.items():
        insert_tasks[id] = db_prepare_item(i,'tasks')

    # Clear incomplete lists cache
    lists_cache(reset=True)

    # for testing
    # insert_tasks = {'3':insert_tasks['3'],'294':insert_tasks['294']}
    # print('insert_tasks: ',json.dumps(insert_tasks,indent=4))

    db_query("DELETE FROM tasks WHERE todolist = ?",(todolist_id,)) # What about removed 
    db_query("DELETE FROM lists WHERE todolist = ?",(todolist_id,))

    if insert_tasks:
        task_columns = insert_tasks[list(insert_tasks.keys())[0]].keys()
        columns = ', '.join(task_columns)
        placeholders = ':'+', :'.join(task_columns)

        db_query('INSERT INTO tasks (%s) VALUES (%s)' % (columns, placeholders),insert_tasks)
        
    if insert_lists:
        list_columns = insert_lists[list(insert_lists.keys())[0]].keys()
        columns = ', '.join(list_columns)
        placeholders = ':'+', :'.join(list_columns)

        db_query('INSERT INTO lists (%s) VALUES (%s)' % (columns, placeholders),insert_lists)


def db_cleanup(widget = None):
    
    # ids = tuple(conf.user['todolists'].keys())
    ids = []
    # print('ids_sql',ids_sql)
    for id, todo in conf.user['todolists'].items():
        ids.append(id)

    # Old save
    # print("Active todolist ids",ids)

    # Delete unlinked tasks
    db_query('DELETE FROM tasks WHERE todolist NOT IN (%s)' % ','.join('?'*len(ids)),ids)
    
    # print(len(orphaned_tasks),"orphaned_tasks",orphaned_tasks)
    # orphaned_tasks = db_query('SELECT id, extended_label, todolist FROM tasks WHERE todolist NOT IN (%s)' % ','.join('?'*len(ids)),ids)
    # print(len(orphaned_tasks),"orphaned_tasks",orphaned_tasks)
    
    # Delete unlinked lists
    db_query('DELETE FROM lists WHERE todolist NOT IN (%s)' % ','.join('?'*len(ids)),ids)

    # orphaned_lists = db_query('SELECT id, extended_label, todolist FROM lists WHERE todolist NOT IN (%s)' % ','.join('?'*len(ids)),ids)
    # print("orphaned_lists",orphaned_lists)

    missing_task_sessions = db_query("SELECT * FROM sessions WHERE task_id NOT IN (SELECT id FROM tasks)")
    # print("missing_task_sessions",missing_task_sessions)
    print('found',len(missing_task_sessions),'unlinked sessions')

    for s in missing_task_sessions:
        if s['extended_label']:
            print(s['extended_label'])
            possible_matches = db_query("SELECT * FROM tasks WHERE extended_label = ? ORDER BY status DESC",(s['extended_label'],))
            if len(possible_matches) > 0:
                match = first(possible_matches)
                print("Found 1 task with exact-match extended_label",s['extended_label'])
                print('Relinking',s['task_id'],'to', match['id'])
                db_query("UPDATE sessions SET task_id = ?, parent_id = ? WHERE task_id = ?",(match['id'],match['parent_id'],s['task_id']))
                # print(pretty_print(possible_matches))
            # else:
                # not very good yet...
                # search = db_query("SELECT *, rank FROM taskindex WHERE extended_label MATCH ? ORDER BY rank DESC",(s['extended_label'].replace('>','').replace('?',''),))
                # print('fuzzy search results',(search,))

    # update extended_labels
    # mismatched_sessions = db_query("SELECT * FROM sessions WHERE extended_label NOT IN (SELECT extended_label FROM tasks)")

    db_query("UPDATE sessions SET extended_label = (SELECT extended_label FROM tasks WHERE id = task_id), parent_id = (SELECT parent_id FROM tasks WHERE id = task_id) WHERE task_id IN (SELECT id FROM tasks) AND extended_label != (SELECT extended_label FROM tasks WHERE id = task_id)")

    # db_query("SELECT label, todolist FROM tasks WHERE todolist NOT IN ?",(ids_sql,))
    # db_query("DELETE FROM tasks WHERE todolist  NOT IN "+ids_sql)
    # db_query("DELETE FROM lists WHERE todolist NOT IN "+ids_sql)

    # exit()

def db_get_item_by_id(id, table = 'tasks',dgb_error_level_for_failure=0):

    if table in ['task','list']:
        table = table+'s'
    if table not in ['tasks','lists']:
        dbg('bad table "'+str(table)+'" passed to db_get_item_by_id',id,l=0)
        return {}
    
    # in case an item dict was passed instead of an id
    if isinstance(id, dict):
        return id

    try:
        data = db_query("SELECT * FROM "+table+" WHERE id = ?",(id,))
        # print(data)
        if data:
            return proc_db_item(data[0],table)
        else:
            dbg('db_get_item_by_id from '+table+' failed for id',id,l=dgb_error_level_for_failure)
            return {}

    except Exception as e:
        dbg('db_get_item_by_id failed',e,l=dgb_error_level_for_failure)


def get_todo_by_id(todo_or_todo_id = None):
    ''' get user_conf todo connector data, does not validate  '''
    if todo_or_todo_id and isinstance(todo_or_todo_id, str):
        if todo_or_todo_id in conf.user['todolists']:
            return conf.user['todolists'][todo_or_todo_id]
        else:
            return None

    return todo_or_todo_id


def proc_db_item(i,table='tasks'):
    ''' Parse task or list data json and apply time target priority '''
    i['data'] = json.loads(i['data'])
    i['parent_label'] = str(i['parent_label']) #
    i['priority'] = time_target_priority(i,table)
    return i


def db_get_todolist(todolist_id):
    tasks = {}

    for t in db_query("SELECT * FROM tasks WHERE status = 1 AND todolist = ?",(todolist_id,)):
        tasks[t['id']] = proc_db_item(t)

    lists = {}
    for l in db_query("SELECT * FROM lists WHERE todolist = ? AND status = 1",(todolist_id,)):
        lists[l['id']] = proc_db_item(l,table='lists')

    o = {'lists': lists, 'tasks':tasks}
    return o


def db_save_session(session):
    dbg("db_save_session",session)
    prepared_session = {
        'start_time' : str(session['start_time'].strftime("%Y-%m-%d %H:%M:%S")),
        'duration': round(session['duration']),
        'task_id': str(session['task']['id']),
        'parent_id': str(session['task']['parent_id']),
        'todolist': str(session['task']['todolist']),
        'extended_label': str(session['extended_label']),
        'timetracker': str(session['timetracker']),
        'notes': str(session['notes']),
        'priority': "0",
    }

    if 'priority' in session['task']:
        prepared_session['priority']: str(session['task']['priority'])
    
    db_query("INSERT INTO sessions(start_time, duration, task_id, parent_id, todolist, extended_label,timetracker, notes, priority) VALUES(:start_time, :duration, :task_id, :parent_id, :todolist, :extended_label, :timetracker, :notes, :priority )",prepared_session)

    reindex(session['task'])


def default_session():

    # TODO: if 'default_task' in user_conf:
    #     # use it!

    o =  {
        "label":"Randomness",
        "extended_label": 'Randomness',
        "start_time":datetime.now(),
        "duration":0,
        'task':{
            "label":"Randomness",
            'id':'Randomness',
            'parent_id':'None',
            'todolist':'None',
        },
        'timetracker': 'None',
        'notes':'',
    }
    return o


def get_sessions(conditions_sql = None, order_by = 'start_time', limit = 35, use_sessions_timeframe_setting = False):

    conditions = ''

    if conditions_sql:
        conditions += " AND "+conditions_sql

    if use_sessions_timeframe_setting:
        conditions += " AND "+sessions_timeframe_sql()

    return db_query(" SELECT * FROM sessions WHERE 1=1 "+conditions+" ORDER BY "+order_by+" DESC LIMIT ? ",(limit,)) 


def show_sessions(widget = None, self = None, sessions_box = None, label_text = "Most Recent Sessions", order_by = 'start_time', limit = 35, passed_sessions = None, truncate_labels_to_chars = None ):

    sessions_box.foreach(lambda child: child.destroy()) 

    if passed_sessions:
        dbg("using passed_sessions",passed_sessions,s='settings')
        sessions = passed_sessions
    else:
        dbg("show_sessions: order_by:",order_by, 'limit',limit, s='settings')
        sessions = db_query(" SELECT * FROM sessions WHERE "+sessions_timeframe_sql()+" ORDER BY "+order_by+" DESC LIMIT ? ",(limit,)) 


    if label_text:
        label = Gtk.Label()
        if passed_sessions:
            label.set_markup('<b>'+label_text+'</b>')
        else:
            label.set_markup('<b>'+str(limit)+' '+label_text+' of '+conf.user['hours_search_timeframe']+'</b>')
        sessions_box.add(label)

    for ls in sessions:
        dbg('Add session to session_box',ls['extended_label'],s='settings')
        if truncate_labels_to_chars:
            label = ls['extended_label'].split('>')[-1].strip()
            if len(label) > truncate_labels_to_chars:
                label = label[:truncate_labels_to_chars]+'…'
            btn = Gtk.Button(label=label+' '+str(sec_to_time(ls['duration'])))
        else:
            btn = Gtk.Button(label=ls['extended_label']+' '+str(sec_to_time(ls['duration'])))


        btn.set_halign(Gtk.Align.START)
        btn.set_relief(Gtk.ReliefStyle.NONE)

        btn.connect('clicked', lambda button_widget, ls: self.SessionEditDialog(None, self, ls),ls )
        
        sessions_box.add(btn)

    sessions_box.show_all()


def db_set_session_cache(s):
    ''' Add active session to system db table. Not to be confused with db_save_session '''
    db_session = copy.deepcopy(s)
    db_session['start_time'] = db_session['start_time'].strftime("%Y-%m-%d %H:%M:%S.%f%z")

    set_system_db_value('session', json.dumps(db_session))


def get_total_time(id, category = 'tasks', start_time = None, end_time = None, get_minutes = None):
    '''If start_time is int or float: it is treated as a number of days,
    Default returns num seconds, (unless get_minutes is True)
    end_time only work if start time is specified '''

    if category in ['list','lists']:
        where = 'parent_id'
    else:
        where = 'task_id'

    if start_time:
        
        if type(start_time) in [int,float]:
            start_time = start_of_day() - timedelta(days = start_time)
         
        if not end_time: end_time = now()
        
        result = db_query("SELECT sum(duration) as duration FROM sessions WHERE "+where+" = ? AND start_time > ? AND start_time < ? ",(id, start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S")))
    else:
        result = db_query("SELECT sum(duration) as duration FROM sessions WHERE "+where+" = ? ",(id,))

    # TODO make the list version (reverse) recursive
    # print("get_total_time result",result)

    result = force_number(result[0]['duration'])

    if get_minutes:
        result = result and result / 60 or 0
    
    return result


def get_percent_time_focused():

    rand_seconds = force_number(db_query("SELECT SUM(duration) as seconds FROM sessions WHERE sessions.task_id = 'Randomness' AND "+ sessions_timeframe_sql())[0]['seconds'])

    focus_seconds = force_number(db_query("SELECT SUM(duration) as seconds FROM sessions WHERE sessions.task_id != 'Randomness' AND "+ sessions_timeframe_sql())[0]['seconds'])

    percent = round(divide(focus_seconds,(focus_seconds + rand_seconds)) * 100)

    dbg('get_percent_time_focused', str(percent)+"%", 'focus_seconds', focus_seconds, 'rand_seconds', rand_seconds)

    return percent

def get_percent_time_priority():

    priority_seconds = force_number(db_query("SELECT SUM(duration) as seconds FROM sessions WHERE sessions.task_id = 'Randomness' AND "+ sessions_timeframe_sql())[0]['seconds'])

    total_seconds = force_number(db_query("SELECT SUM(duration) as seconds FROM sessions WHERE "+ sessions_timeframe_sql())[0]['seconds'])

    percent = round(divide(priority_seconds,(total_seconds)) * 100)

    dbg('get_percent_time_focused', str(percent)+"%", 'focus_seconds', priority_seconds, 'rand_seconds', total_seconds)

    return percent


def get_recent_tasks(count = 15):
    data = db_query("SELECT DISTINCT tasks.* FROM tasks JOIN sessions ON sessions.task_id = tasks.id WHERE tasks.status = 1 GROUP BY tasks.id ORDER BY MAX(sessions.start_time) DESC LIMIT ?",(count,))
    o = {}
    for t in data:
        o[t['id']] = proc_db_item(t)
    return o


def get_timetarget_priority_tasks():

    tt_task_ids = list(conf.user['time_targets']['tasks'].keys())
    tt_list_ids = list(conf.user['time_targets']['lists'].keys())

    tt_tasks = db_query('SELECT DISTINCT * FROM tasks WHERE id IN(%s)' % ','.join('?'*len(tt_task_ids)),tt_task_ids)
    tt_list_tasks = db_query('SELECT DISTINCT * FROM tasks WHERE parent_id IN(%s)' % ','.join('?'*len(tt_list_ids)),tt_list_ids)

    o = {}

    for t in tt_tasks + tt_list_tasks: 
   
        i = proc_db_item(t)
        if i['priority'] > 0: 
            o[t['id']] = t

    return o

def get_priority_tasks(count = 100):

    p_tasks = db_query("SELECT DISTINCT tasks.* FROM tasks WHERE priority > 0 AND status = 1 ORDER BY priority ASC LIMIT ?",(count,))

    tt_task_ids = list(conf.user['time_targets']['tasks'].keys())
    tt_list_ids = list(conf.user['time_targets']['lists'].keys())

    # TODO: [Performance] combine these two queries
    tt_tasks = db_query('SELECT DISTINCT * FROM tasks WHERE id IN(%s)' % ','.join('?'*len(tt_task_ids)),tt_task_ids)
    
    tt_list_tasks = db_query('SELECT DISTINCT * FROM tasks WHERE parent_id IN(%s)' % ','.join('?'*len(tt_list_ids)),tt_list_ids)

    o = {}

    for t in p_tasks + tt_tasks + tt_list_tasks: 
    # for t in tt_tasks + tt_list_tasks: #for testing
        i = proc_db_item(t)
        if i['priority'] > 0: 
            o[t['id']] = t
        # else: 
            # dbg('de-prioritize '+ t['label'], i['priority'], s='targets')


    dbg('priority tasks', o, s='targets', l=3)
    return o


def force_number(i):
      try:
        o = float(i)
      except:
        o = 0
      return o


def divide(a, b):
    a = force_number(a)
    b = force_number(b)

    if a == 0 or b == 0:
        return 0
    else:
        return (a / b)

def clamp(value, min_limit, max_limit):
    return max(min_limit, min(value, max_limit))


def invert_number_scale(i, max=5):
    ''' Flips a positive number within a given range '''
    o = abs(i - max )
    return o


def num_is_multiple_of(i,devisor = 2):
    try:
        i = int(i)
        if i > 0 and  (i / devisor).is_integer():
            return True
        else:
            return False

    except:
        return False


# TODO rename and cleanup
def get_times(task):
    day = start_of_day()
    week = day - timedelta(days = 7)
    month = day - timedelta(days = 30)

    o = {}
    task['parent_label'] = str(task['parent_label']) # This keeps causing a noneType + str concat error even though it should be a string already 

    o[task['label'] +' today'] = get_total_time(task['id'],'task',day)
    o[task['parent_label']+' today'] = get_total_time(task['parent_id'],'list',day)

    o[task['label'] +' weekly'] = get_total_time(task['id'],'task',week)
    o[task['parent_label']+' week'] = get_total_time(task['parent_id'],'list',week)    
    
    o[task['label'] +' monthly'] = get_total_time(task['id'],'task',month)
    o[task['parent_label']+' month'] = get_total_time(task['parent_id'],'list',month)

    for key, val in o.items():
        o[key] = sec_to_time(val)

    return o



def db_deactivate_todo(id):
    dbg("deactivating todolist: ",id, s='todoloading')
    # Delete inactive todo items (except where there are sessions for them) 
    # db_query("DELETE FROM tasks WHERE todolist = ? AND id NOT IN (SELECT task_id FROM sessions)",(id,))
    # db_query("DELETE FROM lists WHERE todolist = ? AND id NOT IN (SELECT parent_id FROM tasks)",(id,))

    db_query("UPDATE lists SET status = -1 WHERE todolist = ?",(id,))
    db_query("UPDATE tasks SET status = -1 WHERE todolist = ?",(id,))


def refresh_todolist(todo, catch_errors = False):

    ''' Refresh a single todo. runs db_set_todolist and returns todos. Exceptions must be handled my caller '''

    try:
        dbg('Refreshing '+todo['label'],l=2)
        
        todos = conf.todo_connectors[todo['type']].get_todos(todo)

        dbg('Refreshing '+todo['label'],l=-1)

        db_set_todolist(todo['id'],todos['lists'],todos['tasks'])

    except Exception as e:
        if catch_errors:
            dbb(notify='Error Loading '+todo['label']+' i refresh_todolist',e=e)
            todos = {'lists': {}, 'tasks':{}}

        else:
            raise e
     
    conf.todo_sync_times[todo['id']] = now() # It may seem foolish to do this even on an error, but otherwise it will constantly try to update when offline 

    clear_todo_file_change_time(todo)

    return todos

def clear_todo_file_change_time(todolist_conf):
    if todolist_conf['id'] in conf.todo_file_change_times:
        del conf.todo_file_change_times[todolist_conf['id']]

def handle_todo_read_error(todo_conf,e):

    if isinstance(e, (FileExistsError, FileNotFoundError, PermissionError)):
        handle_todo_file_access_error(todo_conf,e)

    dbg(todo_conf['label']+ " Access Error",e,l=0,notification=True)


def handle_todo_file_read_error(todo_conf,e):
    conf.user['todolists'][todo_conf['id']]['status'] = False
    save_user_settings()
    dbg(todo_conf['label']+ " Deactivated",e,l=-1,notification=True)


def get_todolists(use_db_cache = False):
    tasks = {}
    lists = {}  

    # TODO: Use threads to load todos concurrently?
    # with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    #    executor.map(thread_function, range(3))
    
    for id, todo in conf.user['todolists'].items(): 
        if not todo['status']:
            db_deactivate_todo(id)
            continue # omit inactive connectors
        
        if use_db_cache:
            dbg('Loading '+todo['type']+' todo '+id+" from db", s='todoloading')

            todos = db_get_todolist(todo['id'])
        else:
            dbg('Refreshing '+todo['type']+' todo '+id, s='todoloading')

            try:
                todos = refresh_todolist(todo,False)
            except Exception as e:
                # This will happen if offline

                if conf.debug_level == 3 or 'todoloading' in conf.debug_systems or todo['type'] in conf.debug_systems :
                    raise e

                dbg(notification='Error refreshing '+todo['label'],e=e)
                
                try:
                    todos = db_get_todolist(todo['id'])
                except Exception as e:
                    error_notice('Also Failed to load '+todo['label']+' From cache' ,e=e)
                    todos = {'lists': {}, 'tasks':{}}

        tasks.update(todos['tasks'])
        lists.update(todos['lists'])

    if not use_db_cache:
        reindex()
        conf.todo_sync_time = now()


    lists_cache(lists)

    o = {'lists': lists, 'tasks':tasks}
    return o


def get_system_db_value(field, json = False):
    try:
        o = db_query("SELECT value FROM system WHERE field = ? ",(field,))
        if o:
            o = o[0]['value']
        else:
            dbg('no system_db_value for', field, l=1)

        if json:
            o = json.loads(o)
        return o
    except Exception as e:
        dbg("Error getting",field, 'from system db',e,l=0)


def set_system_db_value(field, value, json = False):
    try:
        if json:
            value = json.dumps(value)

        db_query("REPLACE INTO system(field, value) VALUES(:field, :value)", {'field':field,'value':value})

    except Exception as e:
        dbg("Error setting", field, value, 'in system db',e,l=0)


def get_session_from_system_db():
    try:
        db_session = db_query("SELECT value FROM system WHERE field = 'session'")

        if db_session:
            s = json.loads(db_session[0]['value'])
            s['start_time'] = datetime.strptime(s['start_time'],'%Y-%m-%d %H:%M:%S.%f')
            return s
    except Exception as e:
        dbg("Error in get_session_from_system_db session",e,l=1)


def get_most_recent_list(session = None):
    ''' returns a list object '''
    lists = lists_cache()
    # print(lists.keys())

    try:
        return lists[session['task']['parent_id']]

    except Exception as e:
        pass

    try:
        return lists[get_session_from_system_db()['task']['parent_id']]
        
    except Exception as e:
        pass

    try:
        return lists[db_query("SELECT parent_id FROM sessions WHERE parent_id IN (SELECT id FROM lists WHERE status = 1) ORDER BY sessions.start_time DESC LIMIT 1")[0]['parent_id']]

    except Exception as e:
        return lists.items()[0]



def get_default_list_for_new_tasks():
    # if conf.user['default_list_for_new_tasks'] != 'Most recently used list':
    #     try:

    # List that was last added to

    return get_most_recent_list()


def choose_from_lists(callback, selected_list_id = None, session = None, accepts_tasks = True, show_todolist_headers = True, truncate_labels_to_chars = 100):
    ''' Returns a Gtk.ScrolledWindow widget with radio buttons'''

    # TODO: consider using TreeView https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreeView.html#Gtk.TreeView 

    # get last used list
    if not selected_list_id:
        selected_list_id = get_most_recent_list(session = None)

    box = Gtk.VBox()
    box.set_spacing(8)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled_window.set_propagate_natural_height(True)
    # scrolled_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
    scrolled_window.add(box)

    lists = db_query("SELECT lists.*, (SELECT start_time FROM sessions WHERE todolist = lists.todolist ORDER BY start_time DESC  LIMIT 1 ) as last_session_on_todo FROM lists WHERE status = '1' ORDER BY last_session_on_todo DESC, CASE WHEN parent_id IS NULL THEN 1 ELSE 2 END, extended_label ASC ", None, 'id')    
    
    r_button = None
    todolist_id = None

    for id, l in lists.items():
        try:
            l = proc_db_item(l)
            if len(l['label']) > truncate_labels_to_chars:
                l['label'] = l['label'][:truncate_labels_to_chars] + '…'
            
            nested_list_count = l['extended_label'].count(' > ')

            label = f'{" · " * nested_list_count}' + GLib.markup_escape_text(l['label'])

            if todolist_id != l['todolist']:
                todolist_id = l['todolist']
                if show_todolist_headers:
                    label = "<b>" + label + "</b>"
                    if r_button:
                        r_button.set_margin_bottom(20)
                else:
                    continue

            label_widget = Gtk.Label()
            label_widget.set_halign(Gtk.Align.START)
            label_widget.set_markup(label)
            
            if accepts_tasks and l['data']['accepts_tasks'] == False:
                label_widget.set_markup('   '+label)
                box.add(label_widget)

            else:
                r_button = Gtk.RadioButton(group=r_button)
                r_button.add(label_widget)

                if l['id'] == selected_list_id:
                    r_button.set_active(True)

                r_button.connect("toggled", callback, l) 
                box.add(r_button)

        except Exception as e:
            dbg('Exception adding to choose_from_lists list', l, e=e, l=0)

    # TODO: allow a height argument to account for other things that require space, and possibly a global screen height value?

    # Optimize the height, 27px per item with max of 700 px and a min of 50
    height = max(50,min(500, (len(lists) * 27))) 
    scrolled_window.set_size_request(-1, height)

    return scrolled_window


def add_todos_to_menu(target_menu = None, menu_tasks = None, list_menus = None, activate_callback = None, use_db_cache = True):

    todos = get_todolists(use_db_cache)

    lists = todos['lists']  
    tasks = todos['tasks']

    # print('Add tasks to menu:')
    # print('refreshed lists',json.dumps(lists, indent=4))
    # print(json.dumps(tasks, indent=4))

    list_menu_items = {}
    priority_tasks = {}

    if conf.user['display_todolist_as_top_level_list'] == 'always':
        toplevel_todos = True
    elif conf.user['display_todolist_as_top_level_list'] == 'never':
        toplevel_todos = False
    else:
        # Count top level lists and nest if to many 
        toplevel_count = 0

        # items = lists
        items = lists | tasks
        for id, i in items.items():
            if i['status'] == 1 and i['parent_id'] == i['todolist']:
                toplevel_count += 1
            elif 'priority' in i and i['priority']:
                # count priority tasks
                toplevel_count += 1

        dbg('toplevel_count',toplevel_count,s='menu')


        if toplevel_count > conf.user['max_top_level_menu_items']:
            toplevel_todos = True
        else:
            toplevel_todos = False
    
    # separator after priority tasks
    target_menu.prepend(Gtk.SeparatorMenuItem.new())

    # Create menu for each list 
    for list_id, l in lists.items():
        if l['status'] != 1:
            continue

        if not toplevel_todos and l['id'] == l['todolist']:
            continue

        list_menus[list_id] = Gtk.Menu() # the sub_list that items get added to
        list_menu_items[list_id] = Gtk.MenuItem.new_with_label(lists[list_id]['label']) # the "item" that gets added 
        list_menu_items[list_id].set_submenu(list_menus[list_id])

    # Add each list to parents (sub_menus)
    for list_id, l in lists.items():
        if l['status'] == 1:

            try:

                if not toplevel_todos and l['id'] == l['todolist']:
                    continue
                
                if 'priority' in l and l['priority']:
                    target_menu.prepend(list_menu_items[list_id])
                elif (toplevel_todos and l['id'] == l['todolist']) or (not toplevel_todos and l['parent_id'] == l['todolist']):
                    target_menu.append(list_menu_items[list_id])
                else:
                    list_menus[l['parent_id']].append(list_menu_items[list_id])
            
            except Exception as e:
                dbg('Error adding list to menu',l['extended_label'],e=e,l=0,s='menu')



    for id, t in tasks.items():
        if t['status'] == 1:

            # Truncate excessively long task labels 
            if len(t['label']) > 60:
                t['label'] = t['label'][:60]+"..." 

            menu_tasks[t['id']] = Gtk.MenuItem.new_with_label(str(t['label']))
            menu_tasks[t['id']].connect("activate", activate_callback, t)


            if 'priority' in t and t['priority'] > 0 and ('priority' not in lists[t['parent_id']] or lists[t['parent_id']]['priority'] in [0,None]):
                # Hoist priority tasks, in correct order
                priority_tasks[t['id']] = t['priority']

            elif not t['parent_id'] or t['parent_id'] not in list_menus:
                target_menu.append(menu_tasks[t['id']])
            else:
                # print("add "+t['label']+" to sub menu "+t['parent_label'] )
                list_menus[t['parent_id']].append(menu_tasks[t['id']])


    # Sort and add priority tasks
    if priority_tasks:

        priority_tasks = dict(sorted(priority_tasks.items(), key=lambda item: item[1], reverse=True))
        for t_id in priority_tasks:
            target_menu.prepend(menu_tasks[t_id])

    
    # Ugly (but effectively?) remove empty lists
    for key, menuitem in list_menu_items.items():
        if len(menuitem.get_children()) == 0:
            dbg("remove empty list", lists[key]['label'],s="menu")
            menuitem.destroy()


    # Do it again to remove upper level empties!
    for key, menuitem in list_menu_items.items():
        if len(menuitem.get_children()) == 0:
            dbg("remove empty list", lists[key]['label'],s="menu")
            menuitem.destroy()

    target_menu.show_all()


def datetime_minus_calendar_unit(unit = 'days', num = 1, ref_date = None):
    ''' returns a datetime for the start of the unit num units ago (from the optional ref_date) 
    unit can be days, weeks, months, or years (plural or singular)
    ''' 

    num = num - 1 

    if not ref_date:
        ref_date = start_of_day()

    if unit in ['day','days']:
        o = ref_date - timedelta(days=num) 
    elif unit in ['week','weeks']:
        o = ref_date - timedelta(days=ref_date.weekday())
        if num > 0: o = o + relativedelta(dt1= o, weeks= - num)
    elif unit in ['month','months']:
        o = ref_date.replace(day=1)
        if num > 0: o = o + relativedelta(dt1= o, months= - num)
    elif unit in ['year','years']:
        o = ref_date.replace(month=1,day=1)
        if num > 0: o = o + relativedelta(dt1= o, years= - num)

    return o

def get_time_target_data(i, item_type = 'tasks'):
    ''' returns time target data, if any, for the SPECIFIC item (not it's list). If none set returns False '''
    if i['id'] in conf.user['time_targets'][item_type]:
        return conf.user['time_targets'][item_type][i['id']]
    else:
        return False

def check_time_target(i,item_type = 'tasks', min_max_type = None):

    ''' No target returns False 
     max or min returns float of target minus sessions ''' 

    # Backward compatibility 
    if item_type == 'task': item_type = 'tasks'
    if item_type == 'list': item_type = 'lists'

    ballance = False

    if i['id'] in conf.user['time_targets'][item_type]:
        t = conf.user['time_targets'][item_type][i['id']]
    elif i['parent_id'] in conf.user['time_targets']['lists']:
        # TODO: make this infinitely recursive using get lists_for_task
        t = conf.user['time_targets']['lists'][i['parent_id']]
    else:
        dbg(str(i['label']) + " check_time_target no applicable target:", s='targets', l=3 )
        return False
        
    if t['status'] == False:
        dbg(str(i['label']) + " check_time_target: target is inactive", s='targets', l=3 )
        return False
    
    if not min_max_type or t['type'] == min_max_type:
        target_start = datetime_minus_calendar_unit(t['within_unit'],t['within_value'])

        ballance = t['value'] - get_total_time(i['id'],item_type, target_start, None, "get_minutes")

        dbg(i['label'] + " check_time_target ballance:" + str(ballance), s='targets', l=2 )
        return ballance
        
    dbg(i['label'] + min_max_type + " check_time_target no applicable min_max_type target:", s='targets', l=3 )

    return False


def hours_search_timeframes(frame_name = None):
    ''' returns a tuple with start and end time for given frame (if one is provided) or a dict of frame_options. 
    '''

    default = "all time"

    frames = {
        'today':(datetime_minus_calendar_unit('day',1),now()),
        'yesterday':(datetime_minus_calendar_unit('day',2),datetime_minus_calendar_unit('day',1)),
        'this week':(datetime_minus_calendar_unit('week',1),now()),
        'last week':(datetime_minus_calendar_unit('week',2),datetime_minus_calendar_unit('week',1)),
        '7 days':(datetime_minus_calendar_unit('days',7),now()),
        'this month':(datetime_minus_calendar_unit('month',1),now()),
        'last month':(datetime_minus_calendar_unit('month',2),datetime_minus_calendar_unit('month',1)),
        '30 days':(datetime_minus_calendar_unit('days',30),now()),
        'this year':(datetime_minus_calendar_unit('year',1),now()),
        'last year':(datetime_minus_calendar_unit('year',2),datetime_minus_calendar_unit('year',1)),
        '365 days':(datetime_minus_calendar_unit('days',365),now()),
        'all time':(start_of_day().replace(year=1988,month=1,day=1),now()),
    }

    if frame_name:
        if frame_name in frames:
            return frames[frame_name]
        else:
            error_notice('invalid sessions_search_frame'+str(frame_name))
            return frames[default]

    else:
        return frames


def sessions_timeframe_sql():

    timeframe = hours_search_timeframes(conf.user['hours_search_timeframe'])

    timeframe_sql = " sessions.start_time > '"+timeframe[0].strftime("%Y-%m-%d %H:%M:%S")+"' AND sessions.start_time < '"+timeframe[1].strftime("%Y-%m-%d %H:%M:%S")+"' " 

    # dbg('sessions_timeframe_sql',timeframe_sql,s='search')
    return timeframe_sql