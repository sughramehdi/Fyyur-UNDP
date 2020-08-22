# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#


import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.orm import relationship
from sqlalchemy import func

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

ShowDetails = db.Table('ShowDetails',
  db.Column('id', db.Integer, autoincrement=True, primary_key=True), 
  db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True), 
  db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True), 
  db.Column('start_time', db.String, nullable=False))
 
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.String(120))
    seeking_description = db.Column(db.String(120))
    artists = db.relationship('Artist', secondary=ShowDetails, backref=db.backref('Venue'))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.String(120))
    seeking_description = db.Column(db.String(120))
    venues = db.relationship('Venue', secondary=ShowDetails, backref=db.backref('Artist'))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
    format = "EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
    format = "EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
  return render_template('pages/home.html')


# ----------------------------------------------------------------------------#
# Venues
# ----------------------------------------------------------------------------#


@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  citydata = db.session.query(Venue.city).distinct().order_by(Venue.state)
  data = [{
    'city': city.city,
    'state': db.session.query(Venue.state).filter_by(city=city).first(),  # make changes here
    'venues': [{
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': (db.session.execute(ShowDetails.select().where(ShowDetails.c.venue_id==venue.id).where(ShowDetails.c.start_time > str(datetime.now())))).rowcount
      } for venue in db.session.query(Venue).filter_by(city=city).all()]
    } for city in citydata]
  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  searchterm = request.form.get('search_term')
  searchresults = Venue.query.filter(Venue.name.ilike('%' + searchterm + '%')).all()
  response={
    "count": Venue.query.filter(Venue.name.ilike('%' + searchterm + '%')).count(),
    "data": [{
      "id": searchresult.id,
      "name": searchresult.name,
      'num_upcoming_shows': (db.session.execute(ShowDetails.select().where(ShowDetails.c.venue_id==searchresult.id).where(ShowDetails.c.start_time > str(datetime.now())))).rowcount
    } for searchresult in searchresults]
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  pastshowdata = db.session.execute(ShowDetails.select().where(ShowDetails.c.venue_id==venue_id).where(ShowDetails.c.start_time < str(datetime.now())))
  upcomingshowdata = db.session.execute(ShowDetails.select().where(ShowDetails.c.venue_id==venue_id).where(ShowDetails.c.start_time > str(datetime.now())))
  venuedata = Venue.query.get(venue_id)
  def convertolist(genres):
    return list(genres.split(' '))
  data={
    "id": venuedata.id,
    "name": venuedata.name,
    "genres": convertolist(venuedata.genres),
    "address": venuedata.address,
    "city": venuedata.city,
    "state": venuedata.state,
    "phone": venuedata.phone,
    "website": venuedata.website,
    "facebook_link": venuedata.facebook_link,
    "seeking_talent": venuedata.seeking_talent,
    "seeking_description": venuedata.seeking_description,
    "image_link": venuedata.image_link,
    "past_shows": [{
      "artist_id": show.artist_id,
      "artist_name": (Artist.query.filter_by(id=show.artist_id).one()).name,
      "artist_image_link": (Artist.query.filter_by(id=show.artist_id).one()).image_link,
      "start_time": show.start_time
    } for show in pastshowdata],
    "upcoming_shows": [{
      "artist_id": show.artist_id,
      "artist_name": (Artist.query.filter_by(id=show.artist_id).one()).name,
      "artist_image_link": (Artist.query.filter_by(id=show.artist_id).one()).image_link,
      "start_time": show.start_time
    } for show in upcomingshowdata],
    "past_shows_count": pastshowdata.rowcount,
    "num_upcoming_shows": upcomingshowdata.rowcount  
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    def removebraces(genre):
      remove = ' '
      return (remove.join(genre))
    data = Venue(
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'],
      address=request.form['address'],
      phone=request.form['phone'],
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      genres=removebraces(request.form.getlist('genres')),
      seeking_talent=request.form['seeking_talent'],
      seeking_description=request.form['seeking_description'],
      website=request.form['website']
    )
    db.session.add(data)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except():
    db.session.rollback()
    flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  finally:
    db.session.close()
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  #flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except():
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return jsonify({'success': True})
  #return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  data=[{
    "id": artist.id,
    "name": artist.name,
  } for artist in artists ]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  searchterm = request.form.get('search_term')
  searchresults = Artist.query.filter(Artist.name.ilike('%' + searchterm + '%')).all()
  response={
    "count": Artist.query.filter(Artist.name.ilike('%' + searchterm + '%')).count(),
    "data": [{
      "id": searchresult.id,
      "name": searchresult.name,
      "num_upcoming_shows": (db.session.execute(ShowDetails.select().where(ShowDetails.c.artist_id==searchresult.id).where(ShowDetails.c.start_time > str(datetime.now())))).rowcount
    } for searchresult in searchresults]
  }  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  pastshowdata = db.session.execute(ShowDetails.select().where(ShowDetails.c.artist_id==artist_id).where(ShowDetails.c.start_time < str(datetime.now())))
  upcomingshowdata = db.session.execute(ShowDetails.select().where(ShowDetails.c.artist_id==artist_id).where(ShowDetails.c.start_time > str(datetime.now())))
  artistdata = Artist.query.get(artist_id)
  def convertolist(genres):
    return list(genres.split(' '))
  data={
    "id": artistdata.id,
    "name": artistdata.name,
    "genres": convertolist(artistdata.genres),
    "city": artistdata.city,
    "state": artistdata.state,
    "phone": artistdata.phone,
    "website": artistdata.website,
    "facebook_link": artistdata.facebook_link,
    "seeking_venue": artistdata.seeking_venue,
    "seeking_description": artistdata.seeking_description,
    "image_link": artistdata.image_link,
    "past_shows": [{
      "venue_id": show.venue_id,
      "venue_name": (Venue.query.filter_by(id=show.venue_id).one()).name,
      "venue_image_link": (Venue.query.filter_by(id=show.venue_id).one()).image_link,
      "start_time": show.start_time
    } for show in pastshowdata],
    "upcoming_shows": [{
      "venue_id": show.venue_id,
      "venue_name": (Venue.query.filter_by(id=show.venue_id).one()).name,
      "venue_image_link": (Venue.query.filter_by(id=show.venue_id).one()).image_link,
      "start_time": show.start_time
    } for show in upcomingshowdata],
    "past_shows_count": pastshowdata.rowcount,
    "num_upcoming_shows": upcomingshowdata.rowcount
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artistdata = Artist.query.get(artist_id)
  def convertolist(genres):
    return list(genres.split(' '))
  artist={
    "id": artistdata.id,
    "name": artistdata.name,
    "genres": convertolist(artistdata.genres),
    "city": artistdata.city,
    "state": artistdata.state,
    "phone": artistdata.phone,
    "facebook_link": artistdata.facebook_link,
    "image_link": artistdata.image_link,
    "website": artistdata.website,
    "seeking_venue": artistdata.seeking_venue,
    "seeking_description": artistdata.seeking_description
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    def removebraces(genre):
      remove = ' '
      return (remove.join(genre))
    data={
      'name' : request.form['name'],
      'city' : request.form['city'],
      'state' : request.form['state'],
      'phone' : request.form['phone'],
      'image_link' : request.form['image_link'],
      'facebook_link' : request.form['facebook_link'],
      'genres' : removebraces(request.form.getlist('genres')),
      'seeking_venue' : request.form['seeking_venue'],
      'seeking_description' : request.form['seeking_description'],
      'website' : request.form['website']
    }
    db.session.query(Artist).filter_by(id=artist_id).update(data)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except():
    db.session.rollback()
    flash('An error occurred. ' + data.name + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venuedata = Venue.query.get(venue_id)
  def convertolist(genres):
    return list(genres.split(' '))
  venue={
    "id": venuedata.id,
    "name": venuedata.name,
    "genres": convertolist(venuedata.genres),
    "address": venuedata.address,
    "city": venuedata.city,
    "state": venuedata.state,
    "phone": venuedata.phone,
    "website": venuedata.website,
    "facebook_link": venuedata.facebook_link,
    "seeking_talent": venuedata.seeking_talent,
    "seeking_description": venuedata.seeking_description,
    "image_link": venuedata.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    def removebraces(genre):
      remove = ' '
      return (remove.join(genre))
    data = {
      'name' : request.form['name'],
      'city' : request.form['city'],
      'state' : request.form['state'],
      'address' : request.form['address'],
      'phone' : request.form['phone'],
      'image_link' : request.form['image_link'],
      'facebook_link' : request.form['facebook_link'],
      'genres' : removebraces(request.form.getlist('genres')),
      'seeking_talent' : request.form['seeking_talent'],
      'seeking_description' : request.form['seeking_description'],
      'website' : request.form['website']
    }
    db.session.query(Venue).filter_by(id=venue_id).update(data)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except():
    db.session.rollback()
    flash('An error occurred. ' + data.name + ' could not be updated.')
  finally:
    db.session.close()
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    def removebraces(genre):
      remove = ' '
      return (remove.join(genre))
    data = Artist(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      genres = removebraces(request.form.getlist('genres')),
      seeking_venue = request.form['seeking_venue'],
      seeking_description = request.form['seeking_description'],
      website = request.form['website']
    )
    db.session.add(data)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except():
    db.session.rollback()
    flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  finally:
    db.session.close()
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  #flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')

# Delete Artist
# ------------------------------------------------------------
@app.route('/artists/<artist_id>/delete', methods=['DELETE'])
def delete_artist(artist_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  error = False
  try:
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
  except():
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return jsonify({'success': True})
  #return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows = db.session.execute(ShowDetails.select())
  data=[{
    "venue_id": show.venue_id,
    "venue_name": (Venue.query.filter_by(id=show.venue_id).one()).name,
    "artist_id": show.artist_id,
    "artist_name": (Artist.query.filter_by(id=show.artist_id).one()).name,
    "artist_image_link": (Artist.query.filter_by(id=show.artist_id).one()).image_link,
    "start_time": show.start_time
  } for show in shows ]
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    data = ShowDetails.insert().values(venue_id = request.form['venue_id'], artist_id = request.form['artist_id'], start_time = request.form['start_time'])
    db.session.execute(data)
    db.session.commit()
    flash('Show was successfully listed!')
  except():
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  #flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
'''
if __name__ == '__main__':
    app.run()
'''
# Or specify port manually:
# using this part as it my PC has TeamViewer running on port 5000 
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4321))
    app.run(host='0.0.0.0', port=port)

