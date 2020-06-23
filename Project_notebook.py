#!/usr/bin/env python
# coding: utf-8

# # Assessing childhood obesity through geospatial placement of fast food restaurants

# ## *A Coursera Applied Data Science Capstone project notebook* 

# The main data set that will be used is the London Borough Profiles and the London Borough Atlas from the London Datastore (www.data.london.gov.uk). These two files are available in Excel format and they will provide data on prevalence of childhood obesity in each of the boroughs.
# 
# 

# We first install and import all the relevant libraries and packages for the data analysis.

# In[1]:


import numpy as np      # to handle data in a vectorized manner
import statistics       # for statistical analysis
from scipy import stats
from sklearn import preprocessing

import pandas as pd     # for data analsysis and dataframes
pd.set_option('display.max_columns', None)  # to enable maximum column display
pd.set_option('display.max_rows', None)     # to enable maximum row display

import json # library to handle JSON files

get_ipython().system('conda install -c conda-forge geopy --yes ')
from geopy.geocoders import Nominatim # to convert an address into latitude and longitude values
import pgeocode # to convert postcodes into coordinates
import geopy.distance # to calculate distance between coordinates

import requests # library to handle requests
from pandas.io.json import json_normalize # tranform JSON file into a pandas dataframe

# Matplotlib and associated plotting modules
import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')


get_ipython().system('conda install -c conda-forge folium=0.5.0 --yes ')
import folium  # map rendering library

import warnings; warnings.simplefilter('ignore')

print('Libraries imported.')


# First, we download the London Borough Profile data sheet from (https://data.london.gov.uk/dataset/london-borough-profiles) and save it to a temporary dataframe. 

# In[2]:


temp_data = pd.read_excel("https://data.london.gov.uk/download/london-borough-profiles/80647ce7-14f3-4e31-b1cd-d5f7ea3553be/london-borough-profiles.xlsx", sheet_name="Data")


# In[3]:


# We check the entire data sheet to see which rows are of use to us. 
temp_data 


# We are interested only in the 32 Boroughs of London (from index = 2 to index = 33; City of London is not a borough) so we only keep those and save them into a new dataframe

# In[4]:


borough_data = temp_data.loc[2:33, ]
borough_data.reset_index(inplace=True, drop=True)
borough_data


# Since we are interested in the Childhood Obesity Prevalence rates only, we create a new dataframe with just the name of the borough and the corresponding childhood obesity prevalence rate.

# In[5]:


obesity_data=borough_data[['Area name','Childhood Obesity Prevalance (%) 2015/16']]
obesity_data.rename(columns={'Area name':'Borough'}, inplace=True)
obesity_data


# For each borough, we will consider the 'centre' of the borough to be the location of the respective borough council (i.e. town hall). The postcode for each borough council has been found directly from the internet. 

# In[6]:


# we first save all the postcodes into a list and then add it to the main dataframe.
council_postcode=['IG11 7LU', 'N11 1NP', 'DA6 7LB', 'HA9 0FJ', 'BR1 3UH', 'WC1H 9JE', 'CR0 1EA', 'W5 2HL', 'EN1 3XA', 'SE18 6PW', 'E8 1EA', 'W6 9JU', 'N22 8LE', 'HA1 2XY', 'RM1 3BD', 'UB8 1UW', 'TW3 4DN', 'N1 2UD', 'W8 7NX', 'KT1 1EU', 'SW2 1RW', 'SE6 4RU', 'SM4 5DX', 'E16 2QU', 'IG1 1DD', 'TW1 3BZ', 'SE1 2QH', 'SM1 1EA', 'E14 2BG', 'E17 4JF', 'SW18 2PU', 'SW1E 6QP']
obesity_data['Post Code']=council_postcode
obesity_data.head()


# Next, we use pgeocode to extract the coordinates for each post code from the above dataframe and store it in the same dataframe.

# In[7]:


coord=[]
longlist=[]
latlist=[]
nomi = pgeocode.Nominatim("GB") # Selecting Great Britain as the country. 

for i in obesity_data.index:
    coord=nomi.query_postal_code(obesity_data.iloc[i]['Post Code'])
    latlist.append(coord['latitude'])
    longlist.append(coord['longitude'])
