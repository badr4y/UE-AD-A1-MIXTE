import grpc
from concurrent import futures


import showtime_pb2
import showtime_pb2_grpc
import json
class ShowtimeServicer(showtime_pb2_grpc.ShowtimeServicer):

    def __init__(self):
        with open('{}/data/times.json'.format("."), "r") as jsf:
            self.db = json.load(jsf)["schedule"]
    
    def getMoviesByDate(self, request, context):
        for showtime in self.db:
            if showtime['date'] == request.date:
                print("time found!")
                # Return the showtime data if the date matches
                return showtime_pb2.ShowTimeData(date=showtime['date'], movies=showtime['movies'])
        
        # If no matching date is found, return empty result
        return showtime_pb2.ShowTimeData(date='', movies=[])
       
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    showtime_pb2_grpc.add_ShowtimeServicer_to_server(ShowtimeServicer(), server)
    server.add_insecure_port('[::]:3002')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

