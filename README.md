# About WebScraper
 
WebScraper is a simple python program enabling rule-based scraping/extraction of data from web pages. Specifications on which data to extract from individual web-pages pages comes in the form or rules stored in .exr files ((EX)traction (R)ules). Each .exr file contains one or more extraction rules, collectively called an extraction library or just library, that will be applied to a single web-page if certain condition hold. .exr files are in json format. More information on how to author .exr files can be found below.

**IMPORTANT: This software is currently in alpha release and under heavy development. This means features may not work, may work inconsistently, are only implemented as a proof of concept and (may) have serious bugs.**


# Required python modules

Make sure you have the following python packages installed before running the application:

* dataconf (https://pypi.org/project/dataconf/)

* requests_html (https://requests.readthedocs.io/projects/requests-html/en/latest/)

* clrprint (https://pypi.org/project/clrprint/)


# Specifying extraction rules using .exr files

.exr files are files in json format defining the rules specifying what data to extract, what consditions the extracted data must meet, from which pages to extract the data and how to return them. Such specfications are referred to as 'extraction rules' and the the extraction rules inside the same .exr file is called a library. .exr files contain one or more rules. All rules inside the .exr files are applied to each individual page.

During WebScraper's startup the preferred .exr file can be specified via the -r option on the command line. If no .exr file is specified, the default extraction rules file default.exr is loaded. If no .exr file is loaded, WebScraper does not start. 

.exr files can also been set as arguments during individual commands in the application's shell. The used .exr file and all the rules it contains are applied to each individual page that the application downloads. Currently only one .exr can be specified and used during the extraction process.

Authoring .exr files requires basic knowledge of [css selectors] (https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) and [regular expressions](https://www.regular-expressions.info/).

## Example .exr file

.exr files, when applied to content (web-page) downloaded from the WWW, attempt to express the following conditions and actions:

*"For each rule inside the .exr file, do the following: If the web-page URL matches the conditions, check if the web-page's content matches zero or more preconditions. If all these conditions hold, extract the data from the web-page specified by a CSS selector. Check if the extracted data meets a contition. If so, return it as the scraped value. If not, return empty extracted data."*   


TODO: library extraction files have been  updated with new properties. Make changes here!
Below is an example of a .exr file that is used to extract data related to football teams from wikipedia pages. It contains 4 rules that will be applied to all wikipedia pages downloaded.

```
#
# json format of 
# 
# version 0.01@18/05/2022
#
#


{
"libraryDescription": "Library to extract data from english wikipedia pages",
"csvLineFormat": ["teamFullName", "clubPresident"],

"library": [

{
 "ruleName": "teamFullName"
 "ruleDescription": "Get full name of clubs from infoboxes"
 "ruleURLActivationCondition": ["en\.wikipedia\.org"]
 
 "rulePreconditionType": "Any"
 "rulePreconditions" : [ 
                            {
                              "ecCSSSelector" : "tr:nth-child(2) .infobox-label" 
                              "ecTextCondition" : "Full name"
                              "ecRuleCSSSelector" : ""
                            }                       
                       ]
 "ruleCSSSelector": "tr:nth-child(2) .infobox-data"
 "ruleTargetAttribute": "text"
 "ruleContentCondition": ""
 "ruleReturnsMore": False
 "ruleReturnedMatchPos": 0
 "ruleReturningMoreIsError": False
 "ruleRemoveChars": []
},

{
 "ruleName": "articleTitle"
 "ruleDescription": "2nd rule"
 "ruleURLActivationCondition": ["en\.wikipedia\.org/wiki"]
 "rulePreconditionType": "Any"
 "rulePreconditions" :  [ 
                             {
                               "ecCSSSelector" : "tr:nth-child(2) .infobox-label" 
                               "ecTextCondition" : "Full name"
                             },
                             {
			        "ecCSSSelector" : "tr:nth-child(3) .infobox-label" 
			        "ecTextCondition" : "Full name"
                             }
                          ]
                       
 "ruleCSSSelector": "#content h1.firstHeading"
 "ruleTargetAttribute": "text"
 "ruleContentCondition": ""
 "ruleReturnsMore": False
 "ruleReturnedMatchPos": 0
 "ruleReturningMoreIsError": False
 "ruleRemoveChars": []
},


{
 "ruleName": "clubPresident"
 "ruleDescription": "Get football club president from infobox"
 "ruleURLActivationCondition": ["en\.wikipedia\.org/wiki"]
 "rulePreconditionType": "Any"
 "rulePreconditions" :   [ 
                             {
			      "ecCSSSelector" : "tr:nth-child(5) .infobox-label" 
			      "ecTextCondition": "President"
			      "ecRuleCSSSelector" : "tr:nth-child(5) .agent"			      			      
                             },
                             
                             {
			      "ecCSSSelector" : "tr:nth-child(6) .infobox-label" 
			      "ecTextCondition": "President"
			      "ecRuleCSSSelector" : "tr:nth-child(6) .agent"			      			      
                             },
                             
                             {
			      "ecCSSSelector" : "tr:nth-child(7) .infobox-label" 
			      "ecTextCondition": "President"
			      "ecRuleCSSSelector" : "tr:nth-child(7) .agent"			      			      
                             },
                             
                             {
                               "ecCSSSelector" : "tr:nth-child(8) .infobox-label" 
                               "ecTextCondition": "President"
                               "ecRuleCSSSelector" : "tr:nth-child(8) .agent"
                             },
                             
                             {
			       "ecCSSSelector" : "tr:nth-child(9) .infobox-label" 
			       "ecTextCondition": "President"
			       "ecRuleCSSSelector" : "tr:nth-child(9) .agent"
                             },
                             
                             {
			       "ecCSSSelector" : "tr:nth-child(8) .infobox-label" 
			       "ecTextCondition": "Chairman"
			       "ecRuleCSSSelector" : "tr:nth-child(8) .agent"
                             },
                             
                             {
			     	"ecCSSSelector" : "style+ .vcard tr:nth-child(9) .infobox-label" 
			     	"ecTextCondition": "Chairman"
			     	"ecRuleCSSSelector" : "tr:nth-child(9) .agent"
                             }
                             
                             
                             
                          ]                       
 "ruleCSSSelector": "#content h1.firstHeading"
 "ruleTargetAttribute": "text"
 "ruleContentCondition": ""
 "ruleReturnsMore": False
 "ruleReturnedMatchPos": 0
 "ruleReturningMoreIsError": False
 "ruleRemoveChars": ["\n", "\t"]
},




{
 "ruleName": "getLinks"
 "ruleDescription": "Extracting links rule"
 "ruleURLActivationCondition": ["en\.wikipedia\.org.*$"]
 
 "rulePreconditionType": "Any"
 "rulePreconditions" : []
 
 "ruleCSSSelector": "a[href]"
 "ruleTargetAttribute": "href"
 "ruleContentCondition": "en\.wikipedia\.org/.*$"
 "ruleReturnsMore": True
 "ruleReturnedMatchPos": -1
 "ruleReturningMoreIsError": False
 
 # other parameters needed
}

]


}

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

IMPORTANT: Some properties are not fully supported and/or may result in errors and exceptions. 


# Related projects

To make life easier, you may use the following extensions to extract the relevant css selectors that are required in .ecr files:

* Chrome extension SelectorGadget to specify CSS seslectors used in .exr files. See: https://chrome.google.com/webstore/detail/selectorgadget/mhjhnkcfbdhnjickkkdbjoemdmbfginb?hl=en and   https://selectorgadget.com/   

* Firefox extension ScrapeMate. See https://addons.mozilla.org/en-US/firefox/addon/scrapemate/