obesity_data['Latitude']=latlist
obesity_data['Longitude']=longlist
obesity_data_test=obesity_data
obesity_data.head()


# We draw a bar chart to compare the prevalence of childhood obesity in the London boroughs.

# In[8]:



barx=obesity_data['Borough'].tolist()
bary=obesity_data['Childhood Obesity Prevalance (%) 2015/16'].tolist()

plt.figure(figsize=(20,10))

plt.bar(barx, bary, width=0.7)
plt.xlabel("Borough")
plt.ylabel("Childhood Obesity Prevalance (%) 2015/16")
plt.title("Childhood Obesity Prevalance (%) in London boroughs in 2015/16")

plt.xticks(barx, rotation='vertical')

plt.show()


# To automate the process of finding the schools and the fast food restaurants near each school, we will build a function and use it to loop through each of the boroughs.

# In[30]:



def mainfunction(a):   # define the main function
    def averageoflist(l): # defining an averaging function that will be used later to calculate the mean.
        if len(l)!= 0:
            avg = sum(l) / len(l) 
            return avg
        else: 
            pass 
    global distance_temp2 # defining global variables for this function
    global distance_temp3
    global number_temp1
    global number_temp2

    CLIENT_ID = 'FVVCW3X51XNUA3KIGWF5RDKHGL5PWIO1CLXO1ALHDYKEX14D' # Foursquare ID
    CLIENT_SECRET = '0UHETLYLXBFQJ2HQRN3Y1XXVTKIIH5J1UTXANHEICWT2EFB2' # Foursquare Secret
    VERSION = '20200617' # Foursquare API version
    LIMIT1 = 10 # limit for the number of schools returned
    radius1 = 2000 # radius for the schools 
    LIMIT2 = 50 # limit for the number of fast food restaurants returned
    radius2 = 1000 # radius for the fast food restaurants
    categoryid_school='4bf58dd8d48988d13b941735'     # search category ID for schools
    categoryid_ffr= '4bf58dd8d48988d16e941735'       # search category ID for fast food restaurants
    
    
    # We next define the url that will be used to get the results
    url = 'https://api.foursquare.com/v2/venues/search?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}&categoryId={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET, 
    VERSION, 
    obesity_data.loc[a][3], 
    obesity_data.loc[a][4], 
    radius1, 
    LIMIT1, categoryid_school)
    
    results = requests.get(url).json()
    schools = results['response']['venues']
    nearby_schools = json_normalize(schools) # flatten JSON
    
    count1=0  # these are the two counters that are used to keep count of the number of schools and fast food restaurants
    count2=0
    
    for j in nearby_schools.index:                     # the first for loop that will search for the restaurants
            nearby_schools.iloc[j]['location.lat']
            nearby_schools.iloc[j]['location.lng']

            # the second url will be used to return results for fast food restaurants
            url = 'https://api.foursquare.com/v2/venues/search?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}&categoryId={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            nearby_schools.iloc[j]['location.lat'], 
            nearby_schools.iloc[j]['location.lng'], 
            radius2, 
            LIMIT2, categoryid_ffr)
            url 
            
            results_ffr = requests.get(url).json()
            ffr = results_ffr['response']['venues']
            nearby_ffr = json_normalize(ffr) # flatten JSON
            
            distance_temp1=[]                # defining an empty list that will be used to store the distances
            
            count2+=1                       # second counter
            
            
            # second for loop used to loop through each restaurant and measure the distance from the respective school
            
            for k in nearby_ffr.index:      

                    nearby_ffr.iloc[k]['location.lat']
                    nearby_ffr.iloc[k]['location.lng']

                    coords_1 = (nearby_ffr.iloc[k]['location.lat'], nearby_ffr.iloc[k]['location.lng']) # location of the restaurant
                    coords_2 = (nearby_schools.iloc[j]['location.lat'], nearby_schools.iloc[j]['location.lng']) # location of the school
                    distance_temp1.append(geopy.distance.vincenty(coords_1, coords_2).km) # Vincenty method of calculating distance between the two points
                    #print("Borough:", obesity_data.loc[a][0], "School:", nearby_schools.iloc[j]['name'], "Fast food restaurant:", nearby_ffr.iloc[k]['name'])
                    count1+=1
                    #print(distance_temp1)
                    
            print("Average distance of all restaurants from",nearby_schools.iloc[j]['name'], ":",averageoflist(distance_temp1)) 
            
            distance_temp2=distance_temp2+distance_temp1 # adding the mean distance to a list containing all the mean distances from the particular school
    print("Average distance of restaurants from schools in ",obesity_data.loc[a][0], ":",averageoflist(distance_temp2))
    distance_temp3.append(averageoflist(distance_temp2)) # adding all the mean distances to a list containing all the mean distances within a borough
    number_temp1.append(count1)
    number_temp2.append(count2)


