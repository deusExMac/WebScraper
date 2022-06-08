

from dataclasses import dataclass, field
from typing import List
import dataconf 

import re
import requests_html


@dataclass
class extractionCondition:
      """
         This is used to place preconditions on the content of the html page.
         Preconditions have a css selector and regular expression the text of the
         selected element needs to match.
         Currently, only the FIRST of the potential many elements is checked.
         TODO: Error checking
      """
      # Currently this places conditions (regular expressions) only on the extracted text of elements.
      ecCSSSelector: str = ''
      ecTextCondition: str = ''  # Regular expression
      ecRuleCSSSelector: str = '' # If not empty and conditionType is ANY, this will replace the rule's css selector. A way to conditionally apply selectors.

      def conditionHolds(self, htmlContent) -> bool:
          res = htmlContent.find(self.ecCSSSelector, first=False)
          if len(res) <= 0:
             return(False)
            
          if re.search(self.ecTextCondition, res[0].text) is None:
             return(False)
          else:
             return(True) 







@dataclass
class ruleConditionList:
      conditionType: str = ''
      conditionList: List[extractionCondition] = field(default_factory=lambda:[])




      

def makeRuleConditionList() -> ruleConditionList or None:
    return ruleConditionList()



@dataclass
class extractionRule:
    """Class for represeing a simple extraction rule."""
    ruleName: str = field(default = '')
    ruleDescription: str  = field(default = '')
    # regular expression the URL has to match to make this rule fire
    ruleURLActivationCondition: List[str] = field(default_factory=lambda:[])
    
    ruleTarget: str = field(default='html') # Does this rule apply on html or on javascript? Two values supported: html and js

    # How to get/scrap the data (in regex or css selector form)
    ruleCSSSelector: str  = field(default = '')
    ruleTargetAttribute: str  = field(default = '')
    #ruleRegularExpression: str = ''
    # Regular expression that the extracted rule content must match
    # to be considered valid
    ruleContentCondition: str = field(default = '') #''
    # Preconditions that (all) must be met by the html content in order to apply the rule

    #rulePreconditions:List[extractionCondition]  = field(default_factory=lambda:[])     
    #rulePreconditions: ruleConditionList=field(default_factory=makeRuleConditionList)
    rulePreconditionType: str = 'ANY'
    rulePreconditions: List[extractionCondition] = field(default_factory=lambda:[])

    # Whether or not downloaded page should be rendered using HTMLSession's .render method
    # TODO: Very, very slow. Please dont set it to true in the current version.
    ruleRenderPage: bool  = False
    
    ruleReturnsMore: bool  = False

    # List of css selectors to apply to each result of ruleCSSSelector in order to
    # extract specific values and assign them to variables one-by-one defined in
    # ruleReturnedValueNames.
    rulePostCSSSelector: List[str] = field(default_factory=lambda:[])
    
    # If more than one value is returned, the next field tells us under what
    # key to store the extracted values (i.e. the text of each element)
    ruleReturnedValueNames: List[str] = field(default_factory=lambda:[])    
    ruleReturnedMatchPos: int  = 0    
    ruleReturningMoreIsError: bool  = False

    # If non-empty, applies this css selector to each result returned by ruleCSSSelector
    # TODO: Do we need this?
    #rulePostContentProcessing: str = field(default = '')
    
    ruleRemoveChars: List[str] = field(default_factory=lambda:[])
    ruleAux1: str = ''
    ruleAux2: str = ''

    # Usage statistics
    ruleMatchedUrlsCount: int = 0
    rulePreconditionFailedCount: int = 0
    ruleAppliedCount: int = 0
    ruleMatchCount: int = 0


    
    def __post_init__(self):  
        if self.rulePreconditions is None:
           self.rulePreconditions = ruleConditionList(conditionType='', conditionList=[])   
    

          
    #@staticmethod
    #def makeRuleConditionList()->ruleConditionList:
    #    return ruleConditionList( conditionType= '', conditionList=[] )
     
    # Check if this rule should be activated for this url
    def ruleMatches(self, url) -> bool:
          
        # No condition means apply it
        if len(self.ruleURLActivationCondition) == 0:
           self.ruleMatchedUrlsCount += 1
           return(True)
            
        for regExp in self.ruleURLActivationCondition:
            if re.search( regExp, url) is not None:
               self.ruleMatchedUrlsCount += 1   
               return(True)

        return(False)



    

    # TODO: Do we need this?
    def load(self, dictionary) -> int:
        self.ruleName = dictionary.get('name', '')
        self.ruleDescription = dictionary.get('decription', '')
        self.ruleRegularExpression = dictionary.get('regex', '')
        self.ruleReturnsMore = dictionary.get('more', False)
        self.ruleReturnedMatchPos = dictionary.get('matchpos', 0)
        self.ruleReturningMoreIsError = dictionary.get('reporterrors', False)
        return(0)
        


    # TODO: Complete me.
    
    def extract(self, text) -> list:
       print("[DEBUG] matching", self.ruleRegularExpression) 
       matches = re.findall(self.ruleRegularExpression, text)
       if self.ruleReturningMoreIsError and len(matches) > 1:
          raise Exception('Returned more than one matches (' + str(len(matches)) + ') while expected only one.')
        
       return(matches)


    

    def extractOne(self, text, pos = 0) -> str:
        matches = re.findall(self.ruleRegularExpression, text)
        if pos < len(matches):
           return( matches[pos] )
        else:
           return('') 



    # EXAMPLE: "data: {.*labels: \[([^\]]*)\],"
    def extractFromScript(self, htmlContent, rgExp, scrName='') -> dict:
          
        scriptList = htmlContent.find('script')

        for s in scriptList:
            fill_sequence=re.compile( rgExp ,re.MULTILINE)
            for match in fill_sequence.finditer(s.text):
              # ok. Found match. Assume this is it.    
              fVal = match.groups()
              return({self.ruleName:fVal[0]})
              
        return( {} )      
          



    def evalPreconditions(self, htmlContent) -> dict:

        # If no preconditions are present, this means rule should be applied. 
        # TODO: Quck and dirty fix. Find a better way to do this.
        if  len(self.rulePreconditions) == 0:
            return({'status':True, 'cssselector':''})

      
        if self.rulePreconditionType.lower() == 'all':
           # This means all conditions must hold to apply rule
           for pc in self.rulePreconditions:
               print('\t\t[DEBUG] [Mode ALL] Checking if precodition rule [', pc.ecCSSSelector, '] holds......', end='')
               if not pc.conditionHolds(htmlContent):
                  print('NO')                  
                  self.rulePreconditionFailedCount += 1
                  return( {'status': False, 'cssselector':''} )

               print('YES')
               
           return( {'status': True, 'cssselector':''} ) 

        if self.rulePreconditionType.lower() == 'any':
           # This means at least one condition must hold to apply rule   
           for pc in self.rulePreconditions:
               print('\t\t[DEBUG] [Mode ANY] Checking if precodition rule [', pc.ecCSSSelector, '] holds......', end='')
               if pc.conditionHolds(htmlContent):
                  print('YES')
                  if pc.ecRuleCSSSelector != '':
                     return( {'status': True, 'cssselector': pc.ecRuleCSSSelector})
                  else:
                      return( {'status': True, 'cssselector': ''} )
               print('NO')

           self.rulePreconditionFailedCount += 1                   
           return( {'status': False, 'cssselector':''} )                   

                        
        print('\t\t[DEBUG] Unknown mode [', self.rulePreconditionType, ']')              
        return( {'status': False, 'cssselector':''} )




    
    # htmlContent must be html object from requests_html
    # TODO: Check this thoroughly. Also, refactor this...
    def apply( self, htmlContent ) -> dict:

        exTractedData = {}
        '''
        # Check if there are preconditions and they are met.
        # If not, rule is not applied.
        for pc in self.rulePreconditions:
            print('\t\t[DEBUG] Checking if precodition rule [', pc.ecCSSSelector, '] holds......', end='')
            if not pc.conditionHolds(htmlContent):
               print('NO')   
               exTractedData[self.ruleName] = ''   
               print('\t\t[DEBUG] precondition [', pc.ecCSSSelector, '] is NOT MET. Stopping')
               self.rulePreconditionFailedCount += 1
               return(exTractedData) 

            print('YES') 

        '''

        preconStatus = self.evalPreconditions(htmlContent)
        print('\t\t[DEBUG] evaluation of preconditions returned: ', preconStatus['status'])
        if not preconStatus['status']:
           exTractedData[self.ruleName] = ''
           return(exTractedData)

        print('\t\t[DEBUG] Precoditions hold. CSS Selector changed to [', preconStatus['cssselector'],']', sep='')
        
        self.ruleAppliedCount += 1

        if self.ruleTarget == 'js':
           # This rule targets a script. Enter script mode
           # preconStatus['cssselector']
           print('\t\t[DEBUG] Extracting from script...')
           if preconStatus['cssselector'] == '':
              return( self.extractFromScript(htmlContent, self.ruleContentCondition  ) )
           else:
               return( self.extractFromScript(htmlContent, preconStatus['cssselector']  ) )  


        
                
        if preconStatus['cssselector'] == '':
           res = htmlContent.find(self.ruleCSSSelector, first=False)
        else:   
            res = htmlContent.find(preconStatus['cssselector'], first=False)





        
        if self.ruleTargetAttribute == "text":
            
             if not self.ruleReturnsMore:
                   
                 if self.ruleContentCondition != '': 
                    res = [m for m in res if re.search(self.ruleContentCondition, m) is not None ]
                 if len(res) <= 0:
                    print("\t\t[DEBUG] Empty. No match present")
                    exTractedData[self.ruleName] = ''
                    return(exTractedData)
                 else:
                    self.ruleMatchCount += 1   
                    xVal = res[self.ruleReturnedMatchPos].text

                    # Replace characters
                    for c in self.ruleRemoveChars:
                        xVal = xVal.replace(c, '')
                     
                    exTractedData[self.ruleName] = xVal
                    return(exTractedData)

             else:
                 # text, but more than one result is returned
                 # TODO: This does not work properly!
              
                 if self.ruleContentCondition != '': 
                    res = [m for m in res if re.search(self.ruleContentCondition, m.text) is not None ]


                 #print('>>>> RETURNED', len(res))
                 #for k in res:
                 #    print('\treturned:', k.text)

                     
                 # TODO: Here, remove specified characters
                 # something like this:
                 #for i in range(len(res)):
                 #     for c in self.ruleRemoveChars:                    
	         #         res[i] = res[i].replace(c, '')
	         # OR BETTER, USE maketrans!
                 #for i in range( len(res) ):
                 #    res[i] = res[i].text.translate({ord(c): None for c in self.ruleRemoveChars}) 
                 nM = 0 
                 if len(self.ruleReturnedValueNames) > 0:
                   if len(self.rulePostCSSSelector) == 0:    
                       for e, name in zip(res, self.ruleReturnedValueNames):
                           exTractedData[name] = e.text.translate({ord(c): None for c in self.ruleRemoveChars})                         
                   else:
                       rsList = []  
                       for e in res:
                           d = {}  
                           for  subR, name in zip(self.rulePostCSSSelector, self.ruleReturnedValueNames):
                                d[name] = e.find(subR, first=True).text 

                           rsList.append(d)
                           print('\t\t\t[DEBUG] Got', d)

                       exTractedData['__LIST'] = rsList
                       
                   nM = len(res) * len(self.ruleReturnedValueNames)    
                 else:
                      # TODO: Get rid of rList and use exTractedData[self.ruleName] = [] etc
                      rList = []
                      for m in res:
                          rList.append( m.text.translate({ord(c): None for c in self.ruleRemoveChars}) )

                      exTractedData[self.ruleName] = rList
                      nM = len(rList)
                      print(':::', exTractedData )

                 self.ruleMatchCount += nM     
                 return(exTractedData)
            
        else:
         # no text   
         numExtracted = 0   
         if self.ruleContentCondition != '': 
            res = [m for m in res if re.search(self.ruleContentCondition, m.attrs.get(self.ruleTargetAttribute)) is not None ]
                         
         if self.ruleReturnedMatchPos >= 0:
            print('>>>>> Got  [', res[self.ruleReturnedMatchPos].attrs.get(self.ruleTargetAttribute), ']', sep='' )
            exTractedData[self.ruleName] = res[self.ruleReturnedMatchPos].attrs.get(self.ruleTargetAttribute)
            numExtracted += 1
         else:
            print(len(res), ' matches found')
            lst = []
            for item in res:
                lst.append( item.text )

            exTractedData[self.ruleName] = lst    
            numExtracted += len(res)

         return(exTractedData)    




