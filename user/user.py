# REST API
from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from werkzeug.exceptions import NotFound

# CALLING gRPC requests
import grpc
from concurrent import futures
import booking_pb2
import booking_pb2_grpc

# CALLING GraphQL requests
# todo to complete

app = Flask(__name__)

PORT = 3004
HOST = '0.0.0.0'

with open('{}/data/users.json'.format("."), "r") as jsf:
   users = json.load(jsf)["users"]

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the User service!</h1>"

@app.route("/users/<user_Id>", methods=['GET'])
def getUserInfoById(user_Id):
    # Convert filter result to a list and check if a user was found
    user = list(filter(lambda x: x['id'] == user_Id, users))
    if user:  # If the user list is not empty
        return make_response(jsonify(user[0]), 200)  # Return the first user found
    else:
        return make_response(jsonify({'error': 'User not found'}), 400)


@app.route("/users/time/<timeSinceLast>", methods=['GET'])
def getUserSinceTime(timeSinceLast):
    if timeSinceLast is None:
        return make_response(jsonify({"error": "timeSinceLastActivity parameter is required"}), 400)

    userArray = list(filter(lambda x: x['last_active'] > int(timeSinceLast), users))
    return make_response(jsonify(userArray), 200)


@app.route("/users/<userId>/booking", methods=['POST'])
def createBookingForUser(userId):
    req = request.get_json()
    date = req.get("date")
    movieId = req.get("movieid")

    # Create a gRPC channel and stub
    with grpc.insecure_channel('localhost:3003') as channel:
        stub = booking_pb2_grpc.BookingStub(channel)

        # Create the request message
        booking_request = booking_pb2.BookingRequest(userid=userId, date=date, movieid=movieId)

        # Make the gRPC call
        try:
            booking_response = stub.CreateBooking(booking_request)
            return make_response(jsonify(f"Reservation at date {date} for movie {movieId} made"), 200)
        except grpc.RpcError as e:
            return make_response(jsonify({'error': e.details()}), e.code().value[0])

@app.route("/users/<userId>/bookingsInfo", methods=['GET'])
def getMoviesInfoBookedByUser(userId):
    # Create a gRPC channel and stub
    with grpc.insecure_channel('localhost:3003') as channel:
        stub = booking_pb2_grpc.BookingStub(channel)

        # Create the request message
        booking_request = booking_pb2.BookingRequest(userid=userId)

        # Make the gRPC call
        try:
            userBookingResponse = stub.GetBookings(booking_request)
            datesWithMovieId = [booking for booking in userBookingResponse.dates if "movies" in booking]
            print(datesWithMovieId)
            moviesIds = {(movieId, movieList.date)
                        for movieList in datesWithMovieId
                        for movieId in movieList.movies}
            print(moviesIds)
            listInfoMovies = []
            for movieId in moviesIds:
                query = f"""
                {{
                    movie(id: "{movieId[0]}") {{
                        id
                        title
                        description
                        releaseDate
                    }}
                }}
                """
                movieResponse = requests.post("http://movie:3200/graphql", json={'query': query})
                if movieResponse.status_code == 200:
                    movie_info = dict()
                    movie_info['filmInfo'] = movieResponse.json()
                    movie_info['BookingDate'] = movieId[1]  # Append booking date to the movie info

                    listInfoMovies.append(movie_info)
            # Check if we found movie information
            if len(listInfoMovies) > 0:
                return make_response(jsonify(listInfoMovies), 200)
            else:
                return make_response(jsonify({'error': 'No movies found'}), 400)
        except grpc.RpcError as e:
            return make_response(jsonify({'error': e.details()}), e.code().value[0])

if __name__ == "__main__":
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT,debug=True)

