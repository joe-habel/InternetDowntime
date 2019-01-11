import socket
import speedtest
from apscheduler.schedulers.blocking import BlockingScheduler
import datetime

def is_connected():
  try:
    # see if we can resolve the host name -- tells us if there is
    # a DNS listening
    host = socket.gethostbyname('www.google.com')
    # connect to the host -- tells us if the host is actually
    # reachable
    s = socket.create_connection((host, 80), 2)
    return True
  except:
    pass
  return False

def get_speed():
    servers = []
    s = speedtest.Speedtest()
    s.get_servers(servers)
    s.get_best_server()
    s.download()
    s.upload()
    s.results.share()
    
    results_dict = s.results.dict()
    return (results_dict['download']/1000000, results_dict['upload']/1000000, results_dict['ping'])

def log():
    if is_connected():
         down,up,ping = get_speed()
         now = datetime.datetime.now()
         with open('log.csv', 'a') as logfile:
             logfile.write('%s,%s,%s,%s\n'%(now.strftime('%A %B %d %Y %I:%M%p'),down,up,ping))
         
    else:
        now = datetime.datetime.now()
        with open('log.csv', 'a') as logfile:
            logfile.write('%s,%s,%s,%s\n'%(now.strftime('%A %B %d %Y %I:%M%p'),0,0,0))


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

log()
update_time = get_update_time()
scheduler = BlockingScheduler()
scheduler.add_job(log, 'interval', minutes=update_time)
scheduler.start()