@dataclass
class scriptExtractionRule(extractionRule):
      scrptCaptureRegExp: str =''




@dataclass
class ruleLibrary:
      libraryDescription: str = ''
      library: List[extractionRule] = field(default_factory=lambda:[])

      # A list of ruleNames specifying the way the extracted data should
      # be formatted as a line in csv format
      csvLineFormat: List[str] = field( default_factory=lambda:[] )

      def get(self, ruleName) -> extractionRule:
          for r in self.library:
              if r.ruleName == ruleName:
                 return( r )

          return(None)      

      def numberOfRules(self) -> int:
          return( len(self.library) )

      def getPos(self, pos) -> extractionRule:
          if pos >= self.numberOfRules:
             return(None)
          else:
              return( self.library[pos] )


      def toCSVLine(self, xD, sep=',') -> str:
          csvLine = ''
          for nm in self.csvLineFormat:
              # If one is not found, return nothing.
              # TODO: Change this
              if xD.get(nm) is None:
                 return('')
                
              if type(xD[nm]) == str:
                 if csvLine == '':
                    csvLine =  xD[nm]
                 else:   
                    csvLine = csvLine + sep + xD[nm]

          return(csvLine)             



              
      def toDict(self, xD) -> dict:
          dct = {}
          nonEmpty = 0
          for nm in self.csvLineFormat:
              if xD.get(nm) is None:
                 continue
            
              dct[nm] = xD[nm]
              if xD[nm] != '':
                 nonEmpty += 1   

          if nonEmpty == 0:
             print('\t\t\t[DEBUG] Not adding', dct)   
             return( {} )
            
          return(dct)    



      def libStats(self) -> bool:

          for xr in self.library:
              print('Rule:', xr.ruleName)
              print('\tMatched URLs count:', xr.ruleMatchedUrlsCount)
              print('\tFailed precondition count:', xr.rulePreconditionFailedCount)
              print('\tApplied count:', xr.ruleAppliedCount)
              print('\tMatch count:', xr.ruleMatchCount)

          return(False)    


# Test!
def loadRule( r ):    
    rl = dataconf.loads(r, extractionRule)
    return(rl)

def loadLibrary(r):
    return( dataconf.loads(r, ruleLibrary) )
