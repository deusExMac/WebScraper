

from dataclasses import dataclass, field
from typing import List, Dict
import dataconf 

import re
import requests_html

import booleanEvaluation
import utils

@dataclass
class extractionCondition:
      """
         This is used to place preconditions on the content of the ENTIRE html page or on specfic extracted sections.
         Preconditions have a css selector and regular expression the text of the
         selected element needs to match.         
         TODO: Error checking
      """
      # Condition name. Optional. Usually used to reference this condition
      # to build EVAL expressions.
      ecName: str = ''
      
      # ecBooleanOperator specifies the boolean operator to apply to this
      # condition.
      # TODO: This MUST be improved!
      #ecBooleanOperator: str =''

      ecCSSSelector: str = ''
      ecTextCondition: str = ''  # Regular expression
      ecRuleCSSSelector: str = '' # If not empty and conditionType is ANY, this will replace the rule's css selector. A way to conditionally apply selectors.

      ecAppliedCount: int = 0
      ecExistenceCount: int = 0
      ecTrueCount: int = 0
      ecFalseCount: int = 0
      
      def conditionHolds(self, htmlContent) -> bool:
          self.ecAppliedCount += 1  
          res = htmlContent.find(self.ecCSSSelector, first=False)          
          if len(res) <= 0:
             #print('[DEBUG] ConditionHolds: selector NOT FOUND')   
             self.ecFalseCount += 1   
             return(False)

          # Element found.
          self.ecExistenceCount += 1 

          # if no regular expression is present to match text but
          # element exists, assume that condition holds.
          if self.ecTextCondition.strip() == '':
             self.ecTrueCount += 1   
             return(True)

            
          # NOTE: Case sensitive support is specified at the regex level i.e.
          # using the (?i) flag  
          if re.search(self.ecTextCondition, res[0].text) is None:
             self.ecFalseCount += 1   
             return(False)
          else:
             self.ecTrueCount += 1    
             return(True) 




@dataclass
class ruleDynamicPageContent:
      dpcType: str = field(default='js') # 3 types supported with values: js for javasctipt functions, button for clickable page elements and scroll for scrollable elements
      dpcPageElement: str = field(default = '') # name of js function to execute, element name on page to click on or element to scroll
      dpcScrolldown: int = 0
      dpcWaitFor: str = field(default = '')
      



@dataclass
class ruleConditionList:
      conditionType: str = ''
      conditionList: List[extractionCondition] = field(default_factory=lambda:[])




      
# TODO: Remove this function
def makeRuleConditionList() -> ruleConditionList or None:
    return ruleConditionList()



