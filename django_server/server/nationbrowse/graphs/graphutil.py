# coding=utf-8
from __future__ import division
from django.db import connection

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure


def generate_race_piechart(place,place_type=""):
    if not place.population_demographics:
        return False
    
    # Give this a shorter var name for the calcuations below
    d = place.population_demographics
    
    # Explicitly reset DB connection
    connection.close()
    
    bg = "#ffffff"
    fig = Figure(figsize=(7,7), facecolor=bg)
    ax = fig.add_subplot(111, axis_bgcolor=bg)
    
    labels = "White","Black","Native American","Asian","Pacific Islander","Other"
    fracs = [
        d.onerace_white/d.onerace*100,
        d.onerace_black/d.onerace*100,
        d.onerace_amerindian/d.onerace*100,
        d.onerace_asian/d.onerace*100,
        d.onerace_pacislander/d.onerace*100,
        d.onerace_other/d.onerace*100
    ]
    explode=(.1, .05, 0, 0, 0, 0)
    
    ax.pie(fracs, explode=explode, labels=labels, autopct='%1.2f%%', labeldistance=1.15, shadow=True)
    
    # For ZIP codes, also show the county it's in, if possible.
    if place_type == "zipcode":
        try:
            ax.set_title('Race in ZIP %s, %s, %s\n(total pop %s)' % (place, place.county.long_name,place.county.state.abbr,d.total))
        except:
            raise
            ax.set_title('Race in %s\n(total pop %s)' % (place,d.total))
    elif place_type == "county":
        try:
            ax.set_title('Race in %s, %s\n(total pop %s)' % (place.long_name,place.state.abbr,d.total))
        except:
            raise
            ax.set_title('Race in %s\n(total pop %s)' % (place,d.total))
    else:
        ax.set_title('Race in %s\n(total pop %s)' % (place,d.total))
        
    # Explicitly reset DB connection
    connection.close()

    return fig