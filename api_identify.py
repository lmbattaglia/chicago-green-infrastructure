#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 21:55:50 2026

@author: loganbattaglia

#Use Anthropic's API for Claude to classify work descriptions. Requires
installation of the anthropic module via:

    conda install anthropic -c conda-forge.

"""

#  Initial setup, import needed modules

import pandas as pd
from anthropic import Anthropic
from pydantic import BaseModel
import os
import sys

#  List file names at the top of scripts 

#     apikey_file = contains the Claude API key
#     input_file  = raw data from Chicago building permits
#     column_file = building permit column names and descriptions
#     output_file = where the results should go


apikey_file = 'claude_apikey.txt'
input_file  = 'chicago_building_permits.csv'
column_file = 'chicago_building_permits_metadata.csv'
output_file = 'chicago_permits_parsed.xlsx'

#
#  Define a pydantic object for returning data from Claude.
#
#  The definition gives a list of attributes the object will
#  have along with the data types of the values of the
#  attributes.
#
#  These objects are a little like enhanced dictionaries but
#  with built-in documentation. That allows Claude to see how
#  the data should be returned. Note that the token declaration
#  says it's a dictionary with strings as keys and ints as
#  values.
#

class PermitClassification(BaseModel):
    work_category: str  
    is_resilience_infrastructure: str 
    notes: str
    tokens: dict[str, int]

#
#  Load the API key
#

if os.path.exists('claude_apikey.txt'):
    with open('claude_apikey.txt') as fh:
        apikey = fh.readline().strip()
else:
    print('error: Anthropic API key not found')
    sys.exit()

#
#  Create the Anthropic client
#

client = Anthropic(api_key=apikey)

#
#  Claude model and pricing as of 2/2026 per input and output
#  token
#

model = "claude-sonnet-4-6"
p_in = 3/1e6
p_out = 15/1e6

#============================================================
#  Read the raw data and pick a sample to examine
#============================================================

#  Read the raw data

cols = pd.read_csv(column_file)

raw = pd.read_csv(input_file)

print('Records read',len(raw))

#
#  Pick a random sample of permits. There may be more than one
#  record per address so draw the sample from the IDs.
#
#  The random_state parameter initializes the random number
#  generator. It's useful for testing because it ensures that
#  the same sequence of random rows is chosen each time.
#

ids = raw['id'].drop_duplicates()
ids = ids.sample(frac=0.001,random_state=788)

print('IDs selected',len(ids))

#
#  Now pick out the records for those vehicles
#

sample = raw[ raw['id'].isin(ids) ]

print('Records retained',len(sample))

#============================================================
#  Define a function for sending requests to the model
#============================================================

def ask(client,model,prompt,txt,apikey):

    # Guard against NaN/None coming in
    
    if not isinstance(txt, str):
       txt = ""
       
    #  clean up spacing

    tidy = ' '.join(txt.split())

    #  embed the text in the prompt at the {}

    my_ask = prompt.format(tidy)

    #  build the request and make the API call

    message = client.messages.parse(

        #  model indicates the model to use

        model = model,

        #  max_tokens guards against excessive output

        max_tokens=1024,

        #  system gives Claude a role, which improves performance

        system="""
            You are an analyst examining building permits submitted to the City of Chicago. Your goal is to classify the building permits
            into broad categories and identify whether or not they involve climate resilient infrastructure development.
        """,

        #  messages gives one or more specific questions

        messages=[
            {
                "role": "user",
                "content": my_ask
            }
        ],

        #  output_format indicates that the output should be in
        #  the form of a PermitClassification object

        output_format = PermitClassification,

    )

    #  extract the parsed output from the response

    res = message.parsed_output

    #  get the number of tokens used (for tracking costs)

    usage = message.usage
    res.tokens['in']  = usage.input_tokens
    res.tokens['out'] = usage.output_tokens

    #  return the result

    return res

#%%
#============================================================
#  Set up things prior to calling the API
#============================================================

#
#  Set up the text of the prompt. It's usually necessary to
#  experiment with a few different versions to get good
#  performance. It also helps to use XML-style tags to separate
#  data and instructions from other context.
#

prompt = '''
This text is a building permit work description <text>{}</text>.

Determine a category for each complaint: safety, system, and timing.
Safety indicates that the complaint could result in an accident while
the vehicle is moving. System indicates what vehicle system is affected.
Timing indicates whether it happened suddenly or has been long standing.

<instructions>
The is_resilience_infrastructure tag should be either "yes", "no", or "other".

If the is_resilience_infrastructure tag is "no", leave the work_category tag blank.

If the is_resilience_infrastructure tag is "yes", the work_category tag should be "energy generation", "heating and cooling efficiency", "water management",
"building envelope", "electric transition" or "green space". If none of those tags are
appropriate, use "other".

If the classifications are clear, return the tags and leave the notes
field blank. If any tag is ambiguous or "other", include a brief
explanation in the notes field.
</instructions>
'''

#
#  Set up for running the queries. The results will go in data.
#  If limit is not None, stop after that number of queries.
#

data = []
limit = 4

#%%
#============================================================
#  Now make the calls
#============================================================

#
#  Walk through the rows of sample one at a time. The iterrows
#  method returns a tuple with the index in the first element
#  and a series containing the row data in the second.
#

for idx,rec in sample.iterrows():

    if limit is not None:
        limit -= 1

    #  get the ID and description fields

    pid = rec['id']
    txt = rec['work_description']

    #  make the request

    res = ask(client,model,prompt,txt,apikey)

    #  print a message so the user can see what's going on

    print('\nRequest:\n')
    print(' '.join(txt.split()) if isinstance(txt, str) else "(no description)")
    print()
    print(res)

    #  append the result to the data list. keep the ID for
    #  joining onto the original data.

    data.append({
        'id':pid,
        'is_resilience':res.is_resilience_infrastructure,
        'work_category':res.work_category,
        'notes':res.notes,
        'tokens_i':res.tokens['in'],
        'tokens_o':res.tokens['out']
        })

    #  check if we've hit the limit

    if limit is not None and limit <= 0:
        break

#
#  All done: build a dataframe from the list of results and add
#  a cost column.
#

results = pd.DataFrame(data)

results['cost'] = p_in*results['tokens_i'] + p_out*results['tokens_o']

#%%
#
#  Merge it onto the original data. Use an inner join since the
#  limit may have stopped the queries before the end of the sample.
#

merged = sample.merge(results,
                      on='id',
                      how='inner',
                      validate='1:1')

#
#  Now trim it down to a subset of the original columns for
#  comparing the AI information with the original data.
#

keep_cols = [
    "id",
    "permit_",
    "permit_type",
    "application_start_date",
    "issue_date",
    "street_number",
    "street_name",
    "work_type",
    "work_description",
    "subtotal_waived",
    "total_fee",
    "census_tract",
    "ward",
    "xcoordinate",
    "ycoordinate",
    "is_resilience",
    "work_category",
    "notes",
    "cost"
    ]

trim = merged[keep_cols]

#
#  Write out the results. Don't write the index, which is just
#  row numbers.
#

trim.to_excel(output_file,index=False)

#%%
#====================================================================
#  Aside on classes in more detail.
#
#  This is purely to illustrate how classes work and is NOT needed
#  for accessing Anthropic.
#====================================================================

#
#  The following creates a class of data objects called myDF that
#  is an extension of a Pandas DataFrame. It will have all the
#  attributes and methods of a DataFrame plus a couple more
#  added here.
#

class myDF( pd.DataFrame ):

    sig = 'Howdy'

    def capcols(self):
        cols = self.columns
        caps = [c.title() for c in cols]
        return caps

#%%
#
#  Outside the class definition. Now create some sample data
#

data = {
    'alpha':[1,2,3],
    'BETA':[4,5,6]
    }

#
#  Build a standard DataFrame and a myDF for comparison
#

standard = pd.DataFrame( data )
extended = myDF( data )

#
#  Print the type
#

print( type(standard) )
print( type(extended) )

#
#  Use the normal DataFrame features of the new class
#

extended['nEW Col'] = extended['alpha']+extended['BETA']

print( extended.columns )
print( extended )
print( extended.mean() )

#
#  Check the new attribute
#

# print(standard.sig) # would be an error
print( extended.sig )

#
#  Use the new capcols method
#

print( extended.capcols() )