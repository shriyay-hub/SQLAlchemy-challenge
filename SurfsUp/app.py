from flask import Flask, jsonify
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt  # Not used in the API, but for potential future visualization

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

# Database connection and model setup (replace 'hawaii.sqlite' with your database name)
engine = create_engine("sqlite:///hawaii.sqlite")
Base = automap_base()
Base.prepare(autoload_with=engine)
Station = Base.classes.station
Measurement = Base.classes.measurement
session = Session(engine)

# Find the most recent date in the dataset (not used in the API, but for reference)
last_date = session.query(func.max(Measurement.date)).scalar()

# Function to calculate temperature statistics for a date range (used in API routes)
def get_temperature_stats(start_date, end_date=None):
    filters = [Measurement.date >= start_date]
    if end_date:
        filters.append(Measurement.date <= end_date)
    temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).filter(*filters).all()
    temperature_list = []
    for temperature in temperature_data:
        temperature_dict = {
            "tmin": temperature[0],
            "tavg": temperature[1],
            "tmax": temperature[2]
        }
        temperature_list.append(temperature_dict)
    return temperature_list

# Flask app setup
app = Flask(__name__)

# API routes
@app.route("/")
def welcome():
    """
    Landing page listing available API routes.
    """
    return (
        "Welcome to the Hawaii Climate Analysis API!<br/>"
        "Available Routes:<br/>"
        "/api/v1.0/precipitation<br/>"  # Get precipitation data for the last year
        "/api/v1.0/stations<br/>"       # List all stations
        "/api/v1.0/tobs<br/>"            # Get temperature data for the most active station for the last year 
        "/api/v1.0/start (enter as YYYY-MM-DD)<br/>"  # Get temperature stats for dates after a specific date
        "/api/v1.0/start/end (enter as YYYY-MM-DD/YYYY-MM-DD)"  # Get temperature stats for a date range
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """
    Returns precipitation data (date as key, prcp as value) for the last year.
    """
    one_year_ago = last_date - dt.timedelta(days=365)
    precipitation_data = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= one_year_ago
    ).order_by(Measurement.date).all()
    precipitation_dict = dict(precipitation_data)
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    """
    Returns a JSON list of all stations and their details.
    """
    stations = session.query(Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()
    station_list = []
    for station in stations:
        station_dict = {
            "station": station[0],
            "name": station[1],
            "latitude": station[2],
            "longitude": station[3],
            "elevation": station[4]
        }
        station_list.append(station_dict)
    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs():
    """
    Returns temperature data (date as key, tobs as value) for the most active station for the last year.
    """
    one_year_ago = last_date - dt.timedelta(days=365)
    active_station = session.query(Station.station, func.count(Measurement.station)).join(
        Measurement, Station.station == Measurement.station
