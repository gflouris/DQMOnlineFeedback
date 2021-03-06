#!/usr/bin/env python
from DQMInterface import *
from mimeemail import *
import sqlite3
import datetime
import time
from utils import WriteOut

conn = sqlite3.connect('logbook.db')
dbcursor = conn.cursor()
#try:
#dbcursor.execute('SELECT EXISTS(SELECT 1 FROM alarms WHERE id=1 )')
# except sqlite3.Error as exerror:
#     if(exerror):
#         dbcursor.execute('''CREATE TABLE alarms(id integer PRIMARY KEY,date, run int, lumi int, dead_value int, DataPresent)''')
#         dbcursor.execute('''CREATE TABLE processed_runs(id integer PRIMARY KEY,date, run int, lumi int, dead_value int, DataPresent)''')
try:
    dbcursor.execute('SELECT EXISTS(SELECT 1 FROM alarms WHERE id=1 )')
    dbcursor.execute('SELECT EXISTS(SELECT 1 FROM processed_runs WHERE id=1 )')
except sqlite3.Error as exerror:
    if(exerror):
        WriteOut("Creating tables")
        dbcursor.execute('''CREATE TABLE alarms(id integer PRIMARY KEY,date, run int, lumi int, dead_value int, DataPresent)''')
        dbcursor.execute('''CREATE TABLE processed_runs(id integer PRIMARY KEY,date, run int, lumi int, dead_value int, DataPresent)''')

serverurl = 'https://cmsweb.cern.ch/dqm/online'


def PrintAlarm(DQMMon):

        WriteOut("=========================================")
        WriteOut(DQMMon.runinfo['run'])
        WriteOut(DQMMon.runinfo['lumi'])
        WriteOut(DQMMon.runinfo['beamMode'])
        WriteOut(DQMMon.runinfo['run_type'])
        WriteOut(DQMMon.dead_value)
        WriteOut("isDataPresent "+str(DQMMon.isDataPresent))
        WriteOut("=========================================")




DQMMon = DQMInterface(serverurl, 0) #Run=0 it takes the latest run

if(DQMMon.onlinePublishing):

    #DQMMon.refresh()
    DQMMon.getRunInfo()
    DQMMon.getdeadRocTrendLayer_1()
    DQMMon.getIsDataPresent()
    #PrintAlarm(DQMMon)

    if(DQMMon.runinfo['lumi'] < 4 or DQMMon.runinfo['beamMode']!='stable' or DQMMon.runinfo['run_type']!='pp_run'):
        pass

    else:

        dbcursor.execute('SELECT EXISTS(SELECT 1 FROM processed_runs WHERE run="%s" )' % DQMMon.runinfo['run'])
        run_processed, = dbcursor.fetchone()
        time.sleep(1)
        if(run_processed!=1):
            dbcursor.execute("INSERT INTO processed_runs(date, run, lumi, dead_value, DataPresent) VALUES (?, ? , ? , ?, ?);",(datetime.datetime.now(), DQMMon.runinfo['run'], DQMMon.runinfo['lumi'], DQMMon.dead_value, DQMMon.isDataPresent))
            conn.commit()
            time.sleep(1)

        if( (DQMMon.dead_value>70 or DQMMon.isDataPresent==False)):
            #Run is written in db only if the sms/email has been sent
            dbcursor.execute('SELECT EXISTS(SELECT 1 FROM alarms WHERE run="%s" )' % DQMMon.runinfo['run'])
            alarm_handled, = dbcursor.fetchone()
            time.sleep(1)

            if(alarm_handled!=1):
                PrintAlarm(DQMMon)

                dbcursor.execute("INSERT INTO alarms(date, run, lumi, dead_value, DataPresent) VALUES (?, ? , ? , ?, ?);",(datetime.datetime.now(), DQMMon.runinfo['run'], DQMMon.runinfo['lumi'], DQMMon.dead_value, DQMMon.isDataPresent))
                conn.commit()
                time.sleep(1)
                send_mail(DQMMon)
                send_mail(DQMMon, isSMS=True) #sendsms