@dataclass
class extractionRule:
    """Class for represeing one simple extraction rule."""
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

    

    # Preconditions applied to the ENTIRE PAGE
    rulePreconditionType: str = 'ANY'
    rulePreconditionExpression: str = ''
    rulePreconditions: List[extractionCondition] = field(default_factory=lambda:[])

    # TODO: Do we need this????
    # Preconditions applied to each extracted record from a SINGLE PAGE, when the rule
    # returns a recordlist i.e. a list of records from one single page.
    ruleMatchPreconditionType: str = 'ANY'
    ruleMatchPreconditions: List[extractionCondition] = field(default_factory=lambda:[])

    # Whether or not downloaded page should be rendered using HTMLSession's .render method
    # TODO: Very, very slow. Please dont set it to true in the current version.
    # NOTE: @11/06/2022: This has been moved to the library class. Was this correct?
    # ruleRenderPage: bool  = False
    
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



    
    '''
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
    '''


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
          


    def pagePreconditionsHold(self, htmlContent ) -> bool:
        try:  
           return( self.evalPreconditions(htmlContent)['status'] )
        except Exception as evalEx:
           print('Exception calling pagePreconditionHolds: ', str(evalEx))
           return(False)


          
    # Evaluating PAGE preconditions
    def evalPreconditions(self, htmlContent) -> dict:

        # If no preconditions are present, this means rule should be applied. 
        # TODO: Quck and dirty fix. Find a better way to do this.
        if  len(self.rulePreconditions) == 0:
            return({'status':True, 'cssselector':''})

        
        if self.rulePreconditionType.lower() == 'eval':

           # No boolean expression given although EVAL is specified.
           # This is considered as an error and False is returned.
           if self.rulePreconditionExpression.strip() == '':
              self.rulePreconditionFailedCount += 1   
              print('[WARNING] EVAL precondition type but empty expression.')   
              return(False)
                       
           evalExpression = self.rulePreconditionExpression.strip().lower()
           #print('>>> Expression:', evalExpression)
           # iterated over preconditions, evaluate them and replace the
           # precondition name with its evaluation valud
           for pc in self.rulePreconditions:
                 
               if pc.ecName.strip() == '':
                  print('[WARNING] precondition with empty name detected in EVAL type. Ignoring precondition.')
                  continue

               
               preconditionEval = pc.conditionHolds(htmlContent)               
               evalExpression = evalExpression.replace( pc.ecName.lower(), str(preconditionEval) )
               
           #print('>>> Expression after replacement:', evalExpression)

           # Keep in variable for debugging purposes ONLY!
           bResult = booleanEvaluation.evaluateBooleanExpressionString(evalExpression)
           #print('>>> Precondition EVAL result:', bResult)
           if not bResult:
              self.rulePreconditionFailedCount += 1
              
           #print('>>>>Returning:', {'status': bResult, 'cssselector':''})
           return( {'status': bResult, 'cssselector':''} )
           
               

               
      
        if self.rulePreconditionType.lower() == 'all':
           # This means all conditions must hold to apply rule
           for pc in self.rulePreconditions:
               #print('\t\t[DEBUG] [Mode ALL] Checking if precodition rule [', pc.ecCSSSelector, '] holds......', end='')
               if not pc.conditionHolds(htmlContent):
                  #print('NO')                  
                  self.rulePreconditionFailedCount += 1
                  return( {'status': False, 'cssselector':''} )

               #print('YES')
               
           return( {'status': True, 'cssselector':''} ) 

        if self.rulePreconditionType.lower() == 'any':
           # This means at least one condition must hold to apply rule   
           for pc in self.rulePreconditions:
               #print('\t\t[DEBUG] [Mode ANY] Checking if precodition rule [', pc.ecCSSSelector, '] holds......', end='')
               if pc.conditionHolds(htmlContent):
                  #print('YES')
                  if pc.ecRuleCSSSelector != '':
                     return( {'status': True, 'cssselector': pc.ecRuleCSSSelector})
                  else:
                      return( {'status': True, 'cssselector': ''} )
               #print('NO')

           self.rulePreconditionFailedCount += 1                   
           return( {'status': False, 'cssselector':''} )                   

                        
        print('\t\t[DEBUG] Unknown mode [', self.rulePreconditionType, ']')              
        return( {'status': False, 'cssselector':''} )






    def evalMatchPreconditions(self, record, debug=False):        
        print( utils.toString('\t\t[DEBUG] Evaluating MATCH preconditions. Total of [', len(self.ruleMatchPreconditions), ']\n') if debug else '', end='' )
        if len(self.ruleMatchPreconditions) <= 0:
           return({'status':True, 'cssselector':''})   


        for rpc in self.ruleMatchPreconditions:
            print( utils.toString('\t\t[DEBUG] Evaluating MATCH precondition [', rpc.ecCSSSelector, '] to [', record.text,'] ....') if debug else '', end='')
            #print('\t\t\t[DEBUG] for record', record)
            if rpc.conditionHolds( record ):
               print( utils.toString('YES. Returning [', rpc.ecRuleCSSSelector, ']\n') if debug else '', end='' )
               return( {'status': True, 'cssselector': rpc.ecRuleCSSSelector} )      

            print( utils.toString('NO\n') if debug else '', end='' )
        
        return( {'status': False, 'cssselector':''} )  



    
    # htmlContent must be html object from requests_html
    # TODO: Check this thoroughly. Also, refactor this...
    #       THIS IS A MESS. Has become so ugly. I'm sorry...
    def apply( self, htmlContent, debug=False ) -> dict:

        exTractedData = {}
        exTractedData['datatype'] = 'record'
        
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
        # Check if the PAGE preconditions hold
        preconStatus = self.evalPreconditions(htmlContent)
        print( utils.toString('\t[DEBUG] evaluation of PAGE preconditions for [', self.ruleName, '] (mode:', self.rulePreconditionType.upper(),') returned: ', str(preconStatus['status']).upper(), '\n') if debug else '', end='' )
        if not preconStatus['status']:
           # TODO: Since precondition does not hold,
           #       an empty value is assigned to key ruleName.
           #       Should we return an empty dictionary instead?  
           exTractedData[self.ruleName] = ''
           return(exTractedData)

        #print('\t\t[DEBUG] Precoditions hold. CSS Selector changed to [', preconStatus['cssselector'],']', sep='')
        
        self.ruleAppliedCount += 1

        # We are now applying the actual selectors or regular expressions

        if self.ruleTarget == 'js':
           # This rule targets a script. Enter script mode meaning
           # start executing the regular expression in ruleContentCondition
           # if the selector was nor replaced by a precondition. 
           print( utils.toString('\t\t[DEBUG] Extracting from script...\n') if debug else '', end='')
           if preconStatus['cssselector'] == '':
              return( self.extractFromScript(htmlContent, self.ruleContentCondition  ) )
           else:
               return( self.extractFromScript(htmlContent, preconStatus['cssselector']  ) )  


        
        # Apply the actual CSS selector        
        if preconStatus['cssselector'] == '':
           print( utils.toString('\t\t[DEBUG] Applying selector ', self.ruleCSSSelector,'...\n') if debug else '', end='')     
           res = htmlContent.find(self.ruleCSSSelector, first=False)
        else:   
            res = htmlContent.find(preconStatus['cssselector'], first=False)



        # Apply now the ruleMatchPreconditions for each matched result.
        
        #print('\t\t[DEBUG] Evaluating preconditions for EACH MATCH (', len(self.ruleMatchPreconditions), ' MATCH preconditions)', sep='' )
        if len(self.ruleMatchPreconditions) > 0:
            print( utils.toString('\t\t[DEBUG] rule MATCH Preconditions ', len(self.ruleMatchPreconditions),'\n') if debug else '', end='')
            print( utils.toString('\t\t[DEBUG] Total of ', len(res),' ruleCSSSelector matches...\n') if debug else '', end='')  
            pRes = []   
            for e in res:                
                pStatus = self.evalMatchPreconditions(e, debug)
                if pStatus['status']:
                   if pStatus['cssselector'] != '':
                      pRes.append( e.find( pStatus['cssselector'], first=True) )
                      #print(pRes)
                   else:
                      pRes.append(e)

            res = pRes

       # We have checked all conditions and preconditions. Now  


        
        if self.ruleTargetAttribute == "text":
            
             if not self.ruleReturnsMore:
                   
                 if self.ruleContentCondition != '': 
                    res = [m for m in res if re.search(self.ruleContentCondition, m) is not None ]
                 if len(res) <= 0:
                    #print("\t\t[DEBUG] Empty. No match present")
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
                       # in this situation, we get the element's text  
                       for e, name in zip(res, self.ruleReturnedValueNames):
                           exTractedData[name] = e.text.translate({ord(c): None for c in self.ruleRemoveChars})                         
                   else:
                       rsList = []  
                       for e in res:
                           d = {}  
                           for  subR, name in zip(self.rulePostCSSSelector, self.ruleReturnedValueNames):
                                
                                if e.find(subR, first=True) is None:
                                   d[name] = val  = ''
                                else:
                                   d[name] = e.find(subR, first=True).text   
                                

                           rsList.append(d)
                           print( utils.toString('\t\t\t[DEBUG] Got', d, '\n') if debug else '', end='')

                       exTractedData[self.ruleName] = rsList
                       exTractedData['datatype'] = 'recordlist'
                       
                   nM = len(res) * len(self.ruleReturnedValueNames)    
                 else:
                      # TODO: Get rid of rList and use exTractedData[self.ruleName] = [] etc
                      rList = []
                      for m in res:
                          if not m:
                             continue   
                          #print('\t\t[DEBUG] Appending ', m.text)  
                          rList.append( m.text.translate({ord(c): None for c in self.ruleRemoveChars}) )

                      exTractedData[self.ruleName] = rList
                      nM = len(rList)
                      #print(':::', exTractedData )

                 self.ruleMatchCount += nM     
                 return(exTractedData)
            
        else:
         # This is no simple text
         
         #print('\t\t[DEBUG] Total of ', len(res), '(', self.ruleName, ')')                  
           
         if len(res) <= 0:
            return(exTractedData)   

                   
         #print('>>>#####', res)          
         numExtracted = 0

         # TODO: The next commented out check must somehow be included. Does not work as intended whtn
         # getLinks rule is applied
         '''
         if self.ruleContentCondition != '': 
            res = [m for m in res if re.search(self.ruleContentCondition, m.attrs.get(self.ruleTargetAttribute)) is not None ]
         '''
         
         #print('\t\tNo TEXT.', res)                
         if self.ruleReturnedMatchPos >= 0:
            print( utils.toString('>>>>> Got  [', res[self.ruleReturnedMatchPos].attrs.get(self.ruleTargetAttribute), ']\n') if debug else '', sep='', end='' )
            exTractedData[self.ruleName] = res[self.ruleReturnedMatchPos].attrs.get(self.ruleTargetAttribute)
            numExtracted += 1
         else:
            #print(len(res), ' matches found')
            #print(res)
            lst = []
            for item in res:
                #print('\t\t\t\t[DEBUG] Doing', item)  
                #lst.append( item.text )
                if not item:
                   continue

                #print('\t\t\t[DEBUG] Getting attribute', self.ruleTargetAttribute, ' from item', item)  
                lst.append( item.attrs.get(self.ruleTargetAttribute) )
                #print('\t\t\t[DEBUG] Extracted:', item.attrs.get(self.ruleTargetAttribute) )

            #print(lst) 
            exTractedData[self.ruleName] = lst    
            numExtracted += len(res)

         return(exTractedData)    





