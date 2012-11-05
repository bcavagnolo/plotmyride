import urllib2, urllib, sys, getpass, json
import sqlite3
import datetime, time

STRAVA_URL_V1 = 'http://www.strava.com/api/v1/'
STRAVA_URL_V2 = 'https://www.strava.com/api/v2/'
DBFILE = 'strava.db'

def add_athlete(c, a):
    c.execute("insert or replace into athletes values (?, ?, ?)",
              (a['id'], a['name'], a['username']))

def add_effort(c, e):
    c.execute("insert or replace into efforts values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (e['id'], e['athlete']['id'], e['segment']['id'], e['ride']['id'],
               e['startDate'], e['elapsedTime'], e['movingTime'], e['distance'],
               e['averageSpeed'], e['maximumSpeed'], e['elevationGain']))

def add_segment(c, s):
    c.execute("insert or replace into segments values (?, ?, ?, ?, ?, ?)",
              (s['id'], s['name'], s['distance'], s['elevationGain'],
               s['averageGrade'], s['climbCategory']))

def get_segment_efforts(id, start=0, end=0):
    # Thanks to
    # http://marc.durdin.net/2011/11/working-around-limitations-in-stravas.html
    # for this approach.
    if start == 0 and end == 0:
        start = int(time.mktime(datetime.datetime.strptime("01/01/2010", "%d/%m/%Y").timetuple()))
        end = int(time.mktime(datetime.datetime.today().timetuple()))

    if start >= end:
        return []

    startString = datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%d')
    endString = datetime.datetime.fromtimestamp(end).strftime('%Y-%m-%d')

    f = urllib2.urlopen(STRAVA_URL_V1 + 'segments/' + str(id) + '/efforts' +
                        '?startDate=' + startString + '&endDate=' + endString)
    all_efforts = json.loads(f.read())['efforts']
    numEfforts = len(all_efforts)
    if numEfforts == 50:
        mid = round((start + end)/2)
        firstEfforts = get_segment_efforts(id, start, mid)
        secondEfforts = get_segment_efforts(id, mid, end)
        if not firstEfforts:
            return secondEfforts
        if not secondEfforts:
            return firstEfforts
        return firstEfforts + secondEfforts
    return all_efforts

def fetchData(email=None, pw=None, id=None):

    if id == None:
        args = {
            'email': email,
            'password': pw,
            }
        f = urllib2.urlopen(STRAVA_URL_V2 + 'authentication/login',
                            urllib.urlencode(args))
        id = json.loads(f.read())['athlete']['id']
        print 'Got id ' + str(id) + ' for user ' + email

    # now we can get the users rides
    f = urllib2.urlopen(STRAVA_URL_V1 + 'rides?athleteId=' + str(id))
    rides = json.loads(f.read())['rides']

    # and now we need all the efforts for this athlete
    efforts = []
    conn = sqlite3.connect(DBFILE)
    c = conn.cursor()
    added_self = False
    for r in rides:
        print 'Fetching data for ride "' + r['name'] + '"'
        f = urllib2.urlopen(STRAVA_URL_V1 + 'rides/' + str(r['id']))
        rr = json.loads(f.read())['ride']
        c.execute("insert or replace into rides values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (r['id'], rr['startDate'], rr['elapsedTime'], rr['movingTime'],
                   rr['distance'], rr['averageSpeed'], rr['maximumSpeed'],
                   rr['elevationGain'], rr['location'], rr['name']))
        f = urllib2.urlopen(STRAVA_URL_V1 + 'rides/' + str(r['id']) + '/efforts')
        efforts = json.loads(f.read())['efforts']

        for e in efforts:
            print '\t' + e['segment']['name']
            f = urllib2.urlopen(STRAVA_URL_V1 + 'efforts/' + str(e['id']))
            ee = json.loads(f.read())['effort']
            if not added_self:
                a = ee['athlete']
                c.execute("insert or replace into athletes values (?, ?, ?)",
                          (a['id'], a['name'], a['username']))
                added_self = True
            ee['id'] = e['id']
            add_effort(c, ee)
            f = urllib2.urlopen(STRAVA_URL_V1 + 'segments/' + str(e['segment']['id']))
            s = json.loads(f.read())['segment']
            add_segment(c, s)

            try:
                all_efforts = get_segment_efforts(e['segment']['id'])
                print "\t\tfetching " + str(len(all_efforts)) + " efforts"
                for ee in all_efforts:
                    f = urllib2.urlopen(STRAVA_URL_V1 + 'efforts/' + str(ee['id']))
                    eee = json.loads(f.read())['effort']
                    a = eee['athlete']
                    add_effort(c, eee)
                    add_athlete(c, a)
            except urllib2.HTTPError as err:
                print '\t\t' + 'WARNING: Failed to find efforts for segment ' + str(e['segment']['name'])
                print '\t\t' + str(err)

    conn.commit()

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print 'usage: ' + sys.argv[0] + ' <cmd> <args>'
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'fetch':
        if len(sys.argv) < 3:
            print 'usage: ' + sys.argv[0] + ' fetch <email|uid>'
            sys.exit(1)
        if '@' in sys.argv[2]:
            fetchData(email=sys.argv[2], pw=getpass.getpass())
        else:
            fetchData(id=sys.argv[2])

    elif cmd == 'createdb':
        conn = sqlite3.connect(DBFILE)
        c = conn.cursor()
        c.execute('CREATE TABLE athletes (id int, name text, username text, PRIMARY KEY(id))')
        c.execute('''CREATE TABLE rides (id int, startDate date, elapsedTime float,
                    movingTime float, distance float, averageSpeed float,
                    maximumSpeed float, elevationGain float, location text, name text,
                    PRIMARY KEY(id))''')
        c.execute('''CREATE TABLE efforts (id int, athlete_id int, segment_id int, ride_id int,
                     startDate date, elapsedTime float, movingTime float,
                     distance float, averageSpeed float,
                     maximumSpeed float, elevationGain float, PRIMARY KEY(id))''')
        c.execute('''CREATE TABLE segments (id int, name text, distance float,
                     elevationGain float, averageGrade float,
                     climbCategory int, PRIMARY KEY(id))''')
        conn.commit()

    else:
        print 'Error: unknown command ' + cmd
        sys.exit(1)
