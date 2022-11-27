# About WebScraper
 
WebScraper is a simple python program enabling rule-based scraping/extraction of data from html web pages. Rules specifying what part of a page to extract from individual web-pages pages are stored exr files ((EX)traction (R)ules). Such files can be recognized in this distribution by the extension .exr . Each exr file contains one or more extraction rules, collectively called an extraction library or just library, that will be applied to a single web-page if certain rule-specific condition hold. 


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


exr files are files in json format defining the extraction rules that should be applied to a web page.  Since .exr files are json formatted, they can be edited with a simple text editors. exr files are encoded in utf-8. If the file encoding changes, this may have an effect on the result returned by rules. During an Web scraping process, one exr file defining the extraction rules that will be applied to downloaded pages can be specified. Exactly one exr file must be specified when WebScraper starts executing. In the current version, WebScraper supports only the loading and application of one exr file during execution.

All the rules specified in an exr file will be applied to the same downloaded web-page if the rule-specific conditions hold, before moving on to the next page which will trigger again the application of the rules of the library. 

TODO: Fix below picture... 

![alt text](https://github.com/deusExMac/WebScraper/blob/main/doc/procOutline.jpg?raw=true)


		   Download one 
	      |->  page
	      |	       |
	      |	       |
	      |	       |
	      |	   Apply all rules 
	      |    in the loaded exr
	      |	   file
	      |	       |
	      |	       |
	      |	       |
	      |	   Process the extracted 
              -----data    


Each rule in a exr file is responsible for extracting only one specific kind of data  (e.g. title, links, div content, specific html elements etc) from a downloaded page, if the rule specific conditions hold. Each rule returns all the extracted data as strings. Every extraction process applied on downloaded pages needs to be considered and expressed as a rule in the exr file. Even the extraction of links, when WebScraper crawls a site, must be expressed as a specific rule in the exr file and must have the very specific name ```getLinks``` (this is because such rules are handled  differently by WebScraper). Currently, extraction is supported only from html resources.  

Each rule returns the extracted/scraped data always as a string. Rules may return only one string value as the result of the extraction, return a list of string values or a list of objects. If a rule is not applied, an empty string is returned.

Each rule in an exr file may specify a set of optional preconditions the page must meet in order to apply the rule. These preconditions may refer to the downloaded page's URL and its content. If these rule preconditions hold the rule is applied and the specified element extracted; if preconditions do not hold, the rule is not applied and an empty value is returned as the rule's extraction value. If no preconditions have been specified, the rule is applied on the page. 

In general, exr files, when applied to content (web-page) downloaded from the WWW, attempt to extract the data according to the following scenario:

*"Once a Web page has been downloaded do the following for each rule inside the current exr file:  If the web-page do not match the rule's preconditions do not apply the rule and return an empty value. Otherwise, extract the data from the web-page specified by a CSS selector. After extraction, check if the extracted data meets other conditions. If so, return it as the extracted/scraped data. If not, return empty extracted/scraped data."*   

A rule may also specify conditions (post conditions) that are applied on data after these have been extracted from a page; if post-conditions are specified in a rule, only the extracted data meeting these post-conditions will be returned.


Authoring rules in exr files requires basic knowledge of [css selectors] (https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) and [regular expressions](https://www.regular-expressions.info/).

Besides rules, exr files can also specify/dioctate other aspects of the extraction process such as how to render/fetch the page, what HTTP headers and/or cookies to use, if and how to interact with the downloaded page (e.g. scrolling, filling boxes, clicking etc) before applying the rules etc.


# .exr files

## Overview of exr file
 
Below is an overview of an exr file, presenting all supported fields. The supported fields are explained in greater detail in this section.


```

########################################################################################################################################################
#
# Template listing all supported fields in exr files.
#                    
# 
#
#
# 
# v0.5@14/10/2022
#
########################################################################################################################################################



{

# Description of the library

"libraryDescription": <string>,
"csvLineFormat": <list of strings specifying rule names>,
"requiredFilledFields": <list of strings specifying rule names>,
"allowedMinimumFilled" : <float>,
"renderPages":<True|False>,

"launchParameters" : { "executablePath":"<path to chrome browser on local machine>", "userDataDir" : "<path to user directory>" },

"requestCookies": {
                   <comma separated "key":"value" pairs (strings)> 
                   },

"requestUserAgent": <string>,


"requestHeader": {
                   <comma separated "key":"value" pairs (strings)> 
                   },

# list of dynamic elements
"ruleDynamicElements": [ 

               
                  <list of comma separated dynamic elements>

                 # dynamic element 
		 {
		     "dpcType":"<'click' | 'js' | 'fill' | 'scrollpage' | 'scroll'>",
		     "dpcPageElement":<string, css selector>,
		     "dpcScrolldown":<integer>,
		     "dpcWaitFor":"<string, css selector>",
		     "dpcFillContent": "<string css selector>",
		     "dpcURLActivationCondition":"<string, regular expression>",
		     "dpcIsSubmit": <True|False>,
		     "dpcRedirects" : <True | False>
		     "dpcScrollTargetElementCount" : { "scrollTargetSelector": <string, css selector>, "scrollTargetCount":"<integer>" },		   
		 }

		 
],




######################################################################################
#
#  List of library rules starts from here. Each rule
#  is responsible for scraping one item from a webpage: this item
#  can be a value, list of values or list of dictionaries (i.e. recordlist). 
#  
#
######################################################################################

# list of comma separted rules to apply on every page
"library": [

   {
        
        # Rule definition starts here
        
        "ruleName": <string>, 
        "ruleDescription": <string>,
        "ruleURLActivationCondition": <list of regular expressions>,
        "ruleTarget": <'html' | 'js'>,
        
        "rulePreconditionType": <'ANY' | 'AND'|'EVAL'>,
        "rulePreconditionExpression": <string>,
        
        "rulePreconditions" : [ 
	                          {
	                             
	                             "ecName": <string>,
	                             "ecCSSSelector" : <string, css selector>, 
	                             "ecTextCondition" : <string, regular expression>"
                              },
                                  
                
                          
                             ] , # end of rule preconditions
       
       
       
       
        "ruleCSSSelector": <string, css selector>, 
        "ruleTargetAttribute": <string, element attribute | text>,
 
 
 
        "ruleMatchPreconditionType": 'ANY',
	
	<comma separated match preconditions>
        "ruleMatchPreconditions": [
  	                                 
	                                 {
	                                   "ecCSSSelector" : <string, css selector>, 
	                                   "ecTextCondition" : <string, regular expression>,
	                                   "ecRuleCSSSelector" : <string, css selector>
	                                 }
	                                 
	                                 # Next match precondition here... match precondition separated rules by comma.
	     
                                  ], # end of rule MATCH preconditions
        
        
        
        
        "rulePostCSSSelector" : <list of css selectors>,
        
        "ruleReturnedValueNames" : <list of names, one for each css selector in rulePostCSSSelector>,
 
 
 
 
        "ruleContentCondition": <string, regular expression>,
 
 
        "ruleReturnsMore": True | False,
        "ruleReturnedMatchPos": <integer>,
        "ruleReturningMoreIsError": True | False,
 
        "ruleRemoveChars": <list of characters or string>,
        
   } # end of rule

   
   
   # Next rule here... Don't forget: separate rules by comma.
   

] # list of rules


} # library

```


## Fields in .exr files

-``libraryDescription``: A human readable description of the .exr file. What it is used for etc.

-``csvLineFormat``: List of rule names (string - see below) specifies the rule names the extracted data of whose should be stored in the .csv files. E.g. if value is ["pageTitle"] this means that in the csv file only the extracted value of rule pageTitle will be stored. WebScraper tags extracted data with the rule name that extracted the data. If an empty list is specified, nothing is written in the csv file.

-``requiredFilledFields``: List of strings. List of rule names that must extract non-empty data from a page in order to consider the extraction process successful and the data be written in the csv file.  If at least one rule (indentified by rule name) in this list returns an empty value, the extraction process is unsuccessfully and nothing is written in the csv file. Default value [] (empty list).

-``allowedMinimumFilled``: floating point numner. Minimum percentage of extracted rule names that must extract a nono-empty value. If this value is 0.8 this means that the extraction process is successful if 80% of rules extracted non-empty value. If < 80% of rules extracted non-empty values, the extraction process is unsunccessful and nothing is written in the csv file. A negative value disables this setting. Default value -1.    


-``renderPages``: True | False. Specifies how the WWW page should be downloaded: using simple HTTP method or using a browser engine (Chromium or Chrome). If set to True, Chromium (the default build-in browser of [pyppeteer](https://github.com/pyppeteer/pyppeteer) ) or Chrome will be used. Defaults to False.


-``launchParameters``: object literal. Specifies using an **external Chrome browser installation** in headless as the rendering engine (instead of pyppeteer's build-in Chromium) to download web pages. The associated value specifies location of the Chrome broser on the local machine along with the user data directory. The object literal has the following fields:

   * ``executablePath``: path to Chrome executable on local machine
   * ``userDataDir``: path to OSs user directory. Need to specify this if WebScraper is executed on Windows. On Mac, this field can be ommited.

If ``launchParameters`` is empty i.e. not specified and renderPages is set to True, pyppeteers build in Chromium browser will be used. Defaults to an empty object.

*NOTE: The version of pyppeteer used by WebScraper has a build-in Chromium browser that is not able to render properly some pages. E.g. pyppeteer's Chromium does not properly render pages of airbnb listings and hence loading of these pages fail. In such cases using an external Chrome installation solves the issue. With respect to this, [see issue #27](https://github.com/deusExMac/WebScraper/issues/27)*


-``requestCookies``: json object literal with arbitrary key:value pairs. Specifies the request cookies that should be used with every HTTP request. Cookies should be specified in the form of comma separated  "cookieName":"cookieValue" pairs. If not specified, no request cookie will be set during reguests. If set, these cookies will be used for ALL requests issued on the server: no URL filtering is carried out.  Defaults to {} i.e. empty cookie json object i.e. no cookie.

-``requestHeader``: json object literal with arbitrary key:value pairs. Sepecifies the HTTP header lines that will be used during requests. These header lines will replace lines of existing fields or add new ones. Any HTTP header line can be set, except the first request line (GE/POST). Header lines should be specified in the form of comma separated "field":"value" pairs e.g. "Accept-Language": "en-US,en;q=0.5" . field:value pairs should be in double quotes. If not specified, default header lines will be used. Defaults to {} i.e. no modification/addition to header lines. 


-``requestUserAgent``: string. Sepecifies the user agent to use during HTTP requests. Overwrites the User-Agent line if this is set in the requestHeader field. If not specified, the default User-Agent is used. Defaults to empty string which results in using the http requests or browser's default user-agent.


-``ruleDynamicElements``: list of json object literals. Specifies the list of operations to apply on the downloaded page before applying the rules in the exr file i.e. the extraction process. Each json object literal in the list specifies one action to carry out on a downloaded page. These operations are applied only if renderPages is set to True i.e. a rendering engine is used to download the pages. If renderPages is set to False, no operation is carried out on page and this field is ignored. Operations in this list will be qpplied on the page in the order in twhich they appear in this list (i.e. first operation will be executed first, then second, then third etc). If one operation cannot be applied or returns error, the execution of other, subsequent operations will continue. 

The object literal specifying an operation on the page has the following fields:

   * ``dpcType``: One of: ['click' | 'js' | 'fill' | 'scrollpage' | 'scroll']. Operation to apply on page or element. Supported values and operations they will invoke:
     * *click*: Used when the operation denotes a click on an element. 
     * *js*: Special value to indicate execution of a javascipt function. Has not been tested. Use with caution.
     * *fill*: Filling an input element with some specified value
     * *scrollpage*: Scrolling the entire web page/browser viewport
     * *scroll*: Scrolling an html element (not entire page) that is scrollable e.g.  div, subwindow, textarea etc
     
   * ``dpcPageElement``: css selector. On which html element on the downloaded page to perform operation specified in ``dpcType``.
   * ``dpcScrolldown``: integer > 0. How many times to scroll an html element (specified by ``dpcPageElement``) or the entire page (scrollpage). Scrolling using this option does not check if elements appear on page: it just scrolls element or entire page without any test or control. If integer is <= 0, scrolling is disabled. Default value 0.
   * ``dpcScrollTargetElementCount``: json object literal. Specifies scrolling until a specific count/number of css elements will appear. Json object literal has the following fields: ``dpcType``.
     * ``scrollTargetSelector`` css selector defining the elements to count
     * ``scrollTargetCount`` number of html elements defined by ``scrollTargetSelector`` that must appear before stopping (exact value cannot always be guaranteed as scrolling may load many such elements). If ``scrollTargetCount`` is negative, this means infinite scrolling i.e. scrolling until no new elements appear. This is the only way infinite scrolling is supported. If boh ``dpcScrolldown`` and ``dpcScrollTargetElementCount`` is specified, ``dpcScrollTargetElementCount`` takes precedence. Defaults to an empty json object meaning no scrolling target count.
     * ``dpcWaitFor`` string. CSS element. The element to wait for to appear, when operation is scroll or scrollpage.
     * ``dpcFillContent`` string. The value to  insert in input boxes when operation is fill. Defaults to empty string value. 
     * ``dpcIsSubmit`` True | False. Specifies if a click on an element will result in submitting a form (i.e. data to the server). Used when ``dpcType`` has value click. Defaults to False.
     * ``dpcRedirects`` True | False. Specifies if the operation redirects to another page. Used when ``dpcType`` has value click. Defaults to False.



-``library``: list of json object literals representing an extraction rule to apply on the downloaded page. Libraries may have one or more extraction rules. Object literals define rules have the following fields:
   * ``ruleName`` String. A name for this rule. Rule must have names and rule names must be unique. Rule names are important as extracted values may be referenced inside the exr file via their rule name that extracted them. E.g. field ``csvLineFormat`` requires rule names to reference the extracted data by the referenced rules that should be written in the csv file. If a rule has no name, the extracted value by that rule cannot be referenced in other fields. Defaults to empty string.
   * ``ruleDescription`` String. A short description of what this rule does.
   * ``ruleURLActivationCondition`` List of regular expressions. Specifies for which URLs to apply this rule. If the page's URL matches any of the regular expressions in this list, the rule is applied. If not, the rule is not applied and skipped (o value is returned). An empty value in this field means no constraint at all. TODO: String instead of list of strings.
   * ``ruleTarget`` html | js. Value indicating where to apply the rule: html or javascript. This field is here for legacy reasons.
   * ``rulePreconditionType`` String. Accepted values: ANY | ALL |  EVAL . Specifies how the page preconditions specified in ``rulePreconditionExpression`` should be evaluated.
     * ANY : means page precondition evaluation will return True, if at least one precondition returns True. Akin to logical operator OR
     * ALL : means page precondition evaluation will return True, if all preconditions will return True. Akin to logical operator AND
     * EVAL: Truth value is the result of a logical expression referencing preconditions in ``rulePreconditions``. Any valid logical operator can be used in constructing logical expressions. E.g.   pc1 OR pc2 AND NOT pc3  
   * ``rulePreconditionExpression`` string. Must represent a logical expression referencing preconditions by their name. Keeps the logical expression that must be evaluated when ``rulePreconditionType`` has value EVAL.  

   * ``rulePreconditions`` list of json object literals representing one or more preconditions. Preconditons specify conditions the entire page must hold before applying the rule. Depending on the ``rulePreconditionType``,  if page preconditions hold (i.e. return True) rule is applied; if they do not hold (i.e. return False), rule is not applied and an empty value for the rule is returned. Currently preconditions check only the text of elements. Preconditions are json object literals with the following fields:
       * ``ecName`` String. Name of precondition. Precondition names must be unique. Precondition names are not required except when preconditionss must be referenced in EVAL expressions.
       * ``ecCSSSelector`` string. CSS selector. Specifies the element whose text that is to be checked. Currently page preconditions can only check the text of html elements.
       * ``ecTextCondition`` string. Regular expression. The regular expression the text of element specifid in ``ecCSSSelector`` must match. If matched, precondition returns True, if not precondition returns False.

   * ``ruleCSSSelector`` String. CSS selector. The actual CSS selector extracting the rule's data from the page. Must have a value as this is the central extraction specification defining the rule. If empty, nothing is extracted. Defaults to empty string. Extracted data maybe one string value or a list of string values.
   * ``ruleTargetAttribute`` String. Attribute name | text. Specifies which attribute's value of the extracted element specified by ``ruleCSSSelector`` to return as the extracted data. If value is text, the text of the elements specified by ``ruleCSSSelector`` is returned as extracted value.
   * ``ruleMatchPreconditions`` list of json object literals. Specifies the conditions the extracted data by ``ruleCSSSelector`` must meet. Elements that do not match these conditions are removed from the result. conditions have exactly the same fields are the preconditions presented in the preconditions field:
     * ``ecName`` String. Name of precondition. Precondition names must be unique. Precondition names are not required except when preconditionss must be referenced in EVAL expressions.
     * ``ecCSSSelector`` string. CSS selector. Specifies the element whose text that is to be checked. Currently page preconditions can only check the text of html elements.
     * ``ecTextCondition`` string. Regular expression. The regular expression the text of element specifid in ``ecCSSSelector`` must match. If matched, precondition returns True, if not precondition returns False.
 






####################################################################################################################################################

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