'''
This class was crreated as a derived class from extractionRule.
Was not continued because need to study how dataclasses in Python
support inheritance.

TODO: Complete this. Or remove it.
'''
@dataclass
class scriptExtractionRule(extractionRule):
      scrptCaptureRegExp: str =''




@dataclass
class ruleLibrary:
      libraryDescription: str = ''
      library: List[extractionRule] = field(default_factory=lambda:[])

      # A list of ruleNames specifying the way the extracted data should
      # be formatted as a line when storing results in csv format
      csvLineFormat: List[str] = field( default_factory=lambda:[] )

      # Minimum percentage of non empty rules in extracted data allowed,
      # to consider the extraction a success. Below this pct, no
      # data is added to the csv file.
      # Valid values must be in range [0, 1]
      allowedMinimumFilled: float = -1.0

      # Extracted field names that MUST all be non-empty i.e. filled
      # to consider the extraction process a success and 
      # the data be written to the csv file.
      requiredFilledFields: List[str] = field( default_factory=lambda:[] )


      
      # Whether or not downloaded pages should be rendered using HTMLSession's .render() method
      # If set to True, all downloaded pages will be rendered
      # TODO: Seems to be very, very slow. Be careful when setting is to true.
      renderPages: bool = False

      # A list of dynamic elements i.e. js scripts and buttons on html page, that need to be executed or clicked/pressed after the
      # page has been loaded and before parsing of the page in order to render properly the page.
      # Currently, works only if the fetch method is dynamic i.e. renderPages is True.
      #
      # IMPORTANT: Elements/buttons are executed/clicked in the order in which they appear in this list.
      ruleDynamicElements: List[ruleDynamicPageContent] = field(default_factory=lambda:[])



      # HTTP request related variables
      
      requestCookies: Dict[str, str] = field(default_factory=dict)
      requestUserAgent: str = ''
      
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

      def applyAllRules(self, pageUrl, pageHtml, debug=False) -> dict:
            
          pageData = {}
          for i, r in enumerate(self.library):
                 #print( utils.toString('\t\t[DEBUG] Total of [', str(len(extractedLinks)), '] links extracted\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')
                 print(utils.toString('>>> Applying rule [', r.ruleName, ']\n') if debug else '', end='' )
                 print( utils.toString('\t[DEBUG] Checking if URL pattern matches activation constraints of [', r.ruleName,'].......') if debug else '', end='')
                 if not r.ruleMatches(pageUrl):
                    print( utils.toString('NO\n') if debug else '', end='')   
                    continue
                  
                 print( utils.toString('YES\n') if debug else '', end='')   
                 
                 xrd = r.apply(pageHtml, debug)
                 pageData.update( xrd )
          
          return(pageData)       
          #pass

      '''
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
      ''' 



      # Filter from xD (the data extracted by rules)
      # the fields/keys that are mentioned in the rule's csvLineFormat
      # to produce the data that is to be added to the csv file as one line.
      # Checks also if extracted data meets the library's constraints that
      # determine if the extraction process was successful.
      #
      # xD: dictionary with extracted data as they originated by applying all rules.
      # reqFilled: List of required fields that must be non-empty (get value from
      # field requiredFilledFields in .exr files
      # minFilled: minimum percentage of fields that need to be non empty. Gets value
      # from allowedMinimumFilled in .exr files. Defaults to -1 meaning no minimum
      # percentage.
      def CSVFields(self, xD, reqFilled=[], minFilled=-1, debug=False) -> dict:
          return( self.toDict(xD, reqFilled, minFilled, debug) )


      # minFilled: percentage of keys that must not be empty in order
      # to consider an extraction to have succeeded.
      def toDict(self, xD, reqFilled=[], minFilled=-1, debug=False) -> dict:
          dct = {}
          nonEmpty = 0
          if minFilled > 1:
             minPctFilled = 1
          else:
              minPctFilled = minFilled

          found=0 # number of fields found in extracted data
          for i, nm in enumerate(self.csvLineFormat):
              if xD.get(nm) is None:
                 continue

              found += 1
              if isinstance(xD[nm], str):
                 dct[nm] = xD[nm].strip()
                 if dct[nm] != '':
                    nonEmpty += 1
              else:
                   # Assuming its a list.
                   # Only 2 data types valid here: str or list
                   dct[nm] = xD[nm]
                   if dct[nm]:
                      nonEmpty += 1   
          

                  
          print( utils.toString('\t[DEBUG] Checking if data ', dct, ' meets constraints.\n') if debug else '', sep='', end='' )

          # Now check if there are any constraints.
          print( utils.toString('\t[DEBUG] Required non-empty fields: ', reqFilled, '\n') if debug else '', end='', sep='' )

          # First, check if required fields are non empty.
          if reqFilled:
             for k in reqFilled:
                 # if field is a list, the list must be non empty.
                 if isinstance(dct.get(k, ''), list):
                    if not dct[k]:
                       return( {} )
                  
                 if dct.get(k, '') == '':
                    print( utils.toString('\t[DEBUG] Required field [', k, '] empty. Returning empty data.\n') if debug else '', end='', sep=''  )   
                    return({})

          

          # Check if minimum amount of keys is filled      
          print( utils.toString('\t[DEBUG] Total of ', found, ' fields found. NonEmpty:', str(nonEmpty), ' (pct filled:', '{:.2}'.format(nonEmpty/found) if found != 0 else '---', ') min:', str(minFilled), '\n' ) if debug else '', end='', sep='' )
  
          if float('{:.2}'.format(nonEmpty/found) if found !=0 else -666 ) < minFilled:    
             print( utils.toString('\t[DEBUG] Not adding ', dct, ' (pct filled:', '{:.2}'.format(nonEmpty/found) if found != 0 else '---', ' minFilled:', str(minFilled), ')\n') if debug else '', sep='', end=''  )  
             return( {} )
            
          return(dct)    



      def libStats(self) -> bool:
          print('Library statistics for current run:')
          for xr in self.library:
              print('\tRule:', xr.ruleName)
              print('\t\tMatched URLs count:', xr.ruleMatchedUrlsCount)
              print('\t\tRule applied count:', xr.ruleAppliedCount)
              print('\t\tRule match count:', xr.ruleMatchCount)
              print('\t\tFailed precondition count:', xr.rulePreconditionFailedCount)
              print('\t\tPreconditions (total:', len(xr.rulePreconditions),', mode:', xr.rulePreconditionType, '):', sep='' )
              for i, r in enumerate(xr.rulePreconditions):
                  if r.ecName == '':  
                     print('\t\t\tPrecondition ', i, ' :: Applied:', r.ecAppliedCount, ' Found:', r.ecExistenceCount, ' True count:', r.ecTrueCount, ' False count:', r.ecFalseCount, sep='')
                  else:
                     print('\t\t\tPrecondition ', r.ecName, ' :: Applied:', r.ecAppliedCount, ' Found:', r.ecExistenceCount, ' True count:', r.ecTrueCount, ' False count:', r.ecFalseCount, sep='')
                     
              

          return(False)    




