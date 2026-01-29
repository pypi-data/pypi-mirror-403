import conf
from utils import * 
# from pkg_resources import parse_version


def do_upgrades(app):
    db_schema_version = get_system_db_value('db_schema_version')

    if db_schema_version == '0.2':
                
        db_query("ALTER TABLE lists DROP COLUMN status")
        db_query("ALTER TABLE tasks DROP COLUMN status")

        db_query("ALTER TABLE lists ADD COLUMN status INTEGER DEFAULT 1")
        db_query("ALTER TABLE tasks ADD COLUMN status INTEGER DEFAULT 1")

        db_query("REPLACE INTO system(field, value) VALUES('db_schema_version', '0.3')")
    
        db_schema_version = '0.3'


    if db_schema_version == '0.3':
        db_query("ALTER TABLE sessions ADD COLUMN timetracker TEXT")
        db_query("ALTER TABLE sessions ADD COLUMN notes TEXT")
        db_query("REPLACE INTO system(field, value) VALUES('db_schema_version', '0.4')")
        print('adding timetracker column to session table')

        for todolist_id, todo in conf.user['todolists'].items():
            db_query("UPDATE sessions SET timetracker = ? WHERE todolist = ?",(todo['timetracker'],todolist_id) )

        db_schema_version = '0.4'

    if db_schema_version == '0.4':
        dbg('Schema Update from', db_schema_version, 'to 0.5',l=-1)

        print('Adding priority column to session table')

        db_query("ALTER TABLE sessions ADD COLUMN priority INTEGER DEFAULT 0")

        for session in db_query("SELECT DISTINCT task_id, extended_label FROM sessions"):
            t = db_get_item_by_id(session['task_id'],dgb_error_level_for_failure=3)
            if t and t['priority'] > 0:
                print("setting",session['extended_label']," session priority to ",t['priority'] )

                db_query("UPDATE sessions SET priority = ? WHERE task_id = ?",(t['priority'],session['task_id']))

        print("Total hours priority sessions",round(divide(db_query("SELECT SUM(duration) as total FROM sessions WHERE priority > 0")[0]['total'],3600),2))
        db_query("REPLACE INTO system(field, value) VALUES('db_schema_version', '0.5')")

        db_schema_version = '0.5'

    if db_schema_version == '0.5':
        dbg('Schema Update from', db_schema_version, 'to 0.5.6',l=-1)

        from install import copy_desktop_integration_files
        copy_desktop_integration_files()

        db_schema_version = "0.5.6"
        set_system_db_value("db_schema_version",db_schema_version)

    # if db_schema_version == 0.5:
    #     db_query("ALTER TABLE tasks ADD COLUMN tags TEXT DEFAULT '{}'")
    #     db_query("REPLACE INTO system(field, value) VALUES('db_schema_version', '0.5')")
    #     db_schema_version = 0.6


    dbg('db_schema_version updated to', db_schema_version,s='db')













# update time_target format 
# for id, tt in user['time_targets']['lists'].items():
#     if 'within_value' not in tt:
#         print("Updating time target to new format ",tt)
#         tt['within_value'] = tt['num_days']
#         tt['within_unit'] = 'days'
#         print(tt)
#     if 'status' not in tt:
#         tt['status'] = True

        
# for id, tt in user['time_targets']['tasks'].items():
#     if 'within_value' not in tt:
#         print("Updating time target to new format ",tt)
#         tt['within_value'] = tt['num_days']
#         tt['within_unit'] = 'days'
#         print(tt)
#     if 'status' not in tt:
#         tt['status'] = True
