from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from enum import Enum
import random
import numpy as np
import pickle
import pika
import pprint

app = FastAPI()
class Vehicle_Type(Enum):
    ambulance = 1
    firetruck = 2
    police_car = 3
    #tow_truck = 4

##Just for reference
class Tile_Type(Enum):
    DISASTER = 0
    FREE = 1
    STATION = 2
    TERRAIN = 3

current_path = []
map = [[1, 1, 1, 0, 1], [1, 1, 0, 0, 1], [0, 1, 0, 1, 1], [1, 1, 0, 0, 0],  [1, 1, 1, 1, 1]]
stations = []

# Dispatch notify all stations (level + coordinates)
# Dispatch choose based on the response and list (shortest distance) and dispatch sends a
# message designating which stations to send
class Station:
    """
    Station Object
    number -> id of the station
    vehicles -> list of vehicle objects per station
    coordinates -> coords of station
    """
    def __init__(self, number, vehicles, coordinates):
        self.number = number
        self.vehicles = vehicles
        self.coordinates = coordinates

class Vehicle:
    """
    Station Object
    id -> id of the vehicle
    available -> availability of vehicle
    coordinates -> coords of vehicle
    """
    def __init__(self, id, vehicle, coordinates, available):
        self.id = id
        self.vehicle = vehicle
        self.coordinates = coordinates
        self.available = available

def generate_vehicles(number_of_vehicles, station_coords):
    """
    Generates vehicles with a random vehcile type
    """
    vehicles = []
    for i in range(number_of_vehicles):
        vehicle = Vehicle(random.randint(100, 999),  random.choice(list(Vehicle_Type)), station_coords, True)
        vehicles.append(vehicle)
    return vehicles

def build_stations(number_of_stations, coordinates, station_num):
    """
    Generates stations with 5 vehicles per station at the specified coordinates
    """
    stations = []
    for i in range(number_of_stations):
        station = Station(station_num[i], generate_vehicles(5, coordinates[i]), coordinates[i])
        stations.append(station)
    return stations

def generate_path(maze, source, destination, visited, path, paths, rows, columns):
    """
    Generates a path given the map with the source and destination
    """
    if source == destination:
        paths.append(path[:])  
        return
    if len(paths) != 0:
        return paths
    
    x, y = source
    visited[x][y] = True
    if x >= 0 and y >= 0 and x < rows and y < columns and maze[x][y] == 1:
        neighbors = [(1,0),(-1,0),(0,-1),(0,1)]
        for index, neighbor in enumerate(neighbors):
            next_xsquare = x + neighbor[0]
            next_ysquare = y + neighbor[1]
            if (next_xsquare < columns and next_xsquare >= 0 and next_ysquare < rows and next_ysquare >= 0 and (not visited[next_xsquare][next_ysquare])):
                    path.append((next_xsquare, next_ysquare))
                    new_source = (next_xsquare, next_ysquare)
                    generate_path(maze, new_source, destination, visited, path, paths, rows, columns)
                    path.pop()
    visited[x][y] = False
    return paths

def get_paths(maze, source, destination):
    """
    Actaul function that should be called to generate the path for a vehicle
    """
    rows = len(maze)
    columns = len(maze[0])
    visited = [[False]*rows for _ in range(columns)] #may be inversed
    path = [source]
    paths = []
    path = generate_path(maze, source, destination, visited, path, paths, rows, columns)
    current_path.append(path)
    return path

##Receive Dispatch Request
def handle_dispatch_request():
    ##Instatiation Code
    ##Reuires Some More Work
    while True:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='Dispatch-Queue')

        def callback(ch, method, properties, body):
            request = pickle.loads(body)
            print("Received %r" % request)
            connection.close()

        tag = channel.basic_consume(queue='Dispatch-Queue', on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

## Sends resposne to dispatch regarding status
def send_dispatch_response(station_num, status):
    station_response = {
        "station": station_num,
        "status": status
    }
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='Station-Response')
    channel.basic_publish(exchange='', routing_key='Station-Response', body=pickle.dumps(station_response))
    connection.close()

##Testing
def test_path():
    map = [[1, 1, 1, 0, 1], [1, 1, 0, 0, 1], [0, 1, 0, 1, 1], [1, 1, 0, 0, 0],  [1, 1, 1, 1, 1]]
    print(np.matrix(map))
    start = (0,0)
    end = (4,4)
    path = get_paths(map, start, end)
    print("Path is: ")
    print(path)

##Testing
def create_get_test_path():
    start = (0,0)
    end = (4,4)
    path = get_paths(map, start, end)
    return path


# Initializes Hard Coded Stations (Not Used if Dispatch Sends the Starting Locations)
def init_stations():
    station_coords = []
    station1 = (3,5)
    station2 = (6,2)
    station3 = (9,9)
    station4 = (8,1)
    station_coords.append(station1)
    station_coords.append(station2)
    station_coords.append(station3)
    station_coords.append(station4)

    station_number = []
    station1_num = 1234
    station2_num = 3612
    station3_num = 7624
    station4_num = 5135
    station_number.append(station1_num)
    station_number.append(station2_num)
    station_number.append(station3_num)
    station_number.append(station4_num)
    return build_stations(4, station_coords, station_number)

#Displaying Initial Stations
def display_stations():
    for station in stations:
        print("Station: ")
        print(station.number)
        print(station.coordinates)
        print("Vehicles: ")
        for vehicle in station.vehicles:
            print(vehicle.id)
            print(vehicle.vehicle)
            print(vehicle.coordinates)
            print(vehicle.available)
        print("------------")

test_path()

if __name__ == "__station__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
   