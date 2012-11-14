import urllib2, urllib, sys, getpass, json
import sqlite3
import datetime, time
import math

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

def get_segment_efforts(id, offset=0):
    f = urllib2.urlopen(STRAVA_URL_V1 + 'segments/' + str(id) + '/efforts' +
                        '?offset=' + str(offset))
    all_efforts = json.loads(f.read())['efforts']
    numEfforts = len(all_efforts)
    if numEfforts < 50:
        return all_efforts
    else:
        return all_efforts + get_segment_efforts(id, offset + 50)

def _fetchGeo(conn):
    c = conn.cursor()
    for s in c.execute('SELECT id FROM segments'):
        if s[0] == 'id':
            continue
        print "Fetching geography of segment " + str(s[0])
        url = STRAVA_URL_V1 + 'stream/segments/' + str(s[0]);
        f = urllib2.urlopen(url)
        latlng = json.loads(f.read())['latlng']
        # take the median point on the ride and use that as the single lat long
        # to represent the ride.  We could be more sophiticated here
        ll = latlng[len(latlng)/2]
        d = conn.cursor()
        d.execute("UPDATE segments SET lat=?, lon=? WHERE id=?",
                  (ll[0], ll[1], s[0]))

def fetchGeo():
    conn = sqlite3.connect(DBFILE)
    try:
        _fetchGeo(conn)
    finally:
        conn.commit()

def _fetchData(conn, email=None, pw=None, id=None):

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
                    cursor = c.execute('SELECT id FROM efforts WHERE id=?', (ee['id'],))
                    if cursor.fetchone():
                        continue
                    f = urllib2.urlopen(STRAVA_URL_V1 + 'efforts/' + str(ee['id']))
                    eee = json.loads(f.read())['effort']
                    a = eee['athlete']
                    add_effort(c, eee)
                    add_athlete(c, a)
            except urllib2.HTTPError as err:
                print '\t\t' + 'WARNING: Failed to find efforts for segment ' + str(e['segment']['name'])
                print '\t\t' + str(err)

def fetchData(email=None, pw=None, id=None):
    conn = sqlite3.connect(DBFILE)
    try:
        _fetchData(conn, email, pw, id)
    finally:
        conn.commit()


# code from:
# http://www.johndcook.com/python_longitude_latitude.html
def distance_on_unit_sphere(lat1, long1, lat2, long2):

    # Convert latitude and longitude to 
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0
        
    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
        
    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
        
    # Compute spherical distance from spherical coordinates.
        
    # For two locations in spherical coordinates 
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) = 
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length

    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos( cos )

    # Remember to multiply arc by the radius of the earth 
    # in your favorite set of units to get length.
    return arc*6371009

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
        c.execute('''ALTER TABLE segments ADD COLUMN lat float''')
        c.execute('''ALTER TABLE segments ADD COLUMN lon float''')
        c.execute('''ALTER TABLE segments ADD COLUMN station_id''')
        conn.commit()

    if cmd == 'fetchGeo':
        fetchGeo()

    if cmd == 'addWeatherStation':
        conn = sqlite3.connect(DBFILE)
        c = conn.cursor()

        stations = []
        for s in c.execute('SELECT id,lat,lon FROM stations'):
            stations.append(s)

        # Now we have a shameful O(n^2) distance calculation...
        for seg in c.execute('SELECT id,lat,lon FROM segments'):
            print "Finding nearest station for segment",seg[0]
            min_d = None
            nearest_station = None
            for s in stations:
                d = distance_on_unit_sphere(float(s[1]), float(s[2]),
                                            float(seg[1]), float(seg[2]))
                if not min_d or d < min_d:
                    min_d = d
                    nearest_station = s

            d = conn.cursor()
            d.execute("UPDATE segments SET station_id=? WHERE id=?",
                      (nearest_station[0], seg[0]))
        conn.commit()

    else:
        print 'Error: unknown command ' + cmd
        sys.exit(1)
