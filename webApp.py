






import os
import time
from tempfile import mkdtemp
from datetime import datetime, timedelta
from collections import deque
import ntpath

#from threading import Lock, Event

import requests
import mimetypes

# flask related
from flask import Flask, render_template, redirect, session, current_app, request, Response, send_file
from flask_socketio import SocketIO, emit


# Server side sessions
# 
# The Session instance is not used for direct access,
# you should always use flask.session
from flask_session import Session



import configparser

import glob
import json

import sys


from wwwInterface import executionThread, transportIF



# This is important so as to import webScraper as a module (make sure that
# scraper/ folder has an __ini__.py file
# The next line will enable importing py files as modules from the
# scraper/ folder where the webScraper code resides.
#
# NOTE: Not needed anymore
#sys.path.append('scraper/')
#from scraper import commandShell, xRules






##############################################################################
#
#
#
#                    Section initializing some global variables.
#                    TODO: needs to change.
#
#
#
##############################################################################




# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

# use parameter instance_relative_config = True or instance_path
# if e.g. config files are stored outside of working path in order 
# to exclude them from versioning,
# See: https://flask.palletsprojects.com/en/2.2.x/config/#instance-folders
app = Flask(__name__)


# Here SERVER SIDE session management is
# initialized.
# Flask  -by default- uses CLIENT SIDE
# session management
# 
# 
print('>>>Setting secret key')
app.secret_key = 'super secret key'


#app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)
#app.config['SESSION_TYPE'] = 'filesystem'

# Load flask app settings from file
app.config.from_pyfile(os.path.join(".", "app.conf"), silent=False)

# Path to store session files
app.config['SESSION_FILE_DIR'] = mkdtemp()

# Initialize server-side session for app
sSess = Session(app)
sSess.init_app(app)



# TODO: Move socketio and it's creation inside transportIF???
socketio = SocketIO(app, async_mode=async_mode, ping_interval=12)

# NOTE: some interesting arguments...
# socketio = SocketIO(engineio_logger=True, ping_timeout=5, ping_interval=5)


# Keeps a reference to the started thread as well as
# to all variables/data structures
# 
# TODO: Use this to replace
# variables below.
threadContext = executionThread()






# End of global variable initialization section











###########################################################################
#
#
#
#                         Flask handlers follow
#
#
#
###########################################################################





#
# This function is defined to update
# the server-side session in order to not expire.
#
# TODO: Does this work (app.before_request and refreshing session)?
#       Check it...
@app.before_request
def requestProlog():
   #session.permanent = True
   #session.modified = True
   pass







def isAuthenticated():
    return( session.get('authenticated') )





#saveLKP
def saveExecutionHistory(paramDict, lkpfile='.lastparams', maxLkp=20):


    allLkp = loadLKP(lkpfile)
    
    if maxLkp > 0:
      if len(allLkp['history']) >= maxLkp:
         allLkp['history'] = allLkp['history'][:(maxLkp - len(allLkp['history']) - 1)]
        
    
    allLkp['history'].insert(0, {'avgpps':'???',
                                 'elapsed':'???',
                                 'nextracted':'???',
                                 'nproc':'???',
                                 'outputfile':'???',
                                 'date':datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                 'params':paramDict})
    
    with open(lkpfile, 'w') as fp:
         json.dump(allLkp, fp, sort_keys=True, indent=5)

    return(0)     



def loadLKP(lkpfile='.lastparams'):
    try:
        
       #if not os.path.isfile(lkpfile):
       #   return( {'history':[]}  )

        
       lkp = {'history':[]}  
       with open(lkpfile, 'r') as lkpf:            
            lkp = json.loads(lkpf.read())
    except Exception as lkpEx:
           print('Error loading lkp:', str(lkpEx))

    #print('Rerutning >>>> ', lkp)
    return(lkp)


def dumpLKP(lkpfile='.lastparams', lkpData={}):
    if not lkpData:
       return(-4)

    
    with open(lkpfile, 'w') as fp:
         json.dump(lkpData, fp, sort_keys=True, indent=5)

    return(0)     


    