# In[31]:


# next, we run the function using a for loop through the main dataframe. 

number_temp1=[]
number_temp2=[]
distance_temp2=[]
distance_temp3=[]
distance_temp4=[]

for i in obesity_data.index: 
    mainfunction(i)
 


# In[11]:


# this block is used to calculate the average number of restaurants in each borough by cycling through the main counter list 
# and averaging the values

number_temp1,number_temp2
number_temp3=[]
for m in pd.DataFrame(number_temp1).index:
    number_temp3.append(number_temp1[m]/number_temp2[m])


# In[12]:


# The final dataframe is then displayed

obesity_data_temp3=obesity_data

obesity_data_temp3.insert(5, "Mean distance", distance_temp3, True)
obesity_data_temp3.insert(6, "Ave. number of restaurants", number_temp3, True)

obesity_data_temp3


# In[16]:


x=obesity_data_temp3['Childhood Obesity Prevalance (%) 2015/16'].to_numpy()
y=obesity_data_temp3['Mean distance'].to_numpy()
z=obesity_data_temp3['Ave. number of restaurants'].to_numpy()


# In[17]:


# A scatter plot is drawn to show the relation between the two variables.

plt.figure(figsize=(15,8))
plt.scatter(x,y)
plt.xlabel("Childhood Obesity Prevalance (%) 2015/16")
plt.ylabel("Mean distance of restaurants from the nearest sampled school (km)")
plt.title("Correlation")

stats.pearsonr(x,y)      # Pearson's correlation coefficient


# In[18]:


plt.figure(figsize=(15,8))
plt.scatter(x,z)
plt.xlabel("Childhood Obesity Prevalance (%) 2015/16")
plt.ylabel("Average number of restaurants within a 1 km radius of the sampled school")
plt.title("Correlation")

stats.pearsonr(x,z)   # Pearson's correlation coefficient


# We next want to display all the search results on a map of London. For that, we first find out the coordinates of London.

# In[19]:


geolocator = Nominatim(user_agent="test-user")
location = geolocator.geocode("London, Great Britain")
lat_lon = location.latitude
long_lon = location.longitude
lat_lon, long_lon

map_london = folium.Map(location=[lat_lon, long_lon], zoom_start=10) # We use folium to develop the map.


# Next, we use three embedded for loops to cycle through each borough, each school, and each fast food restaurant and be displayed on the London map. 
# 

# In[27]:


CLIENT_ID = 'FVVCW3X51XNUA3KIGWF5RDKHGL5PWIO1CLXO1ALHDYKEX14D' # Foursquare ID
CLIENT_SECRET = '0UHETLYLXBFQJ2HQRN3Y1XXVTKIIH5J1UTXANHEICWT2EFB2' # Foursquare Secret
VERSION = '20200617' # Foursquare API version
LIMIT1 = 10 # limit for the number of schools returned
radius1 = 2000 # radius for the schools 
LIMIT2 = 50 # limit for the number of fast food restaurants returned
radius2 = 1000 # radius for the fast food restaurants
categoryid_school='4bf58dd8d48988d13b941735'     # search category ID for schools
categoryid_ffr= '4bf58dd8d48988d16e941735'       # search category ID for fast food restaurants

# The code inside the loops is exactly the same as previously used in the function. 