# General purpose functions
def loadRule( r ):    
    rl = dataconf.loads(r, extractionRule)
    return(rl)

def loadLibrary(r):      
    return( dataconf.loads(r, ruleLibrary) )






# The next two functions are borderline stupid. But i
# could not come up with a better solution in a short
# amount of time i had.
#
# TODO: Needs to go.  Has to be replaced by a better
# and more thought out model.
#
def isRecordData( xd ):
    for k,v in xd.items():
        if type(v) == list:
           if len(v) <= 0:
              continue   

           if type(v[0]) == dict:
              return(False)

    return(True)        


def isRecordListData( xd ):
    nFound = 0  
    for k,v in xd.items():
        if type(v) == list:
           if len(v) <= 0:
              continue   

           if type(v[0]) == dict:
              print('\t\t[DEBUG] Key', k, 'is record list.')   
              nFound  += 1

    if nFound == 0:
       return(False)
    elif nFound == 1:
         return(True)
    else:
          print('Serious error. You should never see this. Need to terminate.')
          sys.exit('Fatal error. Terminating.')




# Returns the key name that is a record list i.e.
# a list of dictionaries.
# This functions returns the first key encounterred that
# is a record list.
def getRecordListFieldName(xd):
    for k,v in xd.items():
        if type(v) == list:
           if len(v) <= 0:
              continue   

           if type(v[0]) == dict:
              return(k)  # Return first. There can only be one. 

    return(None)          
