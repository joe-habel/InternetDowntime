from flask import Flask, render_template
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
import datetime as dt
import calendar
import pandas as pd

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
        majorfmt = mdates.DateFormatter('%M')
        mptfmt = '%M'
    elif time_type == 'D':
        majorloc = mdates.DayLocator()
        minorloc = mdates.HourLocator()
        majorfmt = mdates.DateFormatter('%d')
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
    return datemin,datemax, majorloc,minorloc,majorfmt,mptfmt

def make_plot(rows,title):
    dates = []
    downloads = []
    for row in rows:
        dates.append(datetime.strptime(row[0],'%A %B %d %Y %I:%M%p'))
        downloads.append(round(float(row[1]),1))

    
    datemin,datemax, majorloc,minorloc,majorfmt,mptfmt = get_label(dates[0],dates[-1])
    
    
    
    fig,ax = plt.subplots()
    ax.plot(dates,downloads,'ro')
    ax.set_xlabel('Time')
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
    plt.show()
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

def month(month_year):
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
    return downtime
    
print (month('10&2018'))