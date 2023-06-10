# Next overrides the behavior of the default python print
# function

from __future__ import print_function
# This must be the first statement before other statements.
# You may only put a quoted or triple quoted string, 
# Python comments, other future statements, or blank lines before the __future__ line.



from threading import Lock, Event
from collections import deque

import configparser
from datetime import datetime

# Settings related to how the interface
# should behave
wwwInterfaceSettings = configparser.ConfigParser()
wwwInterfaceSettings['io'] = {
                             # setting to true will pipe
                             # all calls to print() not only
                             # to the screen but also to the
                             # socket.
                             'overrideprint':True
                           }













# Should print() calls be overwritten?
# If True, this will result in redirecting
# any call to print also to the socket.io channel
try:
    import __builtin__
except ImportError:
    # Python 3
    import builtins as __builtin__



#
# This is a special print version: besides printing arguments
# on screen, it also pipes it trhough sockets if one is specified
# and the relevant setting is true.
#
def print(*args, **kwargs):

    """My custom print() function."""
        

    if 'sckt' in kwargs and wwwInterfaceSettings.getboolean('io', 'overrideprint', fallback=False):
       s = kwargs.get('sckt', None)
       if s is None:
          __builtin__.print('xx-------- Socketio IS NONE!...') 
          
       else:
          __builtin__.print('\t--------- Socketio FOUND...') 
          try:            
            s.emit('my_response',
                      {'data': ' '.join(str(v) for v in args), 'count': -1})
          except Exception as sEx:
              pass 
                  

    
       
    # Adding new arguments to the print function signature 
    # is probably a bad idea.
    # Instead consider testing if custom argument keywords
    # are present in kwargs

    # Make sure to remove sckt from kwargs so that print will not raise an
    # error/warning. print will raise error when custom arguments are passed
    # to build-in print.
    # NOTE: default value None will cause pop not to raise
    #       an exception if sckt does not exist.
    kwargs.pop('sckt', None)
    
    #__builtin__.print('My overridden print() function!')
    # Call python's default print.
    return __builtin__.print(*args, **kwargs)







# Represents the execution of webScraper in a separate thread.
# Has 1) a reference to the thread executing,
#     2) a lock for accessing the thread and
#     3) an Event object with which other threads can communicate with the
#        executing thread.
class executionThread:
      def __init__(self, teSts=-5):
          self.teStatus = -5
          self.teTmStarted = ''
          self.teTmStopped = ''

          # Reference to executing thread
          self.teThread = None
          
          # This is used to send events to the executing thread.
          # Passed to transportIF which the executing thread
          # checks periodically to see if any message is queued.
          self.teEvents = Event()
          
          self.teThreadLock = Lock()


      def threadRunning(self):
          if self.teThread is None:
             return(False)

          return(True)



      def reset(self):
          self.teStatus = -5
          self.teTmStarted = ''
          self.teTmStopped = ''
          self.teThread = None
          self.teEvents = Event()
          self.teThreadLock = Lock()

      # TODO: This does not actually start the thread.
      #       It just initializes some settings that *MUST*
      #       be reset before starting the scraper thread.
      #       Maybe rename the method?
      def startThread(self):
          self.teStatus = 0
          self.teEvents.set()
          self.teTmStarted = datetime.now().strftime("%d/%m/%Y %H:%M:%S")


      # This acutally does stop the scraper thread by
      # sending a relevant event that the scraper
      # listens to.
      def stopThread(self, waitForTermination=True):
          self.teEvents.clear()
          if waitForTermination:
             self.teThread.join()
             self.teThread = None
             
          self.teTmStopped = datetime.now().strftime("%d/%m/%Y %H:%M:%S")   



      # TODO: Do we need this?
      def signalStop(self):
          self.teEvents.clear()
          





# transport InterFace.
# Allows communication of a client (i.e. the web browser)
# via socketio with the running webScraper when started as a thread.
# Enables also 
#
# For socketio, see https://python-socketio.readthedocs.io/en/latest/
class transportIF:
    
      def __init__(self, sckt=None, evnts=None):

          self.socketio = sckt # Socket through which data is sent back to client
          self.eventChannel = evnts # Event channel that allows signaling termination to running thread
          self.resetSignal()

          # TODO: Do we need this?
          self.scrapeStats = {}




      # TODO: Remove this method.
      #       send2 is the correct one. 
      def send(self, data):
          self.socketio.emit('my_response',
                        {'data': data, 'count': -1})


      # Send data back to client
      def send2(self, *args):
          if self.socketio is None:
             print('No socketio. Message not send.')
             return
          try:  
             self.socketio.emit('my_response',
                             {'data': ' '.join(str(v) for v in args), 'count': -1})
          except Exception as sendEx:
                 print('Error sending message on socketio.', str(sendEx) )


      def resetSignal(self):
          if self.eventChannel is None:
             return(False)
            
          self.eventChannel.set()

          
        
      def signalIsSet(self):
          if self.eventChannel is None:
             return(False)
            
          if not self.eventChannel.is_set():
             return(False) 

          return(True)


      def clear(self):
          if self.eventChannel is None:
             return(False)
            
          self.eventChannel.clear()

