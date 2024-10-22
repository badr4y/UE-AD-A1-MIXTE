import grpc
from concurrent import futures

# Importing the generated gRPC classes from the protocol buffers
import showtime_pb2
import showtime_pb2_grpc
import json

# Defining the gRPC service for managing showtimes
class ShowtimeServicer(showtime_pb2_grpc.ShowtimeServicer):

    def __init__(self):
        # Loading the showtime schedule from a JSON file
        with open('{}/data/times.json'.format("."), "r") as jsf:
            self.db = json.load(jsf)["schedule"]  # Load the schedule data

    # Method to retrieve movies by a given date
    def getMoviesByDate(self, request, context):
        print('ici')
        # Loop through the schedule to find matching showtimes by date
        for showtime in self.db:
            if showtime['date'] == request.date:  # Check if the requested date matches
                print("time found!")
                # If a match is found, return the showtime data
                return showtime_pb2.ShowTimeData(date=showtime['date'], movies=showtime['movies'])
        
        # If no matching date is found, return an empty result
        return showtime_pb2.ShowTimeData(date='', movies=[])

# Function to start the gRPC server
def serve():
    # Create a gRPC server with a thread pool of workers
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add the Showtime service implementation to the server
    showtime_pb2_grpc.add_ShowtimeServicer_to_server(ShowtimeServicer(), server)
    
    # Bind the server to a specific port for incoming requests
    server.add_insecure_port('[::]:3002')
    
    # Start the server
    server.start()
    
    # Keep the server running indefinitely
    server.wait_for_termination()

# Entry point of the script
if __name__ == '__main__':
    serve()  # Start the gRPC server