def updateLKPStats(lkpfile='.lastparams', pos=0, statData={}):

    if statData is None:
       return(-3)
    
    allLkp = loadLKP(lkpfile)
    if not allLkp:
       return(-2)

    allLkp['history'][pos]['elapsed'] = statData.get('elapsed', '-1')
    allLkp['history'][pos]['nproc'] = statData.get('nproc', '-1')
    allLkp['history'][pos]['nextracted'] = statData.get('nextracted', '-1')
    allLkp['history'][pos]['qsize'] = statData.get('qsize', '-1')
    allLkp['history'][pos]['avgpps'] = statData.get('avgpps', '-1')
    allLkp['history'][pos]['outputfile'] = statData.get('outputfile', '')

    
    dumpLKP(lkpfile, allLkp)
    
    return(0)
    
    






def background_thread(executionParams):
    """Example of how to send server generated events to clients."""
    
    
    # This is the global
    # object keeping/managing the thread and thread
    # related data structures.
    global threadContext

    try:
       executionParamsDict = json.loads(executionParams)
    except Exception as paramEx:
       print('Exception reading json arguments:', str(paramEx))
       return(-7)

    #
    # Prepare the execution parameters passed (which now
    # are encoded in a string) and transform it properly into a list
    # that will be passed to the crawl() method.
    # Moreover, some arguments should not be passed to
    # the webCrawler and need to be handled here.
    #
    # NOTE: we try to keep changes to webCrawler's crawl()
    #       method to an absolute minimum. Hence, we don't
    #       try to change the way arguments are handled inside
    #       crawl().

    # default crawler configuration file to use
    cfgFile = 'scraper/webscraper.conf'
    argumentList = []
    for k, v in executionParamsDict.items():

        if isinstance(v, bool):
           if v:
              argumentList.append(k)

           continue
              
        if k != 'u':          
            if k == '-c':
               # keep the config file. Needed at this level. 
               cfgFile = v
            else:
               argumentList.append(k)
               argumentList.append(v)   
               
        
    # add url as the last argument in the list.
    argumentList.append( executionParamsDict.get('u', '') )
    
    print( 'PARAMETERS:', str(executionParams), ' TRANSFORMED:', argumentList )
    
    
    # make sure specified configuration file exists
    if not os.path.exists(cfgFile):
       transportIF(socketio, threadContext.teEvents).send2( json.dumps( {'status':-5, 'nproc':'???', 'nextracted':'???', 'qsize':'???', 'avgpps':'???', 'url':'???'}) )
       transportIF(socketio, threadContext.teEvents).send2('Configuration file [' + cfgFile + '] does not exist. Scraper not started.')                                                     
       return(-5)


   
    # Read configuration settings for crawler to pass it
    # to the crawl() method.
    # Configuration file of the crawler is read here in order
    # to not change significantly the crawl method.
    config = configparser.RawConfigParser(allow_no_value=True)

    # TODO: Change this...
    print('Loading configuration file [', cfgFile, ']...', sep='', end='')
    config.read(cfgFile)
    config.add_section('__Runtime')
    config.set('__Runtime', '__configSource', 'scraper/webscraper.conf')

    # How to format argument list before passing it to
    # crawl method
    #argumentList = ["-M", "-n", "-1", "-r", "rules/books.toscrape.com.exr", "https://books.toscrape.com/"]

    print('###########\nCALLING CRAWLER\n###########\n')
    print('Executing web scraper with following parameters:', ' '.join(argumentList) )
    time.sleep(3)


    saveExecutionHistory(executionParamsDict)
    
    # Signal thread start. Does not actually start the thread
    # but rather initializes some settings.
    #
    # NOTE: stopThread is called when a stop message is
    #       received from the client.
    # TODO: Change this? Rename method (Start/stop)?
    threadContext.startThread()
    
    executioner = commandShell.commandImpl(config, None)
    executioner.crawlI( argumentList, transportIF(socketio, threadContext.teEvents) )

    # Since we've finished, send back stats to client.
    if executioner.execStats is None:
       transportIF(socketio, threadContext.teEvents).send2( json.dumps( {'status':-2, 'nproc':'???', 'nextracted':'???', 'qsize':'???', 'avgpps':'???', 'url':'???'})   ) 
    else:   
       # ΤODO: Send stats here.
       transportIF(socketio, threadContext.teEvents).send2( json.dumps( {'status':-1, 'nproc':executioner.execStats['nproc'], 'nextracted':executioner.execStats['nextracted'], 'qsize':executioner.execStats['qsize'], 'avgpps':executioner.execStats['avsgpps'], 'url':''})) 
       print('\n\n')
       print('####### ', executioner.execStats)
       print('\n\n')
       updateLKPStats(statData=executioner.execStats)
       
    return(0)
    


