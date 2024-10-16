import grpc
from concurrent import futures

import booking_pb2
import booking_pb2_grpc
import showtime_pb2
import showtime_pb2_grpc
import json
from flask import jsonify
class BookingServicer(booking_pb2_grpc.BookingServicer):

    def __init__(self):
        with open('{}/data/bookings.json'.format("."), "r") as jsf:
            self.db = json.load(jsf)["bookings"]


    def getBookingByUserId(self, request, context):
        for booking in self.db:
            if booking['userid'] == request.userid:
                print("user Found!")
                # Return the showtime data if the date matches
                return booking_pb2.BookingUser(userid= booking['userid'], dates=booking['dates'])     
        return booking_pb2.BookingUser(userid='', dates=[])
    
    def addBookingByUserId(self, request, context):
        userid = request.userid
        bookingInfo = request.bookingInfo
        # Check for None or empty BookingInfo
        if not bookingInfo:
            print("BookingInfo is None or empty, returning empty BookingUser")

            return booking_pb2.BookingUser()  # Return an empty BookingUser message

        # Check for empty movies list
        if not bookingInfo.date:
            print("Movies list is empty, returning empty BookingUser")
            return booking_pb2.BookingUser()  # Return an empty BookingUser message

        movieid = bookingInfo.movies[0]  # Safe to access the first element now
        date = bookingInfo.date  

        
        # Debug logging
        print(f"Received request for userid: {userid}, date: {date}, movieid: {movieid}")
        
        if not userid or not bookingInfo:
            print("Invalid input, returning empty BookingUser")
            return booking_pb2.BookingUser()  # Return an empty BookingUser message
        
        with grpc.insecure_channel('localhost:3002') as channel:
            stub = showtime_pb2_grpc.ShowtimeStub(channel)
            print("Fetching showtimes data")
            
            movieDateTest = showtime_pb2.MovieDate(date=date)
            showtime_response = stub.getMoviesByDate(movieDateTest)  # Call the stub method
            
        # Log the showtime response
        print(f"Showtime response: {showtime_response}")

        # Validate the response
        if showtime_response.date == '':
            print("Showtime response has no date, returning empty BookingUser")
            return booking_pb2.BookingUser()  # Return an empty BookingUser message

        available_movies = showtime_response.movies  # Assuming the response has a 'movies' field
        print(f"Available movies: {available_movies}")

        if movieid not in available_movies:
            print(f"Movie ID {movieid} not in available movies, returning empty BookingUser")
            return booking_pb2.BookingUser()  # Return an empty BookingUser message

        # Check if the booking already exists
        for booking in self.db:
            if (booking["userid"] == userid and 
                    any(d['date'] == date and movieid in d.get('movies', []) for d in booking["dates"])):
                print("Booking already exists, returning empty BookingUser")
                return booking_pb2.BookingUser()  # Return an empty BookingUser message

        # Create or update the booking
        user_booking = next((booking for booking in self.db if booking["userid"] == userid), None)
        if user_booking:
            print(f"Updating booking for user {userid}")
            # Add the new movie to the existing date or create a new date entry
            user_dates = user_booking["dates"]
            existing_date = next((d for d in user_dates if d["date"] == date), None)
            if existing_date:
                existing_date["movies"].append(movieid)
            else:
                user_dates.append({"date": date, "movies": [movieid]})
        else:
            print(f"Creating new booking for user {userid}")
            user_booking = {
                "userid": userid,
                "dates": [
                    {
                        "date": date,
                        "movies": [movieid]
                    }
                ]
            }
            self.db.append(user_booking)

        # Write the updated bookings to the JSON file
        write_bookings(self.db)

        # Return the updated BookingUser
        return booking_pb2.BookingUser(userid=userid, dates=user_booking["dates"])

def get_movies_by_date(stub,date):
    movie = stub.getMoviesByDate(date)
    print(movie)

def write_bookings(bookings):
    with open('./data/bookings.json', 'w') as f:        
        json.dump({"bookings": bookings}, f)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=30))
    booking_pb2_grpc.add_BookingServicer_to_server(BookingServicer(), server)
    server.add_insecure_port('[::]:3003')
    
        
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
