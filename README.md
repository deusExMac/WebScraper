# About WebScraper
 
WebScraper is a simple python program enabling rule-based scraping/extraction of data from web pages. Rules specifying what part of a page to extract from individual web-pages pages are stored .exr files ((EX)traction (R)ules). Each .exr file contains one or more extraction rules, collectively called an extraction library or just library, that will be applied to a single web-page if certain rule-specific condition hold. 


**IMPORTANT: This software is currently in beta release and under heavy development. This means features may not work, may work inconsistently, are only implemented as a proof of concept and (may) have serious bugs.**


# Required python modules

Make sure you have the following python packages installed before running the application:

* requests_html (https://requests.readthedocs.io/projects/requests-html/en/latest/)

* requests

* pyppeteer (https://miyakogi.github.io/pyppeteer/)

* pandas

* dataconf (https://pypi.org/project/dataconf/)

* clrprint (https://pypi.org/project/clrprint/)

* asyncio

* pyppdf

* tldextract

* pyjokes


# .exr files


.exr files are files in json format defining the extraction rules that shoould be applied to a web page.  Since .exr are json formatted files that can be edited with a simple text editors. exr files are encoded in utf-8. If the file encoding changes, this may have an effect on the result returned by rules. During an Web scraping process, one the exr file defining the extraction rules that will be applied ti the downloaded pages can be specified. Exactly one exr file can be specified during a Web scraping session.

All the rules specified in an exr file will be applied to the same downloaded web-page if the rule-specific conditions hold, before moving on to the next page which triggers again the application of the rules of the library. Each rule in a exr file is responsible for extracting only one specific kind of data  (e.g. title, links, div content, specific html elements etc) from a downloaded page, if rule specific conditions hold. Rules return the extracted data as strings. One rule may return only one string value, return a list of string vaues or a list of objects. If a rule is not applied the rule returns an empty string.

Each rule in an .exr file specifies the conditions the page must meet in order to apply the rules, the data to extract, the conditions the extracted data must meet and how to return the extracted data. Such specfications are referred to as 'extraction rules' and  a set of extraction rules is called an extraction libraries. Extraction libraries are stored in .exr files in JSON format. All rules inside an .exr files are applied to each individual page downloaded from the Web, when rule-specific conditions are met.

In general, .exr files, when applied to content (web-page) downloaded from the WWW, attempt to extract the data according to the following scenario:

*"Once a Web page has been downloaded do the following for each rule inside the current .exr file:  If the web-page URL matches the rule's activation condition, check if the web-page's content matches zero or more page preconditions. If all these page conditions hold, extract the data from the web-page specified by a CSS selector. If preconditions do not hold, do not extract data and return empty data (1 <--footnote for better description). After extraction, Check if the extracted data meets other preconditions. If so, return it as the extracted/scraped data. If not, return empty extracted/scraped data."*   

The above description sumplifies the process but attempts to give the general idea. 
The overall idea is that each individual rule inside a library when applied to a downloaded web page is responsible of extracting only one particular kind of data from the web page which it returns in the form of key:value.
.exr files when applied to a URL and may return: 1) a single record containing the extracted data as values of keys for a given web page or 2) a list of records containing the extracted data as values of keys for a single page.

During WebScraper's startup the preferred .exr file can be specified via the -r option on the command line. If no .exr file is specified, the default extraction rules file default.exr is loaded. If no .exr file is loaded, WebScraper does not start. 

.exr files can also been set as arguments during individual commands in the application's shell. The used .exr file and all the rules it contains are applied to each individual page that the application downloads. Currently only one .exr can be specified and used during the extraction process.

Authoring .exr files requires basic knowledge of [css selectors] (https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) and [regular expressions](https://www.regular-expressions.info/).

## .exr files: Supported fields

 

TODO: library extraction files have been  updated with new properties. Make changes here!
Below is an example of a .exr file that is used to extract data related to football teams from wikipedia pages. It contains 4 rules that will be applied to all wikipedia pages downloaded.

```
#######################################################################################################################################################
#
# Template listing all supported fields.
#                    
# 
#
#
# 
# v0.1@14/10/2022
#
########################################################################################################################################################



{

# Description of the library

"libraryDescription": "",
"csvLineFormat":[],
"requiredFilledFields": [<RULE NAME | RETURNED VALUE NAME (recordlist)>, <RULE NAME | RETURNED VALUE NAME (recordlist)>],
"allowedMinimumFilled" : <REAL NUMBER IN RANGE [0,1]>,
"renderPages":True|False,

"launchParameters" : { "executablePath":"<PATH TO BROWSER>", "userDataDir" : "<PATH TO USER DIRECTORY>" },

"requestCookies": {
                   <COMMA SEPARATED key-value pairs with format: "KEY":"VALUE". Keys and values must be strings and in double quotes. key-value pairs must be separated by commas. >
                   
                   Example:
                   
                   "CONSENT": "YES+cb.20211005-08-p0.en+FX+206" 
                   },

"requestUserAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",


"requestHeader": {
                   <COMMA SEPARATED key-value pairs with format: "KEY":"VALUE". Keys and values must be strings and in double quotes. Many key-value pairs should be separated by commas.>
                   
                   Examples:
                   
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                   "Accept-Encoding": "gzip, deflate, br",
                   "Accept-Language": "en-US,en;q=0.5",
                   "Connection": "keep-alive",
                   "Sec-Fetch-Dest":"document",
                   "Sec-Fetch-Mode":"navigate",
                   "Sec-Fetch-Site":"none",
                   "Sec-Fetch-User":"?1",
                   "Upgrade-Insecure-Requests": "1" 
                   },

"ruleDynamicElements": [ 

          Examples:
           
		 {
		     "dpcType":"<'click' | 'js' | 'fill' | 'scrollpage' | 'scroll'>",
		     "dpcPageElement":"",
		     "dpcScrolldown":<INTEGER>,
		     "dpcWaitFor":"",
		     "dpcFillContent": "",
		     "dpcURLActivationCondition":"",
		     "dpcIsSubmit": True|False,
		     "dpcRedirects" : True | False
		     "dpcScrollTargetElementCount" : { "scrollTargetSelector": "", "scrollTargetCount":"<INTEGER>" },		     
		 },
		 
		 {
		     "dpcType":"<'click' | 'js' | 'fill' | 'scrollpage' | 'scroll'>",
		     "dpcPageElement":"",
		     "dpcScrolldown":<NUMBER>,
		     "dpcWaitFor":"",
		     "dpcFillContent": "",
		     "dpcURLActivationCondition":"",
		     "dpcIsSubmit": True|False,
		     "dpcRedirects" : True | False
		     "dpcScrollTargetElementCount" : { "scrollTargetSelector": <CSS SELECTOR>, "scrollTargetCount":"<INTEGER>" },		     
		 }

		 # Next dynamic element here... dynamic elements separated rules by comma.
],







######################################################################################
#
#  List of library rules starts from here. Each rule
#  is responsible for scraping one item from a webpage: this item
#  can be a value, list of values or list of dictionaries (i.e. recordlist). 
#  
#
######################################################################################

"library": [

   {
        
        # Rule definition starts here
        
        "ruleName": "<MUST BE UNIQUE>", 
        "ruleDescription": "Extracts ....",
        "ruleURLActivationCondition": ["youtube\.com", "wikipedia\.com[\]$"],
        "ruleTarget": <'html' | 'js'>,
        
        "rulePreconditionType": <'ANY', 'AND', 'EVAL'>,
        "rulePreconditionExpression": 'p1 AND p2 AND p3 AND ( (p4 AND p5) OR (p6 AND p7) OR (p8 AND p9) ) <ONLY IN CASE OF EVAL>',
        
        "rulePreconditions" : [ 
	                          {
	                             
	                             "ecName": "p1",
	                             "ecCSSSelector" : "#mw-normal-catlinks", 
	                             "ecTextCondition" : "(?i)\bphysicists\b"
                              },
                                  
                              {
				  	                             
				                 "ecName": "p2",
				                 "ecCSSSelector" : "#mw-normal-catlinks", 
				                 "ecTextCondition" : "(?i)\bphysicists\b"
                              }
                                  
                                  # Next rule precondition here... rule precondition separated rules by comma.
                          
                             ] , # end of rule preconditions
       
       
       
       
        "ruleCSSSelector": "a[href]", 
        "ruleTargetAttribute": "href" <ELEMENT ATTRIBUTE | 'text'>,
 
 
 
        "ruleMatchPreconditionType": <'ANY'>,
        "ruleMatchPreconditions": [
  	                                 
	                                 {
	                                   "ecCSSSelector" : "td:nth-child(2)", 
	                                   "ecTextCondition" : "([4-9]|\d{2,})",
	                                   "ecRuleCSSSelector" : "th a[href]:nth-child(2)"
	                                 }
	                                 
	                                 # Next match precondition here... match precondition separated rules by comma.
	     
                                  ], # end of rule MATCH preconditions
        
        
        
        
        "rulePostCSSSelector" : ["th", "td:nth-child(2)", "td:nth-child(3)", "td:nth-child(4)" <LIST OF CSS SELECTORS APPLIED TO ruleCSSSelector>]
        
        "ruleReturnedValueNames" : ["name", "winnerCount", "runnerUpCount", "seasonsWon" <VARIABLE NAMES, STORING CORRESPONDIVE VALUES OF rulePostCSSSelector>]
 
 
 
 
        "ruleContentCondition": '<REGEX>',
 
 
        "ruleReturnsMore": True | False,
        "ruleReturnedMatchPos": <NUMBER EXPRESSING POSITION OF ELEMENT TO RETURN. -1 FOR ALL elements>,
        "ruleReturningMoreIsError": True | False <CURRENTLY NOT USED>,
 
        "ruleRemoveChars": [],
        
   } # end of rule

   
   
   # Next rule here... Don't forget: separate rules by comma.
   

] # list of rules


} # library

```

## Structure of rules in .exr file

-``[libraryDescription]``: A human readable description of the .exr file. What it is used for etc.
-``[csvLineFormat]``: List of rule names (string - see below) that specify the extracted data from which rules should be stored in .csv files.
-``[renderPages]``: If downloaded html pages should be rendered i.e. 
-``[library]``: list of rules defining this library.


Rule attributes/properties:

- ``[ruleName]``: String. Name of the rule. In the current version, rule names should not contain spaces. Rule names are important as these names are used to store extracted values, by that rule, with these keys in python dictionaries.
- ``[ruleDescription]``: String. A human readable description of the rule's aim i.e. what it does. 
- ``[ruleURLActivationCondition]``: List of regular expressions.  List of regular expression that the URL of the web page must match. Rule is applied if ANY of the regular expressions in this list is matched. If no regular expression is matched, rule if not applied. If this list is empty, rule is applied. Example: ruleURLActivationCondition: ["en\.wikipedia\.org", "C://downloadedPages//"] meaning if URL matches en.wikipedia.org or C://downloadedPages//, then apply this rule. If URL (or file name) does not match any of regular expressions in this list rule will not applied. NOTE . is escaped as it is also a metacharacter.
- ``rulePreconditionType``: Values ``Any`` or ``All`` . Specifies if all preconditions (all) or at least one  (any) the content must hold in order for the rule to be applied. Preconditions are specified in the rulePreconditions property (see below)
- ``rulePreconditions``: List of preconditions. Each precondition has the following properties:
    - ``ecCSSSelector``: String. Specifies a CSS selector on content of the web pages.
    - ``ecTextCondition``: String. Regular expression. The regular expression the text of css selector ``ecCSSSelector`` has to match. if matched, the precondition is evaluation to True and hence holds.
    - ``ecRuleCSSSelector``: String. CSS selector. If non-empty and precondition matches and ``rulePreconditionType`` is any, the CSS selector specified here will replace the CSS slector of this rule (``ruleCSSSelector``) 
- ``ruleCSSSelector``: String. CSS selector. The CSS selector to extract actual data from the web page if conditions hold (URL regular expression and preconditions). This is the sought after data. Can be ovewritten by ``ecRuleCSSSelector`` under specific circumstances (see ``ecRuleCSSSelector``)
- ``ruleTargetAttribute``: String. Attribute of the ``ruleCSSSelector`` element to return as the extracted data. If equal to ``text`` the text of the element is returned. Otherwise the named attribute of the CSS element.
- ``ruleContentCondition``: String. Regular expression. The regular expression the extracted data has to match. If extracted data matches this regular expression, extracted data is returned. If not, empty extracted data is returned.
- ``ruleReturnsMore``: Boolean. True or False. Specifies if CSS selector ``ruleCSSSelector`` will return more than one matching result.
- ``ruleReturnedMatchPos``: Integer. If ``ruleReturnsMore``is True, this specifies which result to return as valid match.
- ``rulePostCSSSelector``: css selector. TODO: Fill this....
- ``ruleReturnedValueNames``: List of strings. Specifies +++
- ``ruleMatchPreconditions``: List of [rule preconditions] . These preconditions will be applied after application of ruleCSSSelector and on each match returned by ruleCSSSelector. These preconditions allow users to apply more complicatied conditions on matches. ruleMatchPreconditions may even replace a match returned with another. Currently only disjunctive match preconditions are supported. 
- ``ruleMatchPreconditionType``: ANY | AND. How the match preconditions specified in ruleMatchPreconditions should be combined (currently ANY, AND values supported.)

IMPORTANT: Some properties are not fully supported and/or may result in errors and exceptions. 

# Order of checks carried out as specified by rules in exr files

When applying rules to html file, checks and extraction is carried out in the following order for each rule in the exr file:

## i. ruleURLActivationCondition 

First url of downloaded page is checked if it matches any of the regular expression specified in ruleURLActivationCondition.
if URL of downloaded resource does not match any regular expression in ruleURLActivationCondition, rule is not applied. Otherwise rule continues.

## ii. rulePreconditions

Then page rule preconditions are applied. The expression in page preconditions, which check if the html content meets the css element conditions specified in rulePreconditions, is evaluated. If evaluation of page preconditions return False, the extraction specified by the rule stops.  Otherwise, it continues. NOTE: page preconditions may overwrite the ruleCSSSelector.

## iii. ruleCSSSelector

ruleCSSSelector extracts the actual target (sourght after) information from the downloaded page. Specified ruleCSSSelector may be overwritten by rulePrecondition. May return a single value or a set/list of values (specified by ruleReturnsMore).

## iv. ruleMatchPreconditions

If specified, on the result set returned by ruleCSSSelector, the ruleMatchPreconditions are applied. These check if each result match a very specific condition. Results that do not meet the conditions specified by ruleMatchPreconditions are removed from the ruleCSSSelector result set and not returned. Although more than one match precondition can be specified, only the ANY operator (s supported (i.e. ruleMatchPreconditionType can only take value ANY). Match preconditions are applied to the results after the extraction process in contrast to page preconditions that are applied before.

## v. ruleContentCondition

If specifies, the regular expression specified in ruleContentCondition is applied to all extracted content in the result set. If ruleContentCondition is  empty, no conditions are enforced on the extracted content i.e. the rcurrent esult set is unafected.


## vi. rulePostCSSSelector

If specified, it applies the css selector list specified in rulePostCSSSelector to cut each and every element of the results set returned by ruleCSSSelector into smaller pieces. May return a list of strings or a list of dictionaries. List of dictionaries are returned, if field ruleReturnedValueNames is specified which has a list of strings acting as keys corresponding to the css selectors one-by-one in rulePostCSSSelector.   


After these steps, the result set is returned as the value of the extracted information after applying one single rule. As already mentioned, the idea of exr files is that each rule extracts one specific information of the downloaded Web page.


# Related projects

To make life easier, you may use the following extensions to extract the relevant css selectors that are required in .ecr files:

* Chrome extension SelectorGadget to specify CSS seslectors used in .exr files. See: https://chrome.google.com/webstore/detail/selectorgadget/mhjhnkcfbdhnjickkkdbjoemdmbfginb?hl=en and   https://selectorgadget.com/   

* Firefox extension ScrapeMate. See https://addons.mozilla.org/en-US/firefox/addon/scrapemate/
