import urllib2, urllib, sys, getpass, json
import sqlite3

STRAVA_URL_V1 = 'http://www.strava.com/api/v1/'
STRAVA_URL_V2 = 'https://www.strava.com/api/v2/'
DBFILE = 'strava.db'

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
            c.execute("insert or replace into efforts values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (e['id'], ee['athlete']['id'], e['segment']['id'], r['id'], ee['startDate'],
                       ee['elapsedTime'], ee['movingTime'], ee['distance'],
                       ee['averageSpeed'], ee['maximumSpeed'], ee['elevationGain']))

            f = urllib2.urlopen(STRAVA_URL_V1 + 'segments/' + str(e['segment']['id']))
            s = json.loads(f.read())['segment']
            c.execute("insert or replace into segments values (?, ?, ?, ?, ?, ?)",
                      (s['id'], s['name'], s['distance'], s['elevationGain'],
                       s['averageGrade'], s['climbCategory']))

            try:
                # TODO: This only gets the first 50 efforts.  To get all of the
                # efforts, we'll have to use start and end dates (e.g.,
                # ?startDate=2012-10-29&endDate=2012-10-30)
                f = urllib2.urlopen(STRAVA_URL_V1 + 'segments/' + str(e['segment']['id']) + '/efforts')
                all_efforts = json.loads(f.read())['efforts']

                for ee in all_efforts:
                    f = urllib2.urlopen(STRAVA_URL_V1 + 'efforts/' + str(ee['id']))
                    eee = json.loads(f.read())['effort']
                    a = eee['athlete']
                    c.execute("insert or replace into efforts values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                              (ee['id'], ee['athlete']['id'], e['segment']['id'], r['id'], eee['startDate'],
                               eee['elapsedTime'], eee['movingTime'], eee['distance'],
                               eee['averageSpeed'], eee['maximumSpeed'], eee['elevationGain']))
                    c.execute("insert or replace into athletes values (?, ?, ?)",
                              (a['id'], a['name'], a['username']))

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
