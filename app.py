from flask import Flask, render_template, redirect, request
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
import datetime as dt
import calendar
import pandas as pd
import logging
import downtime

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True
def get_label(start,end):
    times = ['Y', 'M', 'D', 'h', 'm']
    for time in times:
        datemin = np.datetime64(start, time)
        datemax = np.datetime64(end, time)
        if datemin != datemax:
            time_type = time
            break
    if time_type == 'Y':
        majorloc = mdates.YearLocator()
        minorloc = mdates.MonthLocator()
        majorfmt = mdates.DateFormatter('%Y')
        mptfmt = '%Y'
    elif time_type == 'M':
        majorloc = mdates.MonthLocator()
        minorloc = mdates.DayLocator()
        majorfmt = mdates.DateFormatter('%B %Y')
        mptfmt = '%M'
    elif time_type == 'D':
        majorloc = mdates.DayLocator()
        minorloc = mdates.HourLocator()
        majorfmt = mdates.DateFormatter('%B %d')
        mptfmt = '%d'
    elif time_type == 'h':
        majorloc = mdates.HourLocator()
        minorloc = mdates.MinuteLocator()
        majorfmt = mdates.DateFormatter('%I:%m%p')
        mptfmt = '%h'
    elif time_type == 'm':
        majorloc = mdates.MinuteLocator()
        minorloc = mdates.SecondLocator()
        majorfmt = mdates.DateFormatter('%I:%m%p')
        mptfmt = '%m'
    return datemin,datemax+1, majorloc,minorloc,majorfmt,mptfmt
    
            

def make_plot(rows,title):
    dates = []
    downloads = []
    for row in rows:
        dates.append(datetime.strptime(row[0],'%A %B %d %Y %I:%M%p'))
        downloads.append(round(float(row[1]),1))
    
    datemin,datemax, majorloc,minorloc,majorfmt,mptfmt = get_label(dates[0],dates[-1])
    
    
    
    fig,ax = plt.subplots()
    ax.plot(dates,downloads,'ro')
    ax.xaxis.set_major_locator(majorloc)
    ax.xaxis.set_major_formatter(majorfmt)
    ax.xaxis.set_minor_locator(minorloc)
    ax.set_xlim(datemin,datemax)
    
    
    
    def Mbps(x):
        return '%3.1f' % x
    
    def our_ticks(x,fmt=mptfmt):
        dt = x.strftime('%Y-%B-%d-%I-%M-%p')
        if fmt == '%Y':
            return dt.split('-')[0]
        if fmt == '%M':
            return dt.split('-')[1]
        if fmt == '%d':
            return dt.split('-')[2]
        if fmt == '%h':
            return dt.split('-')[2] + dt.split('-')[5]
        if fmt == '%m':
            return dt.split('-')[2] + ':' + dt.split('-')[3]  + dt.split('-')[5]
    
    ax.format_xdata = our_ticks
    ax.set_ylabel('Download Speed Mbps')
    ax.set_title(title)
    fig.autofmt_xdate()
    fig.set_size_inches(8,6)
    plt.savefig('static/%s.png'%title)
    plt.clf()    

def get_update_time():
    try:
        with open('config.txt', 'r') as config:
            config_contents = config.read()
    except:
        with open('config.txt', 'w') as config:
            config.write('update=15\n')
    
    if config_contents.find('update=') < 0:
        with open('config.txt', 'w') as config:
            config.write('update=15\n')
        update_time = 15
    else:
        try:
            eq = config_contents.find('update=')
            nl = config_contents.find('\n', eq+1)
            update_time = int(config_contents[eq+1:nl])
        except:
            with open('config.txt', 'w') as config:
                config.write('update=15\n')
                update_time = 15
    return update_time
    

def get_total_downtime(month_sheet,today):
    try:
        month = today.month
        year = today.year
    except:
        month, year = today
        month = int(month)
        year = int(year)
    update_time = get_update_time()
    month_sheet['prev_date'] = month_sheet['Date'].shift()
    month_sheet['Difference'] = pd.to_datetime(month_sheet['Date']) - pd.to_datetime(month_sheet['prev_date'])
    month_sheet = month_sheet.loc[month_sheet['Difference'].notnull()]
    month_sheet['Difference'] = month_sheet['Difference'].astype(dt.timedelta)
    update_time = dt.timedelta(minutes=(1.15*update_time))
    month_sheet = month_sheet.loc[month_sheet['Difference'] < update_time]
    runtime = month_sheet['Difference'].sum()
    month_sheet = month_sheet.loc[(month_sheet['Download'] == 0) & (month_sheet['Upload'] == 0) & (month_sheet['Ping'] == 0)]
    downtime = month_sheet['Difference'].sum()
    total_time = dt.timedelta(calendar.monthrange(year,month)[1]*(24*60))    
    return runtime, downtime, total_time     

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

@app.errorhandler(404)
def page_not_found(e):
    return '404 Error, Page Not Found <br> We have no data on file for this month.'

@app.route('/',methods=['GET', 'POST'])
def main_page():
    if request.method == 'POST':
        if  'Last' in request.form:
            today = datetime.now()
            month_diff = relativedelta(months=1)
            last_month = today - month_diff
            month = str(last_month.month)
            year = str(last_month.year)
            month_year = month + '&' + year
            return redirect('month/%s'%month_year)
        elif 'This' in request.form:
            today = datetime.now()
            month = str(today.month)
            year = str(today.year)
            month_year = month + '&' + year
            return redirect('month/%s'%month_year)
        else:
         return redirect('404')
    elif request.method == 'GET':    
        with open('log.csv', 'r') as logfile:
            rows=logfile.readlines()
        
        data_sheet = pd.read_csv('log.csv')
        today = datetime.now()
        this_month = today.month
        data_sheet = data_sheet.loc[pd.to_datetime(data_sheet['Date']).dt.month==this_month]
        runtime, downtime, total_time = get_total_downtime(data_sheet,today)
        if len(rows) < 100:    
            data_rows = [row.split(',') for row in rows[1:]]
        else:
            data_rows = [row.split(',') for row in rows[-99:]]
        title = 'Uptime'
        make_plot(data_rows,title)
        return render_template('index.html',filename=title,current_uptime=reversed(data_rows[-25:]),runtime=runtime,downtime=downtime,total_time=total_time)

@app.route('/month/<month_year>')
def get_month(month_year):
    try:
        data_sheet = pd.read_csv('log.csv')
        month_year = month_year.split('&')
        month = month_year[0]
        year = month_year[1]
        data_sheet = data_sheet.loc[(pd.to_datetime(data_sheet['Date']).dt.month==int(month)) & (pd.to_datetime(data_sheet['Date']).dt.year==int(year))]
        rows = data_sheet.reset_index().values.tolist()
        rows = [[item for item in row[1:]] for row in rows]
        title = str(month) + '-' + str(year)  + ' Uptime'
        make_plot(rows,title)
        runtime,downtime,total_time = get_total_downtime(data_sheet,(month,year))
        return render_template('index.html',current_uptime=rows,filename=title,runtime=runtime,downtime=downtime,total_time=total_time)
    except:
        return redirect('404')
    


app.run(host='0.0.0.0')


