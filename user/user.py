from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from werkzeug.exceptions import NotFound

# Importing gRPC-related modules for handling communication with the booking service
import grpc
from concurrent import futures
import booking_pb2  # gRPC protocol buffer generated class for Booking service
import booking_pb2_grpc  # gRPC stub for the Booking service

# Initializing Flask application
app = Flask(__name__)

PORT = 3004  # Setting the port on which the Flask app will run
HOST = '0.0.0.0'  # Make the app accessible from any IP address

# Loading user data from a JSON file into the `users` variable
with open('{}/data/users.json'.format("."), "r") as jsf:
   users = json.load(jsf)["users"]

# Home route to verify if the service is running
@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the User service!</h1>"

@app.route("/users", methods=['GET'])
def get_users():
    # Endpoint to retrieve all bookings
    res = make_response(jsonify(users), 200)  # Create a response with the bookings data
    return res
# Endpoint to get user information by user ID
@app.route("/users/<user_Id>", methods=['GET'])
def getUserInfoById(user_Id):
    # Filter the users list to find a matching user by ID
    user = list(filter(lambda x: x['id'] == user_Id, users))
    if user:  # If a user is found, return the user info as a JSON response
        return make_response(jsonify(user[0]), 200) 
    else:
        # If no user is found, return an error response with a 400 status code
        return make_response(jsonify({'error': 'User not found'}), 400)

# Endpoint to get users based on the time since their last activity
@app.route("/users/<timeSinceLastActivity>", methods=['GET'])
def getUserSinceTime(timeSinceLastActivity):
    if timeSinceLastActivity is None:
        # If the required parameter is not provided, return an error
        return make_response(jsonify({"error": "timeSinceLastActivity parameter is required"}), 400)

    # Filter users who were active after a certain time
    userArray = list(filter(lambda x: x['last_active'] > int(timeSinceLastActivity), users))
    return make_response(jsonify(userArray), 200)

@app.route("/users/<userId>/booking", methods=['DELETE'])
def deleteBookingForUser(userId):
    req = request.get_json()  # Get the JSON request body
    date = req.get("date")
    moviesid = str(req.get("movieid"))

    if not date or not moviesid:
        return make_response(jsonify({'error': 'Date and movieid parameters are required'}), 400)

    with grpc.insecure_channel('localhost:3003') as channel:
        stub = booking_pb2_grpc.BookingStub(channel)
        # Create the gRPC request mes       sage
        delete_request = booking_pb2.DeleteBookingRequest(userid=userId, date=date, moviesid=moviesid)

        try:
            delete_response = stub.deleteBooking(delete_request)
            if delete_response.success:
                return make_response(jsonify({'message': delete_response.message}), 200)
            else:
                return make_response(jsonify({'error': delete_response.message}), 400)
        except grpc.RpcError as e:
            return make_response(jsonify({'error': e.details()}), e.code().value[0])

# Main entry point of the

# Endpoint to create a booking for a user using gRPC
@app.route("/users/<userId>/booking", methods=['POST'])
def createBookingForUser(userId):
    req = request.get_json()  # Get booking details from the request payload
    
    date = str(req.get("date"))
    movieId = req.get("movieid")
    # Create a gRPC channel and stub to communicate with the Booking service
    with grpc.insecure_channel('localhost:3003') as channel:
        stub = booking_pb2_grpc.BookingStub(channel)

        # Create the gRPC request message with booking information
        booking_info = booking_pb2.MovieDateBooking(date=date, movies=[movieId])
        booking_request = booking_pb2.AddBooking(userid=userId, bookingInfo=booking_info)
        # Make the gRPC call to the Booking service
        try:
            booking_response = stub.addBookingByUserId(booking_request)
            # Return success response upon successful booking
            return make_response(jsonify(f"Reservation at date {date} for movie {movieId} made"), 200)
        except grpc.RpcError as e:
            # Return error response if gRPC call fails
            return make_response(jsonify({'error': e.details()}), e.code().value[0])

# Endpoint to get detailed information about movies booked by a user using both gRPC and GraphQL
@app.route("/users/<userId>/bookingsInfo", methods=['GET'])
def getMoviesInfoBookedByUser(userId):
    # Create a gRPC channel and stub for Booking service
    with grpc.insecure_channel('localhost:3003') as channel:
        stub = booking_pb2_grpc.BookingStub(channel)

        # Create the request message to get user bookings
        booking_request = booking_pb2.BookingUser(userid=userId, dates=[])
        try:
            # Make gRPC call to retrieve booking data
        
            userBookingResponse = stub.getBookingByUserId(booking_request)
            # Filter bookings with movies
            datesWithMovieId = [booking for booking in userBookingResponse.dates if hasattr(booking, 'movies') and booking.movies]
            # Extract movie IDs and booking dates from the response
            moviesIds = {(movieId, movieList.date)
                         for movieList in datesWithMovieId
                         for movieId in movieList.movies}
            listInfoMovies = []
            # Iterate over the movie IDs and fetch movie details using GraphQL
            for movieId in moviesIds:
                query = f"""
                                {{
                                    movie_with_id(_id: "{movieId[0]}") {{
                                        id
                                        title
                                        director
                                        rating
                                    }}
                                }}
                """
                # Make a request to the GraphQL service to get movie details
                movieResponse = requests.post("http://localhost:3001/graphql", json={'query': query})
                if movieResponse.status_code == 200:
                    movie_data = movieResponse.json().get('data', {}).get('movie_with_id', {})
                    if movie_data:
                        # Add movie information to the result list
                        movie_info = {
                            'BookingDate': movieId[1],
                            'filmInfo': movie_data
                        }
                    listInfoMovies.append(movie_info)

            # If movie details are found, return them as a JSON response
            if len(listInfoMovies) > 0:
                return make_response(jsonify(listInfoMovies), 200)
            else:
                # Return an error if no movie details are found
                return make_response(jsonify({'error': 'No movies found'}), 400)
        except grpc.RpcError as e:
            # Handle gRPC errors and return the appropriate error response
            return make_response(jsonify({'error': e.details()}), e.code().value[0])

# Main entry point of the application
if __name__ == "__main__":
    print("Server running in port %s" % (PORT))  # Print message indicating server is running
    app.run(host=HOST, port=PORT, debug=True)  # Start Flask server with debugging enabled