# Searching color theme in following order:
#    session -> url query -> default (if invalid) 
def loadColorTheme(defClr='blue'):
   
    # load default  from config  
    clrthm = app.config.get('APP_COLOR_THEME', 'blue').lower()

    # If session has color theme, use it
    if session.get('colortheme'):
       clrthm = session['colortheme']
       print('[loadColorTheme] >>>> FOUND in session: [', clrthm, ']' )

    # If URL has query specifying color, overwrite existing 
    # color theme.
    # TODO: This needs to change
    if request.args.get('c') is not None:
       clrthm = request.args.get('c').lower()
       print('[loadColorTheme] >>>> Storing color: [', clrthm, '] in session' )
       # Store it in session
       # NOTE: Will be stored in session even if clrthm is not a valid color scheme.
       #       Validity is checked later.
       session['colortheme'] = clrthm
  
    # Load color theme settings from file and search desired theme
    colorThemes = {}
    print('[loadColorTheme] >>>> SETTING color scheme: [', clrthm, ']' )
    try:
       f = open('uiColorThemes.json', 'r')
       colorThemes = json.load(f)       
       f.close()
    except Exception as thmEx:
       pass

    print('[loadColorTheme] >>>> Using color [', clrthm, ']' )
    
    # Return dark- and light- color.
    # Defaults to kind of blue theme if color in clrthm does not exist    
    return(colorThemes.get(clrthm, {"darkcolor":"#4676f2", "lightcolor":"#eceeff"})['darkcolor'],
           colorThemes.get(clrthm, {"darkcolor":"#4676f2", "lightcolor":"#eceeff"})['lightcolor']
          )
    
     



         
        

@app.route('/')
def index():
    
    if not isAuthenticated():
        return( redirect('/login') )

    return redirect("/home2")
    


 

@app.route('/login', methods=["POST", "GET"])
@app.route('/login/', methods=["POST", "GET"]) 
@app.route('/login/<name>', methods=["POST", "GET"])
def login(name=''):

    if isAuthenticated() and "force" not in request.args:
       return redirect("/home2")
    
    if name != '':
       session['authenticated'] = name 
       return( name )

    if request.method == 'POST':
       if "username" in request.form: 
           uname = request.form['username']
           if uname != '':
              session['authenticated'] = uname
              # TODO: Do we need this?
              #session.permanent = True
              return redirect("/home2")
        
        
    return render_template('login.html')

    




@app.route('/authstatus', methods=["POST", "GET"])
def authstatus():
    if session.get('authenticated'):
       return('>>> Authenticated as user:' +  session['authenticated'] + '<br> >>> Session expiration:' + str(app.permanent_session_lifetime) + '<br> >>> Path:' + app.config['SESSION_FILE_DIR'] + '<br> >>>Secret key:' + app.secret_key )
    else:
       return('>>> NOT AUTHENTICATED USER') 





@app.route('/logout', methods=["POST", "GET"])
@app.route('/logout/', methods=["POST", "GET"])
def logout():
    #if not isAuthenticated():
    session.clear()
    #return redirect("/login/logged out")
    return render_template('main.html', async_mode=socketio.async_mode)

        
    

@app.route('/connected')
def connected():
    global threadContext
    if thread is None:
       return('<font color="red">THREAD NOT RUNNING</font>')
    else:
       return('<font color="green">THREAD RUNNING</font>') 






@app.route('/home')
def home():
    return(render_template('home.html') )


@app.route('/home2', methods=['GET'])
def home2():

    #global colorThemes
    
    if not isAuthenticated():
       return( redirect('/login') )

    
    dc, lc = loadColorTheme()
    return(render_template('home2.html', darkcolor=dc, lightcolor=lc) )





