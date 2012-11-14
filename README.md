Introduction
============

Strava is a mobile app and site designed for cyclists to track where they ride
and how they perform.  Data is typically captured on the mobile app and
uploaded to Strava after the ride is completed.  Plot My Ride allows strava
users to visualize their performance and compare it to other riders.
Specifically, riders can view a scatter plot of their average speed by the
grade of the segments they have completed.  This scatter plot is rendered over
a scatter plot of everybody else's average speed and grade.

Usage
=====

Navigate your browser to:

http://people.ischool.berkeley.edu/~bcavagnolo/plotmyride/html/login.html

...and expect the login page to appear.  Login with your strava user name, and
expect your scatter plot to appear.  Now you can:

-- Mouse over the scatter plot to reveal your performance on various segments
   of various grade.

-- Mouse over a region on the plot to see a box plot summarizing everybody's
   performance at that grade.

-- Tune the Hour of Day slide in the side bar to focus in on segments that you
   completed during specific times.

-- Logout by clicking the logout link in the sidebar and expect to be
   redirected to the login page.

Team
====

David Greis: logo, layout, time-of-day slider, offline data analysis

JT Huang: scatter plot, box plots, mouse-over features

Brian Cavagnolo: back-end data collection, integration, login/logout flow

Technologies
============
    html/css
	javascript/jquery
    d3/svg

Preparing the data
==================

INTRO

Plot My Ride uses data from strava.  The basic data element is an effort.  An
effort is a specific athlete's performance data (e.g., average speed, max
speed, etc) on a particular segment.  A segment is a length of road defined by
you and other strava users as interesting.  It might be a specific time trial
route, or a particular climb, or a particular descent.  This data is available
using the strava API which is (mostly) documented here:

https://stravasite-main.pbworks.com/w/browse/#view=ViewMainFolderNewGuiGallery

BIKE DATA

To populate an sqlite database with a particular user's data, use the
getStrava.py script like so:

  $ python getStrava.py createdb
  $ python getStrava.py fetch username

This second command takes a very very long time to run, and may have to be
restarted if (er, when) strava takes down their servers for maintenance...or
when they crash...or whatever.  The reason is that there is no way to
bulk-download the entire strava dataset, so the efforts of you and all of the
athletes who have completed the efforts are downloaded one by one.

WEATHER

The weather data comes from weather stations all around the world.  Historical
weather info from these stations is avaialable online from the National Oceanic
and Atmospheric Administration (NOAA).  The specific locations of the weather
stations are here:

ftp://ftp.ncdc.noaa.gov/pub/data/inventories/ISH-HISTORY.TXT

You'll have to grab this file and distill it down to just the usaf, wban, lat,
and lon columns and save it to a CSV file called stations.csv for this next
step, which adds the stations table to your sqlite db:

   sqlite> create table stations_import (usaf integer, wban integer, lat float, lon float);
   sqlite> create table stations (id integer primary key, usaf integer, wban integer, lat float, lon float);
   sqlite> .separator ","
   sqlite> .import stations.csv stations_import
   sqlite> insert into stations (usaf, wban, lat, lon) select * from stations_import;
   sqlite> drop table stations_import;

Now that you have the stations table, you can find the nearest weather station
to each segment using the getStrava.py tool again:

   $ python getStrava.py fetchGeo
   $ python getStrava.py addWeatherStation

You'll only want to grab weather data for the time period of interest and for
the weather stations of interest.  You can determine these like so:

   sqlite> select MAX(startDate), MIN(startDate) from efforts;
   sqlite> select DISTINCT station_id,s.usaf,s.wban from segments JOIN stations AS s ON s.id=segments.station_id ORDER BY s.usaf;

Armed with this information, you can now head to the following URL and fill out
the form to get the data you need:

http://hurricane.ncdc.noaa.gov/pls/plclimprod/cdomain.abbrev2id

You'll eventually get a big text file back.  I'll leave it to you to figure out
how to pare this down to the only columns we need: USAF, WBAN, DATETIME
(originally called YR--MODAHRMN), TEMP, MAX, MIN.  Now you can import it to the
weather table like so:

   sqlite> create table weather_import (USAF integer, WBAN integer, DATETIME text, TMP integer, MAX integer, MIN integer);
   sqlite> .import weather.csv weather_import
   sqlite> delete from weather_import where DATETIME='DATETIME';
   sqlite> create table weather (usaf integer, wban integer, date datetime, temp integer, maxtemp integer, mintemp integer);
   sqlite> insert into weather (usaf, wban, date, temp, maxtemp, mintemp) select USAF,WBAN,datetime(substr(DATETIME,1,4)||'-'||substr(DATETIME,5,2)||'-'||substr(DATETIME,7,2)||' '||substr(DATETIME,9,2)||':'||substr(DATETIME,11,2)),TMP,MAX,MIN from weather_import;

Now you can populate the temp column in the efforts table:

   $ python getStrava.py addWeather

Note that this command takes a while because the date matching is a bit
complicated.

PREPARING DATA

The application requires two data files to work: strava.csv and athletes.csv.
You must generate these and place them in the root directory:

   sqlite> .mode csv
   sqlite> .header on
   sqlite> .out athletes.csv
   sqlite> select * from athletes;
   sqlite> .out strava.csv
   sqlite> select * from efforts as e JOIN athletes as a ON a.id=e.athlete_id JOIN segments as s ON s.id=e.segment_id;

Quirks and known issues
=======================

1. The actual data that is served up is static.  That is, it is not fetched
   from strava when the page is loaded.  The reason is that it takes a very
   long time to gather the strava data for everyone.  So effectively, this is a
   visualization demo, not a full-fledged site.

2. The time of day data is not corrected by timezone before being presented.

3. Users are not actually authenticated with strava.  In fact, strava freely
   shares all of the data presented here with their deprecated v1 API.  So we
   just ensure that the specified username exists so that some interesting data
   can be shown, and the password is not checked against anything.

4. Tested on Chrome.  Firefox has some layout problems and doesn't load custom
   font correctly.

5. The strava.csv file can get very large for riders that ride in popular areas
   or who have completed many rides.  This problem can be addressed in many
   ways.  One way is that the the crowd data can be based on a sample instead
   of the full population.  Data streaming and compression are a couple of
   others.  At this time, none of these techniques are implemented.

6. The progress meter does not advance while the data is rendered.  This is
   because the rendering blocks the CPU.  The solution is to break up the
   rendering into smaller chunks.  But this is not implemented yet.
