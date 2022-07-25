
import sys

import pandas as pd
import numpy as np
import csv

import datetime


class urlQueue:

      def __init__(self, qSz=-1, qMemSz='-1', startNewSession=True, qF='.queue',  csvSep=';', sQ=False, cP = 0, tS='bfs'  ):
          
          self.qSize = qSz
          self.qMemorySize = -1
          self.traversal = tS.lower() # traversal stratery: dfs or bfs.
          print('\t[DEBUG] Got queue memory size [', qMemSz.lower(), ']. Traversal: [', self.traversal, ']')
          if qMemSz.lower().endswith('k'):
             self.qMemorySize = int(qMemSz[:-1])*1024
          elif qMemSz.lower().endswith('m'):
                self.qMemorySize = int(qMemSz[:-1])*1024*1024
          elif qMemSz.lower().endswith('g'):
               self.qMemorySize = int(qMemSz[:-1])*1024*1024*1024
          else:
              if int(qMemSz) < 0:
                 self.qMemorySize = -1
              else:
                 self.qMemorySize = qMemSz   

          print('\t[DEBUG] Queue memory size set to ', self.qMemorySize)      
          self.qFile = qF
          self.qSave = sQ
          self.currentQPos = cP # Current position used in update mode
          self.queue = pd.DataFrame({'url': pd.Series(dtype='str'),
                                          'fetched': pd.Series(dtype='str'),
                                          'status': pd.Series(dtype='int'),
                                          'contenttype': pd.Series(dtype='str'),
                                          'contentlength':pd.Series(dtype='int'),
                                          'lastmodified': pd.Series(dtype='str'),
                                          'hash': pd.Series(dtype='str')
                                         }
                                       )
          if not startNewSession:
              # We do it this way so that even if an error occurs, an empty data frame exists.
              # Also, we rely on the Python gb to do its job.
              print('[DEBUG] loading queue from [', self.qFile, '].....', end='')
              try:
                 self.queue = pd.read_csv(self.qFile, header=0, sep=csvSep, quoting=csv.QUOTE_NONNUMERIC)
                 print('ok.')
              except Exception as rEx:
                 print('[DEBUG] Error loading queue from file ', self.qFile, ':', str(rEx), 'Continuing with empty queue.', sep='') 
              
          
          print('[DEBUG]Using queue file [', self.qFile, ']')
          
          
          


      def uInQueue(self, u):
          if self.queue.loc[ self.queue['url'] == u ].shape[0] == 0:
             return(False)

          return(True)  



      def hInQueue(self, h):
          if self.queue.loc[ self.queue['hash'] == h ].shape[0] == 0:
             return(False)

          return(True)
        

      def getByUrl(self, u):
          if  self.queue[ self.queue['url'] == u ].shape[0] == 0:
              return( {} )
            
          return( self.queue[ self.queue['url'] == u ].to_dict( orient='records' )[0]  )



      def getByHash(self, h):
          if  self.queue[ self.queue['hash'] == h ].shape[0] == 0:
              return( {} )
            
          return( self.queue[ self.queue['hash'] == h ].to_dict( orient='records' )[0]  )



      def add(self, u, f=np.nan, s=-1, c=np.nan, cl=np.nan, l=np.nan, h=np.nan):

                    
          if self.qSize >= 0:
             if self.queueSize() >= self.qSize:
                #print('\t[DEBUG] QUEUE: maximum queue size [', self.qSize,  '] reached. Rejecting URL.', sep='')   
                return(False)

          if self.qMemorySize > 0:
             if self.queueMemorySize() >= self.qMemorySize:
                #print('\t[DEBUG] Memory limit [', self.qMemorySize , '] reached. Current size:', self.queueMemorySize(), '. Not adding.', sep='')
                return(False)
             
          if self.uInQueue(u):
             #print('\t[DEBUG] url [', u, '] Already in queue. Not adding.', sep='') 
             return(False)
            
            
          try:
            d = {'url':u, 'fetched':f, 'status':s, 'contenttype':c, 'contentlength':cl, 'lastmodified':l, 'hash':h}
            if self.traversal == 'dfs':
               # this is a depth first search. Add it to the start of the queue   
               self.queue = pd.concat([pd.DataFrame.from_records([ d ]), self.queue], ignore_index=True )
            else:   
               # this is a breadth first search. Add it to the end of the queue
               # add it to the end of the queue            
               self.queue = pd.concat([self.queue, pd.DataFrame.from_records([ d ])], ignore_index=True )

            return(True)
      
          except Exception as ex:
             return(False) 


      def isEmpty(self):
          if self.queue is None:
             return(True)
            
          if self.queue.shape[0] == 0:
             return(True)

          return(False)  
          


      def getNext(self, mode = 'expand'):

          if mode == 'update':
             # In update mode, setup a  position (currentQPos) that
             # tells us which URL to process.
             if self.currentQPos < self.queue.shape[0]:   
                uUrl = self.queue.iloc[ self.currentQPos ]['url']
                self.currentQPos += 1
                return( uUrl )
             else:
                return( None )

          # Not in update mode. Get one that has not been yet fetched i.e.
          # has status equal to -1.
          try:
             
             return( self.queue.loc[ self.queue['status'] == -1, 'url' ].iloc[0] )
             
          except IndexError as iErr:              
              return( None )


       
      def queueSize(self):
          return( self.queue.shape[0] )


      def queueMemorySize(self):
          #print(sys.getsizeof(self.queue) )   # kind of different method with the same result.
          return(self.queue.memory_usage(deep=True).sum() ) 
        
      def pendingUrlsCount(self):
          return( self.queue.loc[ self.queue['status'] == -1].shape[0] )

      def fetchedUrlsCount(self):
          return( self.queue.loc[ self.queue['status'] != -1].shape[0] )

      def errorUrlsCount(self):
          return( self.queue[ (self.queue['status'] < 0 ) & (self.queue['status'] != -1) ].shape[0] )

       

      def updateStatus(self, u, sts):          
          self.queue.loc[ self.queue['url'] == u, 'status' ] = sts



      def updateTimeFetched(self, u):
          nw = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
          self.queue.loc[ self.queue['url'] == u, 'fetched' ] = nw
          
          
      def updateLastModified(self, u, lm):          
          self.queue.loc[ self.queue['url'] == u, 'lastmodified' ] = lm


      def updateContentType(self, u, ct):          
          self.queue.loc[ self.queue['url'] == u, 'contenttype' ] = ct

      def updateContentLength(self, u, cl):          
          self.queue.loc[ self.queue['url'] == u, 'contentlength' ] = cl


      def updatePageHash(self, u, ph):          
          self.queue.loc[ self.queue['url'] == u, 'hash' ] = ph   


          
      def showQ(self):
          print( self.queue )

      
          
      def saveQ(self, csvsep=';'):
          if not self.qSave:
             return(False)
            
          try:
             print('\t[DEBUG] Saving to queue file [', self.qFile, ']', sep='')   
             self.queue.to_csv( self.qFile, index=False, sep=csvsep, quoting=csv.QUOTE_NONNUMERIC )
             return(True)
          except Exception as svEx:
             print('[ERROR] Error saving queue to csv file [', self.qFile, '] ', str(svEx), sep='')
             return(False)