@app.route('/status')
def status():

    global threadContext
    
    statusD = {}
    if session.get('authenticated'):
       statusD['user'] = session['authenticated']
    else:
       statusD['user'] = ''
       
    if not threadContext.threadRunning():
       statusD['backgroundthread'] = 'Not running'
    else:
       statusD['backgroundthread'] = 'Running' 

    statusD['backgroundstartdate'] = threadContext.teTmStarted #threadStarted
    statusD['backgroundstopdate'] = threadContext.teTmStopped

    # TODO: Fix next part. In particular what path to sent back and how to format it.
    #       Currently it;s a mess. apphome and APP_RULE_HOME_DIR are not related. 
    apphome = app.config.get('APP_HOME_DIR', os.path.dirname(os.path.realpath(__file__)) )
    if apphome.strip() == "":
       apphome = os.path.dirname(os.path.realpath(__file__))
       
    statusD['exrPath'] = app.config['APP_RULE_HOME_DIR'] + ' (home:' + apphome + ')'
    
    return(statusD)




@app.route('/exr/')
def listExrfiles():

    print('Scanning directory', app.config.get('APP_RULE_HOME_DIR', 'rules/') ) 
    exrfiles = glob.glob(app.config.get('APP_RULE_HOME_DIR', 'rules/')  + '*.exr')
    
    fmt = 'html'
    if 'format' in request.args:
        fmt = request.args.get('format')

    showD = app.config.get('APP_SHOW_EXR_DESCRIPTION', False)  
    if 'showd' in request.args:
        showD = True
        
    if 'nshowd' in request.args:
        showD = False
        
    exfl = []
    for fn in exrfiles:
        lDesc = ''
        if showD:
           try:     
             with open(fn,  encoding='utf-8', errors='ignore', mode='r') as f:          
                xLib = xRules.loadLibrary(f.read())
           except Exception as rFile:
             #print('Error reading rule file', args['exrfile'], str(rFile))
             continue
           lDesc =  xLib.libraryDescription
           #print('Loaded:', xLib.libraryDescription)
           
        exfl.append( {'parentdir':ntpath.dirname(fn), 'filename':ntpath.basename(fn), 'description':lDesc} )
        
    if fmt == 'partial':
       return render_template('jsonList.html', exrfilelist=exfl)
    elif fmt == 'inplaceloading':
         # Changes the links to exr files: does not reload the page but
         # uses ajax to do so
         # TODO: Change this??
         return render_template('jsonListinplace.html', exrfilelist=exfl)
    else: 
       return render_template('exrlist.html', exrfilelist=exfl)





@app.route('/exrs/<path:filename>')
def exr(filename=''):
     file1 = open(filename, 'r')
     Lines = file1.readlines()
     file1.close()

     return('<br>'.join(Lines) )

     ''' 
     with open(filename, 'r') as f:
        text = f.read()
    
     return(text)
     '''
    #if filename == '':
    #   exrfiles = glob.glob('rules/*.exr')
    #   return render_template('exrlist.html', exrfilelist=exrfiles)



@app.route('/getfile', methods=["POST", "GET"])
@app.route('/getfile/', methods=["POST", "GET"])
@app.route('/getfile/<path:fnm>', methods=["POST", "GET"])
def getfile(fnm=''):
    if fnm == '':
       return redirect("/home2")

    if not os.path.exists(fnm):
       return redirect("/home2")

    
    return( send_file(fnm) ) 
    
       