for i in obesity_data.index:
    
    url = 'https://api.foursquare.com/v2/venues/search?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}&categoryId={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET, 
    VERSION, 
    obesity_data.loc[i][3], 
    obesity_data.loc[i][4], 
    radius1, 
    LIMIT1, categoryid_school)
    
    results = requests.get(url).json()
    
    schools = results['response']['venues']
    nearby_schools = json_normalize(schools) 
    
    
    for j in nearby_schools.index:
            nearby_schools.iloc[j]['location.lat']
            nearby_schools.iloc[j]['location.lng']

            url = 'https://api.foursquare.com/v2/venues/search?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}&categoryId={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            nearby_schools.iloc[j]['location.lat'], 
            nearby_schools.iloc[j]['location.lng'], 
            radius2, 
            LIMIT2, categoryid_ffr)
            
            results_ffr = requests.get(url).json()
            ffr = results_ffr['response']['venues']

            nearby_ffr = json_normalize(ffr) 
            
                        
            for k in nearby_ffr.index:

                    nearby_ffr.iloc[k]['location.lat']
                    nearby_ffr.iloc[k]['location.lng']

                    coords_1 = (nearby_ffr.iloc[k]['location.lat'], nearby_ffr.iloc[k]['location.lng'])
                    coords_2 = (nearby_schools.iloc[j]['location.lat'], nearby_schools.iloc[j]['location.lng'])
                                      
                    # We use Circle Marker to mark the respective points and label them accordingly.
                    
                    label_schools = '{}'.format(nearby_schools.iloc[j]['name'])
                    label_schools = folium.Popup(label_schools, parse_html=True)
                    folium.CircleMarker(
                        [nearby_schools.iloc[j]['location.lat'], nearby_schools.iloc[j]['location.lng']],
                        radius=5,
                        popup=label_schools,
                        color='red', # All schools to be marked with a red circle
                        fill=True,
                        fill_color='#cc3131',
                        fill_opacity=0.7,
                        parse_html=False).add_to(map_london) 

                    label_ffr = '{}'.format(nearby_ffr.iloc[k]['name'])
                    label_ffr = folium.Popup(label_ffr, parse_html=True)
                    folium.CircleMarker(
                        [nearby_ffr.iloc[k]['location.lat'], nearby_ffr.iloc[k]['location.lng']],
                        radius=5,
                        popup=label_ffr,
                        color='blue', # All fast food restaurants to be marked with a blue circle
                        fill=True,
                        fill_color='#3186cc',
                        fill_opacity=0.7,
                        parse_html=False).add_to(map_london) 

             
                    
map_london


# We also mark the boroughs (via the respective coordinates of each borough council) with those that have childhood obesity rates greater than the global average (marked in red) and those that have childhood obesity rates lower than the global average (marked in blue). 

# In[25]:


map_london2 = folium.Map(location=[lat_lon, long_lon], zoom_start=10)


for i in obesity_data.index:
    if obesity_data.iloc[i][1]>18:

            label_boroughs = '{}, {:.2f} %'.format(obesity_data.iloc[i][0], obesity_data.iloc[i][1])
            #label_boroughs = folium.Popup(label_boroughs, parse_html=True) 
           
            folium.CircleMarker(
            [obesity_data.iloc[i]['Latitude'], obesity_data.iloc[i]['Longitude']],
            radius=5,
            popup=label_boroughs,
            color='red',
            fill=True,
            fill_color='#cc3131',
            fill_opacity=0.7, 
            parse_html=True).add_to(map_london2)
            
    else:
        
            label_boroughs = '{}, {:.2f} %'.format(obesity_data.iloc[i][0], obesity_data.iloc[i][1])
            #label_boroughs = folium.Popup(label_boroughs, parse_html=True) 
           
            folium.CircleMarker(
            [obesity_data.iloc[i]['Latitude'], obesity_data.iloc[i]['Longitude']],
            radius=5,
            popup=label_boroughs,
            color='blue',
            fill=True,
            fill_color='#3186cc',
            fill_opacity=0.7, 
            parse_html=True).add_to(map_london2)

map_london2


# Thank you for going through this notebook. 
