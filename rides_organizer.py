import csv
import os
from collections import defaultdict
from pprint import pprint
from copy import deepcopy
from math import ceil
from collections import Counter

PREFERRED_PLAN = "preferred post church plan"

# gets the path to the filename that is in the same directory as this script
filename = "nlf_rides.csv"
path = os.getcwd() + "/" + filename

# duplicate check 
users = set()

# drivers
ndrivers = []
sdrivers = []
odrivers = []
all_drivers = []

# riders
nriders = []
sriders = []
oriders = []

# final matches
matches = defaultdict(list)
preferences = defaultdict(str)

# have to manually match
unmatched = []

# process the raw csv
with open(path, newline = '', encoding="utf8") as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for idx, row in enumerate(reader):

        if idx == 0: continue

        # takes care of people who signed up twice on accident
        # make sure people know their first sign up is what counts
        # we can come back later and change this to latest if it matters
        if row[1] not in users: users.add(row[1])
        else: continue

        # mark their preference to refer to later 
        preferences[row[1]] = row[8]

        # split into drivers
        if row[6] == "Yes": 
            if row[4] == "North (Brown, Duncan, Jones, Martel, McMurtry)": ndrivers.append(row)
            elif row[4] == "South (Baker, Hanszen, Lovett, Sid Richardson, Wiess, Will Rice)": sdrivers.append(row)
            else: odrivers.append(row)

        # and riders
        else: 
            if row[4] == "North (Brown, Duncan, Jones, Martel, McMurtry)": nriders.append(row)
            elif row[4] == "South (Baker, Hanszen, Lovett, Sid Richardson, Wiess, Will Rice)": sriders.append(row)
            else: oriders.append(row)

all_drivers = ndrivers + sdrivers + odrivers



def load_balance():
    # we're prioritizing proximity here over load balancing
    # first we want to make sure there are enough north drivers
    if len(ndrivers) * 4.0 / len(nriders) < 1.0: 
        num_drivers_needed = ceil((len(nriders) - len(ndrivers) * 4.0) / 4.0)
        for _ in range(num_drivers_needed):
            if odrivers: ndrivers.append(odrivers.pop())
            else: ndrivers.append(sdrivers.pop())

def get_driver(dname):
    for driver in all_drivers:
        if dname == driver[1]:
            return driver
    raise ValueError("this driver does not exist in our records")

def match(riders, drivers):
    '''
    prioritizes people who have a strong after church preference
    this can definitely be optimized but should work just fine for now
    one more thing to consider is whether we should also only match on the 
    drivers who have preferences first, saving those who mark themselves flexible
    '''
    # first we split the riders into people who have preference and people who do not
    # now assign a north driver to each north rider brute force 
    for rider in riders:
        rname = rider[1]
        matched = False

        # the first pass is seeing if there is an optimal match possible
        for driver in drivers:
            dname = driver[1]
            if len(matches[dname]) >= 4: continue
            if driver[5] == rider[5] and (driver[8] == rider[8] or driver[8] == "I'm flexible :)" or rider[8] == "I'm flexible :)"):
                # since the driver now has a non flexible rider the driver is also now non flexible
                if driver[8] != rider[8]: driver[8] = rider[8]
                matched = True
                matches[dname].append((rname, "optimal"))
                break
        if matched: continue

        # if we get here then we know there wasn't an optimal match for after service
        # but we'll at least try to match the service 
        for driver in ndrivers:
            dname = driver[1]
            if len(matches[dname]) >= 4: continue
            if driver[5] == rider[5]:
                matched = True
                matches[dname].append((rname, "non-optimal"))
                break
        if matched: continue

        # if they get here, we could not find an appropriate match among the given set of drivers
        # let's see if there are any other current drivers that have seats left
        for dname in matches.keys():
            driver = get_driver(dname)
            if len(matches[dname]) >= 4: continue
            if driver[5] == rider[5]:
                matched = True
                if (driver[8] == rider[8] or rider[8] == "I'm flexible :)"): matches[dname].append((rname, "optimal"))
                else: matches[dname].append((rname, "non-optimal"))
                break
        if matched: continue

        # we're trying to minimize the number of drivers that have to drive but 
        # let's see if there are any drivers that aren't listed to drive that can drive 
        for driver in all_drivers:
            dname = driver[1]
            if len(matches[dname]) >= 4: continue
            if driver[5] == rider[5]:
                matched = True
                if (driver[8] == rider[8] or rider[8] == "I'm flexible :)"): matches[dname].append((rname, "optimal"))
                else: matches[dname].append((rname, "non-optimal"))
                break

        if matched: continue

        # if they got here we really were unable to either find a seat for them period
        # or they don't have someone going to the same service as them
        unmatched.append(rname)


def split_into_flexible(riders):
    non_flexible = []
    flexible = []
    for rider in riders:
        if rider[8] == "I'm flexible :)": flexible.append(rider)
        else: non_flexible.append(rider)
    return flexible, non_flexible


def match_all():
    # when matching give priority to those who have an after church preference 
    # since it'll be easier to manually adjust for those who don't end up matched
    nriders_flexible, nriders_non_flexible = split_into_flexible(nriders)
    match(nriders_non_flexible, ndrivers)
    match(nriders_flexible, ndrivers)
    sdrivers.extend(odrivers)
    sriders.extend(oriders)
    sriders_flexible, sriders_non_flexible = split_into_flexible(sriders)
    match(sriders_non_flexible, sdrivers)
    match(sriders_flexible, sdrivers)


def write_cars_vertical(cars):
    """
    Ad-hoc solution to make spreadsheet copiable outputs
    """
    

    copy_output_file = "copy_paste.csv"
    # try:
    with open(copy_output_file, 'w') as text_file:
        for car in cars:
            text_file.write((car["driver"]) + "\n")
            for rider_key in car:
                if rider_key.startswith("rider #"):
                    text_file.write((car[rider_key][0]) + "\n")
            text_file.write("\n")

    # except IOError:
        # print("I/O error") 


# turn these mantches into a list of dicts
def write():
    final_matches = []

    # construct a row 
    for driver in matches.keys():
        d = {"driver": driver}
        pref_list = []
        for idx, rider in enumerate(matches[driver]):
            idx += 1
            d["rider #" + str(idx)] = rider
            print(rider[0])
            pref_list.append(preferences[rider[0]])
        c = Counter(pref_list)
        d[PREFERRED_PLAN] = c.most_common()
        final_matches.append(d)

    pprint(final_matches)

    write_cars_vertical(final_matches)

    cols = final_matches[0].keys()
    csv_file = "matches.csv"
    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=cols)
            writer.writeheader()
            for data in final_matches:
                writer.writerow(data)
    except IOError:
        print("I/O error") 

    final_unmatched = []
    for remaining in unmatched:
        d = {"unmatched": remaining}
        final_unmatched.append(d)

    pprint(unmatched)
    if final_unmatched:
	    cols = final_unmatched[0].keys()
	    csv_file = "unmatched.csv"
	    try:
	        with open(csv_file, 'w') as csvfile:
	            writer = csv.DictWriter(csvfile, fieldnames=cols)
	            writer.writeheader()
	            for data in final_unmatched:
	                writer.writerow(data)
	    except IOError:
	        print("I/O error") 

load_balance()
match_all()

pprint(matches)
pprint(unmatched)
write()
