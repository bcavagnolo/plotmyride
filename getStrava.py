import urllib2, urllib, sys, getpass, json

STRAVA_URL_V1 = 'http://www.strava.com/api/v1/'
STRAVA_URL_V2 = 'https://www.strava.com/api/v2/'

def fetchData(email, pw):
    # First we need the strava athlete id
    args = {
        'email': email,
        'password': pw,
        }
    f = urllib2.urlopen(STRAVA_URL_V2 + 'authentication/login',
                        urllib.urlencode(args))
    id = json.loads(f.read())['athlete']['id']
    print 'Got id ' + str(id) + ' for user ' + sys.argv[1]
    # now we can get the users rides
    f = urllib2.urlopen(STRAVA_URL_V1 + 'rides?athleteId=' + str(id))
    rides = json.loads(f.read())['rides']

    # and now we need all the efforts for this athlete
    efforts = []
    for r in rides:
        print 'Fetching data for ride "' + r['name'] + '"'
        f = urllib2.urlopen(STRAVA_URL_V1 + 'rides/' + str(r['id']) + '/efforts')
        efforts = json.loads(f.read())['efforts']
        for e in efforts:
            print '\t' + e['segment']['name']
            try:
                f = urllib2.urlopen(STRAVA_URL_V1 + 'segments/' + str(e['segment']['id']) + '/efforts')
                all_efforts = json.loads(f.read())['efforts']
            except urllib2.HTTPError as err:
                print '\t\t' + 'WARNING: Failed to find efforts for segment ' + str(e['segment']['name'])
                print '\t\t' + str(err)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print 'usage: ' + sys.argv[0] + ' <cmd> <args>'
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'fetch':
        if len(sys.argv) < 3:
            print 'usage: ' + sys.argv[0] + ' fetch email'
            sys.exit(1)
        fetchData(sys.argv[2], getpass.getpass())
    else:
        print 'Error: unknown command ' + cmd
        sys.exit(1)