@app.route('/editexr', methods=["POST", "GET"])
@app.route('/editexr/', methods=["POST", "GET"])
@app.route('/editexr/<path:fnm>', methods=["POST", "GET"])
def editexr(fnm=''):

    if fnm == '':
       return redirect("/exr/")
    
    # For some reason, when loading
    # monaco .js files, some URLs will
    # get routed to there. In particular, request for this
    # resource will be requested:
    #     /editexr/static/min/vs/editor/editor.main.css
    #
    # This should not happen. For now, we simply
    # ingore these requests until we find out what is happening.
    #
    # TODO: Look into this strange behavior.
    if "min/vs" in fnm:
        return('')

    # We introduce a small delay  so that
    # the 'saving' message at the ui will be shown
    time.sleep(0.8)
    if request.method == 'POST':
       try: 
          targetFile = request.form['exrFileName']
          fileContent = request.form['exrContent']
          if "mode" in request.form:              
             iMode = request.form['mode']
             print('>>> mode=', iMode )
          else:
              print('NO IMODE!')

          print('Saving exr file to [', targetFile, ']', sep='') 
          file = open(targetFile, "w")
          a = file.write(fileContent)
          file.close()
          return('Ok! Saved')
       except Exception as ex:
          print( str(ex) ) 
          return('Error!' + str(ex)) 


    autos = False
    if 'as' in request.args:
        autos = True
    
    fcnt=''
    print('Reading file ==>', fnm)

    with open(fnm, 'r') as f:
        fcnt = f.read()

    #print(fcnt)
    #from markupsafe import Markup
    #fcnt = Markup(fcnt)
    print('Done')
    dc, lc = loadColorTheme()
    return render_template('editExr.html', fcontent = fcnt.replace('\n', '\\n'), fileopened = fnm, autosave=autos, darkcolor=dc, lightcolor=lc )




@app.route('/lkp')
def lkp():

    lstP = loadLKP()
    pList = []
    for p in lstP['history']:
        pList.append( json.dumps(p['params']) )
        
    return render_template('paramList.html', executionParameterList = lstP['history'], jsons=pList )
    #return( json.dumps( lstP ) )

    lkpstr = '{}'
    try:
       with open('.lastparams', 'r') as lkpf:
            lkpstr = json.dumps( json.loads(lkpf.read()) )
    except Exception as lkpEx:
           pass
    return( lkpstr )



###########################################################################
#
#
#
#                         socketio handlers follow
#
#
#
###########################################################################


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})



# Receive the test request from client and send back a test response
@socketio.on('test_message')
def handle_message(data):
    print('received message: ' + str(data))
    # emit('my_response', {'data': 'Test response sent'})
    transportIF(socketio, None).send2('Test message ack.')



# Broadcast a message to all clients
@socketio.on('broadcast_message')
def handle_broadcast(data):
    print('received: ' + str(data))
    emit('broadcast_response', {'data': 'Broadcast sent'}, broadcast=True)




@socketio.on('startScraper')
def startScraper(data):

    try:
        global threadContext

        # We use a lock to make sure no other
        # web request is starting the thread. Lock is used to
        # ensure mutual exclusion on critical section accessing shared variable
        # socketio and threadContext.
        #
        # NOTE: .acquire() and release() will be automatically called upon
        # entering and leaving the block
        with threadContext.teThreadLock:
           if not threadContext.threadRunning():
              print('STARTING background thread...')
              threadContext.teThread = socketio.start_background_task(background_thread, data['data'])
              #socketio.emit('my_response', {'data': 'Worker thread started.', 'count': 0})
              transportIF(socketio, None).send2('Worker thread started successfully.')
           else:
              print('Thread ALREADY running...')
              transportIF(socketio, None).send2('Worker thread not started. Thread already running.')
              #socketio.emit('my_response', {'data': 'Worker thread already running.', 'count': 0})
            
        
    except Exception as ssEx:
        print('Error!', str(ssEx) )
        transportIF(socketio, None).send2('Exception while trying to stop thread', str(ssEx))
    

@socketio.on('stopScraper')
def stopScraper(data):
    
    global threadContext

    print('Calling stopScraper...')
    if not threadContext.threadRunning():
       #emit('my_response', {'data': 'Scraper not running.', 'count': 0})
       transportIF(socketio, None).send2('WebScraper not running.')
    else:    
       print('>>> Stopping scraper. Waiting for scraper to stop...', end='')
       threadContext.stopThread()         
       print('ok. Stopped.')
       transportIF(socketio, None).send2('[', threadContext.teTmStopped, '] WebScraper stopped')
    

@socketio.on('testScraper')
def testScraper(data):
    print('Calling testScraper')
    transportIF(socketio, None).send2( '{status:-6, comment:"Hahahahah"}' )
    #emit('my_response', {'data': 'testScraper ack!'})
    return
   

@socketio.event
def connect():
    
    if session.get('authenticated'):
       print('>>> Connected as user:', session['authenticated'])
    else:
        emit('my_response', {'data': 'Not authenticated.', 'count': 0})
        return()



if __name__ == '__main__':
    app.run(app)
