import argparse
import csv
import json
import sys
from datetime import datetime, timedelta

import requests
from tabulate import tabulate

URL = "http://www.euskadi.eus/aa17aCalidadAireWar/informe/datosHorarios?R01HNoPortal=true"

STATIONS = [
    {
        "name": "MAZARREDO",
        "id": 60
    },
    {
        "name": "Mª DIAZ HARO",
        "id": 81
    }
]

CONTAMINANTS = [
    {
        "name": "SO2",
        "id": 1
    },
    {
        "name": "NO2",
        "id": 2
    },
    {
        "name": "NO",
        "id": 3
    },
    {
        "name": "CO",
        "id": 4
    },
    {
        "name": "O3",
        "id": 5
    },
    {
        "name": "PM10",
        "id": 6
    }
]


# location given here
def scrape_data(station_id, station_name, date, contaminats):
    params = {'idEstacion': station_id, 'nombreEstacion': station_name, 'fecha': datetime.strftime(date, '%d/%m/%Y'),
              'formato': "csv"}

    for i in range(0, len(contaminats)):
        params["listaContaminantes[%s]" % i] = contaminats[i].get("id")
        params["listaNombresContaminantes[%s]" % i] = contaminats[i].get("name")

    # sending get request and saving the response as response object
    r = requests.post(url=URL, params=params)

    data = list(csv.reader(str(r.text).split("\n"), delimiter=";"))

    json_data = []

    for parameter in data[8:]:

        if not parameter:
            break

        hour = 1

        for data_point in parameter[1:]:

            if not data_point:
                break

            if hour == 24:
                dt = date + timedelta(days=1)
            else:
                dt = date + timedelta(hours=hour)

            contaminant = parameter[0].split(" ")[0].lower()

            json_data.append({
                "station": station_name.lower(),
                "time": datetime.strftime(dt, "%Y-%m-%d %H:%M"),
                "contaminant": contaminant,
                "measurement": data_point
            })

            hour += 1

    return json_data


def list_options():
    print("STATIONS")
    print(tabulate(STATIONS, headers="keys"))
    print("\nCONTAMINANTS")
    print(tabulate(CONTAMINANTS, headers="keys"))


if __name__ == '__main__':

    if len(sys.argv) > 1:
        if sys.argv[1] in ["-l", "--list"]:
            list_options()
            sys.exit()

    parser = argparse.ArgumentParser(description="Scrapes air quality data from Euskadi's network")

    parser.add_argument("station", type=int, help="id for the target station")
    parser.add_argument("date", help="date of the query in YYYY/MM/DD format")
    parser.add_argument('contaminants', metavar='contaminants', type=int, nargs='+',
                        help='ids for contaminants')

    parser.add_argument("-o", "--output", help="writes output to a json file", type=argparse.FileType('w'))

    args = parser.parse_args()

    station_id = None
    station_name = None
    date = None
    contaminants = []

    for station in STATIONS:
        if station["id"] == args.station:
            station_id = station["id"]
            station_name = station["name"]
            break

    date = datetime.strptime(args.date, "%Y-%m-%d")

    for id in args.contaminants:
        for contaminant in CONTAMINANTS:
            if contaminant["id"] == id:
                contaminants.append(contaminant)
                break

    if not station_id or not station_name or not date or len(contaminants) == 0:
        parser.print_help()
        sys.exit()
    else:

        data = scrape_data(station_id, station_name, date, contaminants)

        if args.output:
            json.dump(data, args.output)
        else:
            print(tabulate(data, headers="keys"))
