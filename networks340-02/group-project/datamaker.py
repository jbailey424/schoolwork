import json
import pandas
from bs4 import BeautifulSoup
from datetime import timedelta
from isoduration import parse_duration
from warnings import warn
from NwalaTextUtils.textutils import derefURI
from NwalaTextUtils.textutils import genericErrorInfo
from NwalaTextUtils.textutils import getPgTitleFrmHTML
from PyMovieDb import IMDB
import time
from imdb_scraper import *
from dataset_creators import *
import os
from tqdm import tqdm

'''
These are three functions i made to execute the scraping and utilize the given functions in imdb_scraper
First is itemizecrew, which takes the title id of some movie scraped from imdb and returns a list of all the crew and their roles, in the form of a smaller list (role, crew). It also has an optional parameter to input the directors name, and as it loops through the crew of a movie it will only add them to the itemized list if their name does not match the inputted director, to avoid self loops when a network is drawn with links between director and crew

 Next is film_credits, which takes a directors id and creates a "directordict" containing keys and values for the given 'dir_id', scraped from imdb using given functions. It includes directors id, full name, and a list of movies for which they are credited for directing. After initializing this dict and filling in the id and name, it loops through every director credit using Nwala's get_full_credits_for_director function, and it adds a movie dictionary to the list of movies in the director dict. In the movie dict, there is 'title_id', 'title', and 'crew' where crew is a list from the itemizecrew function.
 
 Finally there is isvalid, a simple function that takes a list of strings and checks if a given (role, name) credit has a role which matches one of the given valid strings. For our dataset, I used the valid list ['direct', 'writ', 'produce', 'cinematography', 'casting by', 'editing', 'music by']. Typically, this returned credits for assistant directors, producers, directors of different departments, lead writers and editors, music composers, casting leaders, and head cinematographers. This purposefully filters out credits from art or technical crew departments, because if we credited everyone we would have thousands of credits for each movie and our network would explode. Each of the above functions have the validroles list as a parameter; you input it into film_credits when youre collecting data on a specific director, which feeds it internally into itemize crew, which will then only record crew members with valid roles. If you give no valid role input to your film_credits function it will record every crew member.

'''

def itemizecrew(title_id, directorname = 'no one', validroles = ['']): #this returns all the crewmembers as 'role', 'name' pairs, from a given title_id
    crewlist = []
    for i in get_full_crew_for_movie(title_id)['full_credits']: 
        for r in i['crew']:
            if r['name'] != directorname: #if you input the directors name, this will avoid self loops
                if isvalid((i['role'], r['name']), validroles) == True:
                    crewlist.append((i['role'], r['name']))
            #print(crewmember)
    return crewlist #returns a list of lists, containing (role, pair) for crew members whos credits match given valid roles

def film_credits(dir_id, validroles = ['']): #takes director id and returns a "directordict"
                        #directordict has id, name, and a movies dict which has id, title, and crew list from itemizecrew function
    directordict = {'dir_id':dir_id,
                    'name':(directors.loc[directors['id'] == dir_id, 'FirstName'].iloc[0] + ' ' + directors.loc[directors['id'] == dir_id, 'LastName'].iloc[0]),
                    'movies':[]}
    #print('dict made for ', directordict['name'])
    for i in get_full_credits_for_director(dir_id)['credits']:
        if is_feature_film(i['title_id']) == True:
            movie = {'title_id':i['title_id'], 'title':i['title'], 'crew':itemizecrew(i['title_id'], directordict['name'], validroles = validroles)}
            directordict['movies'].append(movie)
    return directordict

def isvalid(credit, validroles = ['']):
    for valid_role in validroles:
        if valid_role in credit[0].lower():
            return True
    return False

'''
Here is the code which actually runs when you call this script, first it loads in your director csv data, then it initiates a jsonl file 'new_credits.jsonl' and, if the file exists, it checks and records which director are already present in the data and prints their ids. 
'''
datapath = '100_film_directors.csv' #here are the inputs. you can change the director source, jsonl name/location, and the valid roles here.
jsonl_file = 'new_credits.jsonl'
validroles = ['direct', 'writ', 'produce', 'cinematography', 'casting by', 'editing', 'music by']

imdb = IMDB() 
directors = pandas.read_csv(datapath) #given a csv of directors with URIs
directors['id'] = directors['IMDb_URI'].str.extract(r'/name/([a-z0-9]+)/') #extract the id from URI and make it into a new column

dir_ids_in_jsonl = set()

if os.path.isfile(jsonl_file): #if the file already exists:
    with open(jsonl_file, 'r') as f:
        for line in f:
            movie_credits = json.loads(line) #go through each line in the file and record the dir_id
            dir_id = movie_credits['dir_id']
            dir_ids_in_jsonl.add(dir_id)

print(dir_ids_in_jsonl) #report which directors are already found in the data

with open(jsonl_file, 'a') as f:
    for idx, row in tqdm(directors.iterrows(), total=len(directors)): #for each row in your input dataframe
        dir_id = row['id']
        if dir_id in dir_ids_in_jsonl: #if the director is already in the data, pass this row on the loop
            continue
        movie_credits = film_credits(dir_id, validroles) #if the director is not in the data, scrape and record their credits to the jsonl based on the inputted valid role list
        f.write(json.dumps(movie_credits) + '\n')
        dir_ids_in_jsonl.add(dir_id) #finally add the id to the list of already recorded directors. If for some reason the same director is in your input csv twice, this will keep them from being double-credited