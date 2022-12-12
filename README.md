[Go to bottom](#Related-projects)

# About WebScraper
 
WebScraper is a python program enabling rule-based scraping/extraction of data from html web pages. Rules specifying what part to extract from individual web-pages, if optional rule-specific conditions hold,  are stored exr files ((EX)traction (R)ules). Such files can be recognized in this distribution by the extension .exr . Each exr file contains one or more extraction rules, collectively called an extraction library or just library, that will be applied to a single web-page if certain rule-specific condition hold. 

**IMPORTANT: This software is currently in beta release and under heavy development. This means features may not work, may work inconsistently, are only implemented as a proof of concept and (may) have serious bugs.**


# Table of Contents

- [About WebScraper](#about-webscraper)
- [Required python modules](#required-python-modules)
- [.exr files](#exr-files)
- [Overview of .exr files](#overview-of-exr-files)
  * [Supported fields](#supported-fields)
  * [Fields in .exr files](#fields-in-exr-files)
  * [Order of checks carried out as specified by rules in exr files](#order-of-checks-carried-out-as-specified-by-rules-in-exr-files)
    + [i. ruleURLActivationCondition](#i-ruleurlactivationcondition)
    + [ii. rulePreconditions](#ii-rulepreconditions)
    + [iii. ruleCSSSelector](#iii-rulecssselector)
    + [iv. ruleMatchPreconditions](#iv-rulematchpreconditions)
    + [v. ruleContentCondition](#v-rulecontentcondition)
    + [vi. rulePostCSSSelector](#vi-rulepostcssselector)
  * [Example .exr files](#example-exr-files)
- [Running WebScraper](#running-webscraper)
  * [WebScraper configuration file](#webscraper-configuration-file)
    + [Configuration settings](#configuration-settings)
  * [WebScraper command line arguments](#webscraper-command-line-arguments)
  * [WebScraper execution modes](#webscraper-execution-modes)
    + [batch mode](#batch-mode)
    + [interactive mode](#interactive-mode)
      - [Supported application shell commands](#supported-application-shell-commands)
      - [crawl](#crawl)
        * [Description](#description)
        * [Example](#example)
      - [config](#config)
        * [Description](#description-1)
        * [Example](#example-1)
      - [history (or h)](#history--or-h-)
        * [Description](#description-2)
        * [Example](#example-2)
      - [!!](#--)
        * [Description](#description-3)
      - [!](#-)
        * [Description](#description-4)
      - [^](#-)
        * [Description](#description-5)
        * [Example](#example-3)
      - [reload](#reload)
        * [Description](#description-6)
        * [Example](#example-4)
- [Useful tools/projects](#useful-tools-projects)
- [Related projects](#related-projects)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>




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

* psutil


**NOTE: If you are using Python 3.11 and encounter errors installing module requests_html related to lxml, [follow these instructions to install lxml](https://stackoverflow.com/questions/71152710/failing-to-install-lxml-using-pip) and then reinstall requests_html using pip . You may also need to install Microsoft C++ build tools that you may download from [here](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (see [here](https://stackoverflow.com/questions/64261546/how-to-solve-error-microsoft-visual-c-14-0-or-greater-is-required-when-inst/64262038#64262038) for details).**


# .exr files


exr files are files in json format defining the extraction rules that should be applied to a web page.  Since .exr files are json formatted, they can be edited with a simple text editors. exr files are encoded in utf-8. If the file encoding changes, this may have an effect on the result returned by rules. During an Web scraping process, one exr file defining the extraction rules that will be applied to downloaded pages can be specified. Exactly one exr file must be specified when WebScraper starts executing. In the current version, WebScraper supports only the loading and application of one exr file during execution.

All the rules specified in an exr file will be applied to the same downloaded web-page if the rule-specific conditions hold, before moving on to the next page which will trigger again the application of the rules of the library. 

An overview of the extraction process is depicted below: 



		   Download one 
	      Γ->  html page
	      |	       |
	      |	       |
	      |	       |
	      |	   Apply all rules 
	      |    in the loaded exr
	      |	   file to same page
	      |    extrcting data if
	      |    conditions hold
	      |	       |
	      ^	       |
	      |	       |
	      |    Check if extracted 
	      |    data meets criteria
	      |        |
	      |        |
	      |        |
	      |	   Process the extracted 
	      |    data / save it to csv
	      |    file
	      |        |
  	      |<_______|


Each rule in a exr file is responsible for extracting only one specific kind of data  (e.g. title, links, div content, specific html elements etc) from a downloaded page, if the rule specific conditions hold. Each rule returns all the extracted data as strings. Every extraction process applied on downloaded pages needs to be considered and expressed as a rule in the exr file. Even the extraction of links, when WebScraper crawls a site, must be expressed as a specific rule in the exr file and must have the very specific name ```getLinks``` (this is because such rules are handled  differently by WebScraper). Currently, extraction is supported only from html resources.  

Each rule returns the extracted/scraped data always as a string. Rules may return only one string value as the result of the extraction, return a list of string values or a list of objects. If a rule is not applied, an empty string is returned.

Each rule in an exr file may specify a set of optional preconditions the page must meet in order to apply the rule. These preconditions may refer to the downloaded page's URL and its content. If these rule preconditions hold the rule is applied and the specified element extracted; if preconditions do not hold, the rule is not applied and an empty value is returned as the rule's extraction value. If no preconditions have been specified, the rule is applied on the page. 

In general, exr files, when applied to content (web-page) downloaded from the WWW, attempt to extract the data according to the following scenario:

*"Once a Web page has been downloaded do the following for each rule inside the current exr file:  If the web-page do not match the rule's preconditions do not apply the rule and return an empty value. Otherwise, extract the data from the web-page specified by a CSS selector. After extraction, check if the extracted data meets other conditions. If so, return it as the extracted/scraped data. If not, return empty extracted/scraped data."*   

A rule may also specify conditions (post conditions) that are applied on data after these have been extracted from a page; if post-conditions are specified in a rule, only the extracted data meeting these post-conditions will be returned.


Authoring rules in exr files requires basic knowledge of [css selectors](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) and [regular expressions](https://www.regular-expressions.info/).

Besides rules, exr files can also specify/dioctate other aspects of the extraction process such as how to render/fetch the page, what HTTP headers and/or cookies to use, if and how to interact with the downloaded page (e.g. scrolling, filling boxes, clicking etc) before applying the rules etc.


# Overview of .exr files

## Supported fields
 
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

-``csvLineFormat``: List of rule names (string - see below). Specifies the rule names the extracted data of which should be stored in the .csv files. E.g. if ``csvLineFormat`` has value ["pageTitle"] this means that in the csv file only the extracted value after applying rule with name pageTitle should be stored int he csv file. WebScraper tags extracted data with the rule name that extracted the data with which the extracted data can be referenced. If an empty list is specified, nothing is written in the csv file.

-``requiredFilledFields``: List of strings. List of rule names that must extract non-empty data from a page in order to consider the extraction process successful and the data be written in the csv file.  If at least one rule (indentified by rule name) in this list returns an empty value, the extraction process is unsuccessfully and nothing is written in the csv file. Default value [] (empty list).

-``allowedMinimumFilled``: floating point numner. Minimum percentage of extracted rule names that must extract a non-empty value. If a smaller percentage than ``allowedMinimumFilled`` of rules have non-empty values, the extraction is considered unsuccessful and nothing is extracted or written to the csv file. E.g. ff this value is 0.8 this means that the extraction process is successful if 80% of rules applied to the same page extracted non-empty values. If smaller than 80% of rules extracted non-empty values, the extraction process is unsunccessful and nothing is written in the csv file. A negative value disables this setting. Default value -1.    


-``renderPages``: True | False. Specifies how the WWW page should be downloaded: using simple HTTP method or using a browser engine (Chromium or Chrome). If set to True, Chromium (the default build-in browser of [pyppeteer](https://github.com/pyppeteer/pyppeteer) ) or an external Chrome installation will be used. Defaults to False. 
**NOTE: when renderPages is set to True, fetching and processing of pages is slower.**


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
   * ``ruleMatchPreconditions`` list of json object literals. Specifies the conditions the extracted data by ``ruleCSSSelector`` must meet. Conditions defined in ``ruleMatchPreconditions`` will be applied after the css selector in ``ruleCSSSelector`` has been applied to the page. Elements that do not match these conditions are removed from the result. conditions have exactly the same fields are the preconditions presented in the preconditions field:
     * ``ecName`` String. Name of precondition. Precondition names must be unique. Precondition names are not required except when preconditionss must be referenced in EVAL expressions.
     * ``ecCSSSelector`` string. CSS selector. Specifies the element whose text that is to be checked. Currently page preconditions can only check the text of html elements.
     * ``ecTextCondition`` string. Regular expression. The regular expression the text of element specifid in ``ecCSSSelector`` must match. If matched, precondition returns True, if not precondition returns False.
 
   * ``rulePostCSSSelector`` list of strings. Each string in this list must be a css selector. Specifies css selectors that all of them will be applied to each of the extracted elements by ``ruleCSSSelector`` (and after apllying ``ruleMatchPreconditions``) seperately. Extracts from each specific element the specified sub-elements. Currently, rulePostCSSSelectors support the extraction only of text from designated elements. Defaults to empty list. 
   **NOTE: For ``rulePostCSSSelector`` to work properly, field ``ruleTargetAttribute`` must have value 'text'.**
   
   * ``ruleReturnedValueNames`` list of strings. Each string is user defined and should not contain the characters: empty char, whitespace, -, !, , (comma), \*, /, \,?. Specifies each name of the extracted sub-element by ``rulePostCSSSelector`` . ``ruleReturnedValueNames`` is exclusively used with ``rulePostCSSSelector`` . Returns a list of objects, having as key-names the strings defined in ``ruleReturnedValueNames`` and as key-values the extracted data specified by css selector ``rulePostCSSSelector`` in the same position. 
  
     E.g. if ``rulePostCSSSelector`` has the value ["th", "td:nth-child(2)", "td:nth-child(3)", "td:nth-child(4)"] and  ``ruleReturnedValueNames`` the value ["name", "winnerCount", "runnerUpCount", "seasonsWon"] then, for each result separately, the extraction process will result in returning an object having a key with name "name" and value the text of element "th", a key with name "winnerCount" and value the text of element "td:nth-child(2)" and so on. Thus, for each element an object having the keys {name:xxx, winnerCoun:yyy, runnerUpCount:zzz, seasonsWon:kkk} will occur and returned as the extraction result. This will result in a list of such objects, which is called a record list. The key names (name, winnerCount etc as defined previously) can be used in field ``csvLineFormat`` as the values being stored in the csv file.

   * ``ruleContentCondition`` string. Regular expression. Specifies the pattern the text of extracted elements must match in order to be part of the returned result set. Text of extracted elements that do match this regular expression, are kept in the result; text of elements that do not match this regular expression, are removed from the result. Regular expression ``ruleContentCondition`` is applied immediately after ``ruleMatchPreconditions`` and before ``rulePostCSSSelector`` (see section XXX on the order of application of conditions). Defaults to empty string which means no constraint on text.
   * ``ruleReturnsMore`` True|False. Specifies if this rule will return more than one value (string or object) from the extraction process
   * ``ruleReturnedMatchPos`` Integer > 0. Specifies which match position to return as the extracted data. If rule returns more than one value as result of the extraction process, this field specifies which one the elements to return in case only ONE extracted value must be returned by the rule. Defaults to 0 (first element). Negative value means no specification of element and this filed is not applied i.e. ignored. NOTE: Has not been tested thoroughly.
   * ``ruleReturningMoreIsError`` True|False. Specifies if an error/exception should be raised if the rule returns MORE than one result. This has not been implemented or tested.
   *  ``ruleRemoveChars`` list of strings. Specified the characters to be removed from the text values returned by the extraction process. Empty list means no replacement of any character. Defaults to empty list. E.g. values  ['€', '$'] means removing these characters from extracted texts of elements. exr files should be stored in utf-8 encoding in order make such fields work properly.


## Order of checks carried out as specified by rules in exr files

When applying rules to html file, checks and extraction is carried out in the following order for each rule in the exr file:

### i. ruleURLActivationCondition 

First url of downloaded page is checked if it matches any of the regular expression specified in ruleURLActivationCondition.
if URL of downloaded resource does not match any regular expression in ruleURLActivationCondition, rule is not applied. Otherwise rule continues.

### ii. rulePreconditions

Then page rule preconditions are applied. The expression in page preconditions, which check if the html content meets the css element conditions specified in rulePreconditions, is evaluated. If evaluation of page preconditions return False, the extraction specified by the rule stops.  Otherwise, it continues. NOTE: page preconditions may overwrite the ruleCSSSelector.

### iii. ruleCSSSelector

ruleCSSSelector extracts the actual target (sourght after) information from the downloaded page. Specified ruleCSSSelector may be overwritten by rulePrecondition. May return a single value or a set/list of values (specified by ruleReturnsMore).

### iv. ruleMatchPreconditions

If specified, on the result set returned by ruleCSSSelector, the ruleMatchPreconditions are applied. These check if each result match a very specific condition. Results that do not meet the conditions specified by ruleMatchPreconditions are removed from the ruleCSSSelector result set and not returned. Although more than one match precondition can be specified, only the ANY operator (s supported (i.e. ruleMatchPreconditionType can only take value ANY). Match preconditions are applied to the results after the extraction process in contrast to page preconditions that are applied before.

### v. ruleContentCondition

If specifies, the regular expression specified in ruleContentCondition is applied to all extracted content in the result set. If ruleContentCondition is  empty, no conditions are enforced on the extracted content i.e. the rcurrent esult set is unafected.


### vi. rulePostCSSSelector

If specified, it applies the css selector list specified in rulePostCSSSelector to cut each and every element of the results set returned by ruleCSSSelector into smaller pieces. May return a list of strings or a list of dictionaries. List of dictionaries are returned, if field ruleReturnedValueNames is specified which has a list of strings acting as keys corresponding to the css selectors one-by-one in rulePostCSSSelector.   


After these steps, the result set is returned as the value of the extracted information after applying one single rule. As already mentioned, the idea of exr files is that each rule extracts one specific information of the downloaded Web page.



## Example .exr files

You may find working examples of pre-authored exr file in the rules/ directory that will help in understanding how the the above fields should be used. The [file index.html in the same directory will help you in browsing and understanding the exr files in the rules direcory. We encourage you to use this file to check the available exr files.](https://htmlpreview.github.io/?https://github.com/deusExMac/WebScraper/blob/main/rules/index.html).

TODO: use RAWGIT linek this instead of htmlpreview: https://rawgit.com/necolas/css3-social-signin-buttons/master/index.html OR the gh-branch approach described here: https://stackoverflow.com/questions/8446218/how-to-see-an-html-page-on-github-as-a-normal-rendered-html-page-to-see-preview



# Running WebScraper 

WebScraper's main module is WebScraper.py which must be loaded and executed in your development environment. WebScraper has been developed and tested on IDLE.


## WebScraper configuration file

When starting execution, WebScraper looks for and loads a default configuration file named [webscraper.conf](https://github.com/deusExMac/WebScraper/blob/main/webscraper.conf) in the local directory. A different configuration file can be specified on the command line using the -r switch . If no configuration file is loaded, WebScraper continues with default settings.


### Configuration settings

WebScraper's configuration file defines and initializes the values on some important aspects that are required during its execution. The configuration file initializes these settings during startup; these settings can be altered when WebScraper executes using command line arguments or WebScraper shell arguments. WebScraper's configuration file is separated in sections, each section controlling a specific aspect of the program. Below is a list of each section and a list of supported settings:

* Shell 

  This section has settings related to the shell that appears only when WebScraper is executed in interactive mode.

  - ``commandPrompt ``: string. The string that will appear as the command prompt when WebScraper is executed in interactive mode.
  - ``historySize  ``: integer. Specifies the number of commands to keep in shell history when WebScraper operates in interacive mode. Shell supports history of commands to make it easier to type and execute application shell commands.

* Rules 

  This section has settings related to the default exr file loaded during execution. Current version requires loading of at least one exr file.
  
  - ``ruleFile  ``: path to exr file. Default exr file to load if no exr file is specified on the command line.

* Crawler 

  This section has settings related to the fetching of web resources.
  
  - ``guardRunningChromeInstances``: True | False. Specifies if existing Chrome instances (started by the user in head mode) should be protected from being forcibly killed in case Chromium (pyppeteer's default browser) or an external Chrome installation is used to fetch pages. Takles effect only if renderPages is set to True and no external browser is used (TODO: check this???).
  
   - ``forceBrowserCleanup``: True | False | Auto. Specifies if Chromium and external Chrome instances should be killed forcibly by WebScraper when renderPages is True. Due to a bug in pyppeteer (see also [Issue 27](https://github.com/deusExMac/WebScraper/issues/27) ), Chromium and external Chrome instances spawned by WebScraper may remaining after properly closing browsers in headless mode (aka zombie processes). In order to avoid memory leaks, WebScraper may forcibly kill these instances. Depending on the value of ``forceBrowserCleanup``, this setting will kill these zombie processes in the following ways:
     - True : killing of zombies will be carried out only once, when WebScraper terminates execution.
     - Auto : killing of zombies will be carried out after each use of Chromium/Chrome to fetch pages.
     - False: no killing of zombies will be carried out.     

     In order to avoid killing Chrome browsers that the user is using while WebScraper executes, you may set ``guardRunningChromeInstances`` to True. Otherwise, all Chrome instances will be killed, including those instances started execution by the user.
     
   - ``windowsChrome``: Regular expression. The pattern identifying the name Chrome processes on Windows machines that should be forcibly killed. Used only when ``forceBrowserCleanup`` is set to True or Auto.
   - ``macosChrome``: Regular expression. The pattern identifying the name of Chrome processes on MacOS machines that should be forcibly killed. Used only when ``forceBrowserCleanup`` is set to True or Auto.
   - ``linuxChrome``: Regular expression. The pattern identifying the name of Chrome processes on Linux machines that should be forcibly killed. Used only when ``forceBrowserCleanup`` is set to True or Auto.
   - ``androidChrome``: Regular expression. The pattern identifying the name of Chrome processes on Android machines that should be forcibly killed. Used only when ``forceBrowserCleanup`` is set to True or Auto. 
       
   - ``traversalStrategy``: bfs | dfs. What traversal strategy to use to crawl a site. bfs will do a [breadth first search](https://en.wikipedia.org/wiki/Breadth-first_search) while dfs will perform a [depth first search](https://en.wikipedia.org/wiki/Depth-first_search). Defaults to bfs.
 
   - ``maxPages``: integer. Maximum number pages to fetch/process/extract from when crawling an entire site. Negative values means no limit.
   - ``allowedSchemes``: http, https. Allwed URL schemes (TODO: should be a regular expression).
   - ``ignoreResponseCookies``: True | False. Specifies if response cookies should be ignored or not. If set to False, any response cookies received will be stored and used in any subsequent request to the same server. If set to True, any response cookie will be ignored.
   - ``ignoredCookies ``: string. Comma separated cookie names. Names of individual response cookies to ignore i.e. not to be stored and used in any subsequent request to the same server. (TODO: should be a regular expression). Takes effect only if ``ignoreResponseCookies`` is set to False. Deafults to empty string i.e. do not ingnore any response cookie.
  - ``allowedContentTypes``: string. Regular expression. Specifies the content type the page must match in order to be processed. Pages whose content type do not match regular expression ``allowedContentTypes`` are ignored. The Content-line response header line is checked against this regular expression pattern.
  - ``takePageScreenShot``: True | False. If a screenshot of the downloaded page should be taken. Works only when renderPages is set to True i.e. pyppeteer  (Chromium or Chrome) is used for downloading the page. If this setting is set to True, screenshots will be stored in directory specified by setting ``screenShotPath`` in the Storage section. Used usually for debugging purposes.
  - ``asyncWaitTime``: Float. Time to wait after an interaction/operation has been applied on the loaded page. Takes effect only if renderPages is True.
  - ``minHitRate``: Float in range [0,1]. Specifies the minimum percentage of pages (defined as number of pages successflly extracted data  / total number of pages downloaded and processed) from which valid data have been extracted using the rules up until now. If this percentage falls below this limit, WebScraper stops. If  ``minHitRate`` is negative, no rate limit is enforced i.e. this setting is disabled.
  - ``minHitRateSamples`` integer. Number of consecutive hit rate samples that have to be below ``minHitRate`` in order to terminate the extraction process. I.e. if ``minHitRate`` has value 0.01 and ``minHitRateSamples`` has value 50 this means that if for 50 consecutive pages the hit rate is below 0.01 (i.e. 1%), terminate the extraction process and WebScraper. Takes only effect when ``minHitRate`` is > 0.
  - ``maxQueueSize`` integer.  Allowed maximum number of URLs in URL queue (keeping the to-be-visited URLs). If this threshold is reached, new URLs will not be added to the queue. Fetching/processing will continue but URL queue will never exceed this number. Negative value means no maximum number.
  - ``maxQueueMemorySize`` integer expressing memory capacity. Allowed maximum size of URL queue in memory. If this size is reached, no new urls are added to the queue. Values may specify K, M, G at the end for units e.g. 8M for 8 Megabyte. If no unit is specified, number is interpreted as bytes. Negative value means no limit.
  - ``delayModel``: c | h. What model to use for wait times between two consecutive requests on the same server. c (constant): constant wait time meaning a constant specific time is waited, h (human): a variable waiting time is used simulating human browsing i.e. a random amount of time is waited. 
  - ``sleepTime``: float. Actual time in seconds to wait/sleep between two consecutive requests on the same server, if ``delayModel`` has value c .
  - ``humanSleepTimeAvg`` and ``humanSleepTimeSigma`` : floats. Specify the waiting/sleeping times if ``delayModel`` is set to h. These settings specify a random waiting time that is drawn from a normal distribution having average ``humanSleepTimeAvg`` and standard deviation  ``humanSleepTimeSigma`` . 
  - ``autoSave``: True | False. If URL queue and extracted data (csv file) should be periodically saved to file.
  - ``autoSaveInterval``: float. Numeric value specifying period of autosaves in seconds i.e. the interval that must elapse before autosaving. ``autoSaveInterval`` takes effect only when ``autoSave`` is set to True.
  - ``maxTPPSamples``: integer. Number of samples to use for calculating average speed in pages/seconds.
 
  
* Storage 

  This section has settings related to places to downloaded files and screenshots.
  
  - ``mirrorRoot``: string. Path to local directory. Directory root to store and mirror downloaded pages if the -M option is set. 
  - ``screenShotPath``: string. Path to local directory. Directory to store screenshots of webpages. Take effect only if renderPages is set to True. Screenshots are saved in files with names calculated out of their URL.
  
   
   
 * DEBUG 

   This section controls debugging issues. 
  
   - ``debugging``: True | False. If set, debug messages will be displayed.
 
     
IMPORTANT: Some properties are not fully supported and/or may result in errors and exceptions. 

## WebScraper command line arguments

WebScraper's command line arguments allow the overwriting of settings defined in configuration file. Usage:

``webScraper.py [-c configuration file] [-r exr file] [-B] [-M] [-n number] [-s amount] [-o output] [-q queue] [-C] [-D] [-HR pct] [-CT regular expression[ [-R] [-ST] [-U] [-p pos] [-G] start_url``


Command line options supported:

-c configuration file : will result in loading  <configuration file> as configuration file

-r exr file: will load <exr file> as the default exr file

-B: will execute WebScraper in batch mode i.e. no shell will be displayed and crawling/extraction will start immediately from start url..

-M: will enable mirroring i.e storing all downloaded pages locally mirroring the remote website. Fetched pages will be stored using as local root directory the directory specified in ``mirrorRoot`` (see Crawler section above).

-n number: will fetch/process a maximum of <number> pages before stopping. If number if negative, no number of pages limit is enforced i.e. infinite pages.

-s amount: amount of time to sleep between consecutive requests to the same server. Has effect only if  ``delayModel`` is set to c .

-o output csv file: will store all extracted data from pages in the csv file <output csv file>.

-q queue file: will use file <queue file> as the file to store the URL queue when WebScraper terminates or saves periodically the queue. If no -q option if present, default URL queue file is .queue . Whenevr WebScraper starts, the queue file is reinitialized except when the -C option is specified.

-C: will not create a new URL queue file but uses the existing one and continues processing of urls in queue file, fetching and processing pending urls.
	
-D: will apply a depth first strategy for site traversal
	
-HR pct: uses pct as the minimum hit rate percentage. If pct is negative, minimum hit rate is disabled.

-CT regular expression: during fetching and processing of pages content type of downloaded pages mus match regular expression. Allows changing accepted content type of pages. 
	
-R: fetches pages using pyppeteer;s browser (Chromium or Chrome depending on other settings).

-ST: Turns taking screenshots on. This is supported only when renderPages is set to True and a rendering engine is used to download the page.

-ML: Mute library. Don't display librar description when starting extraction.

-U: Entering update mode i.e. using existing url queue file and checking if pages have been modigied. Will re-extract data from pages that have been visited and from where data has been extracted. TODO: Not thoroughly tested.
	
-p pos: starting fetching urls starting from position pos of URL queue file.
	
-G: enables debug mode. Prints debug messages on screen.
	
start_url: url to start downloading and apply exreaction rules. Depending on set of rules and number of pages desired to download will crawl entire site extracting the specified data.	

	
## WebScraper execution modes

WebScraper can be executed in batch or interactive mode.

### batch mode

In batch mode, WebScraper starts execution, fetches and processes web resources based on the arguments and terminates its execution when no other resource is available. Specifying option -B on the command line, will execute WebScraper in batch mode.	

### interactive mode	

If option -B is not specified on the command line, WebScraper executes in interactive mode (the default). In interactive mode, WebScrpaer displays an application shell that allows users to execute a set of supported shell commands. Ιn interactive mode, WebScraper's application shell will appear:

```
[v0.3.6a 20/10/2022]
Execution started on Darwin release 21.6.0 (posix)

Loading configuration settings from [ ./webscraper.conf ]....ok.
Loading extraction rule library [./default.exr]...done
	Total of  1  extraction rules loaded.

Starting INTERACTIVE mode

Instatiating MacOS platform object
(v0.3.6a){0}WebScraper >>

```
At the displayed prompt, a set of shell commands can be executed along with a set of shell command arguments. Below a list of supported shell commands. 
	
#### Supported application shell commands
	
- #### crawl 	
	
  Syntax: ``crawl  [-r exr file]  [-M] [-n number] [-s amount] [-o output] [-q queue] [-C] [-D] [-HR pct] [-CT regular expression] [-R] [-U] [-p pos] [-G] start_url``
     
  ##### Description
	
  crawl starts the downloading of webpages and the extraction process based on the arguments given. The arguments of crawl are the same as WebScraper's command line arguments there were presented [above TODO: add link here](#) . 

  ##### Example	

  ```
          [v0.3.6a 20/10/2022]
          Execution started on Darwin release 21.6.0 (posix)

          Loading configuration settings from [ ./webscraper.conf ]....ok.
          Loading extraction rule library [./default.exr]...done
	       Total of  1  extraction rules loaded.

          Starting INTERACTIVE mode

          (v0.3.6a){0}WebScraper >> crawl -M -n -1 -r rules/example4.2-en.wikipedia.exr -o csv/example4.2.csv https://en.wikipedia.org/wiki/List_of_physicists
	  
	  1) >>> Doing [https://en.wikipedia.org/wiki/List_of_physicists] Queue:1 (mem: 476B/0.00M/-1) Pending:1 Fetched:0 Extracted:0  [Avg pps:--- (0.000KB/sec) Hit rate:0.0000 (min:-1.0000)]
           ...   
  ```


- #### applyRules
  
  Syntax: ``applyRules [-r exr file] [-R rule name] url``
  
  -r exr file: exr file to apply on web page
  
  -R rule name: applying only the specific rule, as defined in exr file specified by -r option, to downloaded web page. If no -R option is provided, all rules in tht exr file will be applied.
  
  url : Webpage onto which rule(s) will be applied. Rule will be applied only to this one webpage. No other Webpage is downloaded. No crawling is initiated.
  
  ##### Description
	
  Applies all the rules in specifid exr file, or one specific rule specified by rule name, to one web page.  Used for testing/debugging purposes in order to see the result when the exr file is applied to the webpage. Application of rules in exr files will enforce all checks and constraints.    	
	
  ##### Example	

  ```
          [v0.3.6a 20/10/2022]
          Execution started on Darwin release 21.6.0 (posix)
  ```	  
  
  **TODO: Complete me**	
	
	
	
	
- #### cssSelector
  
  Syntax: ``cssSelector [-T] url``
  
  -T : Display text content of matching element of css selector. 
	
  ##### Description
	
  Downloads a webpage and displays a primitive interface to apply css selectors to loaded document. Used for testing/debugging purposes in order to see the result of specific selectors.  
  
    **TODO: Complete me**	

	
	

- #### config 	
	
  Syntax: ``config``	
	
  ##### Description
	
  Displays the loaded configuration settings.

  ##### Example	

  ```
          [v0.3.6a 20/10/2022]
          Execution started on Darwin release 21.6.0 (posix)

          Loading configuration settings from [ ./webscraper.conf ]....ok.
          Loading extraction rule library [./default.exr]...done
	       Total of  1  extraction rules loaded.

          Starting INTERACTIVE mode

          (v0.3.6a){0}WebScraper >> config
	  Section [Default]
	   - outputdir = ./articles
	   - maxarticles = 12
	   - contentdownload = true
	   - csvsave = true
	   - csvfilename = allArticles.csv
	   - csvseparator = ;
          
	  Section [Shell]
	   - commandprompt = WebScraper >>
	   - historysize = 700
          
	  Section [Rules]
	   - rulefile = ./default.exr
          
	  Section [Crawler]
	   - guardrunningchromeinstances = True
	   - forcebrowsercleanup = True
	   - windowschrome = ^chrome.exe$
	   - macoschrome = ^(?i)^(Google Chrome)
	   - linuxchrome = 
	   - androidchrome = 
	   - traversalstrategy = dfs
	   - httpuseragent = 
	   - maxpages = 10
	   - allowedschemes = http,https
	   - ignoreresponsecookies = False
	   - ignoredcookies = 
	   - allowedcontenttypes = (?i)(text/html?|application/.*)
	   - takepagescreenshot = False
	   - asyncwaittime = 1.2
	   - minhitrate = -1
	   - minhitratesamples = 121
	   - maxqueuesize = -1
	   - maxqueuememorysize = -1
	   - delaymodel = h
	   - sleeptime = 3.4
	   - humansleeptimeavg = 12.4
	   - humansleeptimesigma = 4.136
	   - autosave = True
	   - autosaveinterval = 131
	   - maxtppsamples = 150
         
	  Section [Storage]
	   - mirrorroot = etc
	   - screenshotpath = etc/sshots
          
	  Section [DEBUG]
	   - debugging = False
          
	  Section [__Runtime]
	   - __configsource = ./webscraper.conf

  ```	

- #### history (or h) 	
	
  Syntax: ``h [-s] [argument]``	
  
  -s argument : integer. Displays the [argument] number of first commands in history entered by the user.
 
	
  argument: If argument is an integer displays the [argument] number of last commands in history entered by the user. if argument is a string, the string value is interpreted as a regular expression and displays only those commands in the history that matches the regular expression pattern. If no argument is given, entire history is displayed. Size of history is configurable (see ``historySize`` in configuration file). History of commands is preserved between executions of WebScraper and is stored in a local file with the default name .history .
	
  ##### Description
	
  Displays the entire or a subset of the history of shell commands as entered/executed by the user using WebScraper's shell.
	
  ##### Example	

  ```
          [v0.3.6a 20/10/2022]
          Execution started on Darwin release 21.6.0 (posix)

          Loading configuration settings from [ ./webscraper.conf ]....ok.
          Loading extraction rule library [./default.exr]...done
	       Total of  1  extraction rules loaded.

          Starting INTERACTIVE mode

          (v0.3.6a){0}WebScraper >> h 4
	
	
	          697.  crawl -M -n -1 -r rules/upatras.gr.exr -o csv/up.csv -HR 0.8 -s 0.6 http://www.upatras.gr/
	          698.  config
	          699.  crawl -M -n -1 -r rules/example4.2-en.wikipedia.exr -o csv/example4.2.csv https://en.wikipedia.org/wiki/List_of_physicists
	          700.  config
	
  ```	

  h with string argument
	
  ```
           [v0.3.6a 20/10/2022]
           Execution started on Darwin release 21.6.0 (posix)

           Loading configuration settings from [ ./webscraper.conf ]....ok.
           Loading extraction rule library [./default.exr]...done
	   Total of  1  extraction rules loaded.

           Starting INTERACTIVE mode

           Instatiating MacOS platform object
           (v0.3.6a){0}WebScraper >>h airbnb
            h airbnb
	          77.   crawl -M -n 1 -r rules/airbnb-Title.exr -o csv/AIRNBN-comments.csv -G https://www.airbnb.com/rooms/48856899
	         174.   crawl -M -n 1 -r rules/airbnb-Title.exr -o csv/AIRNBN-comments.csv -G https://www.airbnb.com/rooms/48856899
	         463.   crawl -M -n 1 -r rules/airbnb-Title.exr -o csv/airbnb.csv -G https://www.airbnb.com/rooms/676044415326884478?source_impression_id=p3_1667250461_pn4Vd1GkeoLOymMX
	         464.   crawl -M -n 1 -r rules/airbnb-Title.exr -o csv/airbnb.csv -G https://www.airbnb.com/rooms/676044415326884478?source_impression_id=p3_1667250461_pn4Vd1GkeoLOymMX
	         557.   crawl -M -n 1 -r rules/airbnb-Title.exr -o csv/airbnb.csv -G https://www.airbnb.com/rooms/34749360

  ```

 h -s number 
	
  ```
           [v0.3.6a 20/10/2022]
           Execution started on Darwin release 21.6.0 (posix)

           Loading configuration settings from [ ./webscraper.conf ]....ok.
           Loading extraction rule library [./default.exr]...done
	   Total of  1  extraction rules loaded.

           Starting INTERACTIVE mode

           Instatiating MacOS platform object
           (v0.3.6a){0}WebScraper >>h -s 10
            h -s 10
	          1.   crawl -M -n 1000 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv  https://en.wikipedia.org/wiki/Statistics
	          2.   crawl -M -n 1000 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv  https://en.wikipedia.org/wiki/Statistics
	          3.   crawl -M -n -1 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv  https://en.wikipedia.org/wiki/Statistics
	          4.   crawl -M -n -1 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv  -C https://en.wikipedia.org/wiki/Statistics
	          5.   crawl -M -n -1 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv  -C https://en.wikipedia.org/wiki/Statistics
	          6.   crawl -M -n -1 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv  -C https://en.wikipedia.org/wiki/Statistics
	          7.   crawl -M -n -1 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv  -C https://en.wikipedia.org/wiki/Statistics
	          8.   crawl -M -n -1 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv   https://en.wikipedia.org/wiki/Statistics
	          9.   crawl -M -n -1 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv -G https://en.wikipedia.org/wiki/Statistics
	         10.   crawl -M -n -1 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv -G https://en.wikipedia.org/wiki/Statistics

  ```	
	
- #### !!  	
	
  Syntax: ``!!``	
  
  ##### Description
	
  (Re-)Executes the last command as entered via WebScraper's shell

	

- #### !  	
	
  Syntax: ``!<number>``	
  
  ##### Description
	
  (Re-)Executes command at position <number> in the history list.


- #### ^	
	
  Syntax: ``^<string>^<replacement>``	
  
  ##### Description
	
  Replaces all occurences of < string > in last command with < replacement > and executes modified command.

	
  ##### Example	

  ```	
           [v0.3.6a 20/10/2022]
           Execution started on Darwin release 21.6.0 (posix)

           Loading configuration settings from [ ./webscraper.conf ]....ok.
           Loading extraction rule library [./default.exr]...done
	           Total of  1  extraction rules loaded.

           Starting INTERACTIVE mode

           Instatiating MacOS platform object
           (v0.3.6a){0}WebScraper >>h 1
           h 1
	           629.   crawl -M -n -1 -r rules/example1.1-stanford.edu.exr  -CT (?i)text/html https://www.stanford.edu/
           
	   (v0.3.6a){0}WebScraper >>^-1^16
              crawl -M -n 16 -r rules/example1.1-stanford.edu.exr  -CT (?i)text/html https://www.stanford.edu/
              Instatiating MacOS platform object

              1) >>> Doing [https://www.stanford.edu/] Queue:1 (mem: 355B/0.00M/-1) Pending:1 Fetched:0 Extracted:0  [Avg pps:--- (0.000KB/sec) Hit rate:0.0000 (min:-1.0000)]
	      ...
	
  ```	

	
- #### reload  	
	
  Syntax: ``reload [-c configuration_file]``

  -c configuration_file: path to configuration file. If -c option is specified, the specified configuration file is loaded. If no -c option is specified, the same configuration file that was loaded when WebScraper started execution is reloaded again (default webscraper.conf). 	 
  
  ##### Description
	
  Reloads the already loaded or loads a new configuration file. After successfully loading a configuration file, any new extraction process will use the newly loaded settings.

##### Example	

  ```	
           [v0.3.6a 20/10/2022]
           Execution started on Darwin release 21.6.0 (posix)

           Loading configuration settings from [ ./webscraper.conf ]....ok.
           Loading extraction rule library [./default.exr]...done
	           Total of  1  extraction rules loaded.

           Starting INTERACTIVE mode

           Instatiating MacOS platform object
           
	   (v0.3.6a){0}WebScraper >> reload
                   reload
                   Loading configuration file: [./webscraper.conf]
                   Configuration file [./webscraper.conf] successfully loaded.
	   (v0.3.6a){1}WebScraper >>
	      
	
  ```		
	
	
	
# Useful tools/projects

To make life easier, you may use the following browser extensions that may help you in specifying the  relevant css selectors that are required when authoring an .exr file:

* Chrome extension SelectorGadget to effortlessly determine CSS seslectors for html elements that can be used in .exr files. See: https://chrome.google.com/webstore/detail/selectorgadget/mhjhnkcfbdhnjickkkdbjoemdmbfginb?hl=en  and   https://selectorgadget.com/   

* Firefox extension ScrapeMate. See https://addons.mozilla.org/en-US/firefox/addon/scrapemate/



# Related projects

* [Scrapy](https://github.com/scrapy/scrapy)

* [Scrapy-cluster](https://github.com/istresearch/scrapy-cluster)

* [Djano dynamic scraper](https://github.com/holgerd77/django-dynamic-scraper)

* [Power BU](https://www.phdata.io/blog/web-scraping-in-power-bi/)

* [Portia](https://github.com/scrapinghub/portia)

* [Crawlee](https://github.com/apify/crawlee)
	
* [web.scraper.workers.dev](https://github.com/adamschwartz/web.scraper.workers.dev)
	
* [Crawly](https://crawly.diffbot.com/)

* [Scrape-it](https://github.com/IonicaBizau/scrape-it)

	
You can find exhaustive lists of scrapers [here](https://github.com/cassidoo/scrapers) and a list crawlers [here](https://github.com/BruceDone/awesome-crawler)
	


[Go to top](#About-WebScraper)
