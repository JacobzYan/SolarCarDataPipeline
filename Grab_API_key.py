import os
import sys
import csv
from pathlib import Path



# Please include a CSV named ".API_Keys.csv" in your root directory with column names of Service and Key that hold service name and API key respectively
def Grab_API_Key(Service):
    # Paste the path to a text document containing your API key here
    filename = Path('~/.API_Keys.csv')
    filename = os.path.expanduser('~/.API_Keys.csv')

    if not os.path.isfile(filename):
        print('API KEY FILENAME NOT FOUND')
        return None


    # Read CSV
    with open(filename, 'r') as file:
        Data = list(csv.reader(file))
    
    # Find column title indexes
    indexes = {}
    for var in Data[0]:
        indexes[var] = list(Data[0]).index(var)

    # Check if requested service is listed in the file
    kept_row = None
    for row in Data:
        if row[indexes['Service']] == Service:
            kept_row = row
            break
    if kept_row == None:
        print('COULD NOT FIND API KEY IN THE LISTED FOLDER')
        return None


    return kept_row[indexes['Key']]


# Testing
if __name__ == '__main__':
    
    # Get service name
    if len(sys.argv) < 2:
        print('NO ARG PROVIDED, RETURING TESTING KEY')
        Service = 'Testing'
    else:
        Service = sys.argv[1]
    Key = Grab_API_Key(Service)
    print(f'Grabbed Key: {Key}')
