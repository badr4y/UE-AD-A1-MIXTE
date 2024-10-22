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
        # Log the incoming request for debugging
        print(f"Received request for user ID: {request.userid}")

        for booking in self.db:
            if booking['userid'] == request.userid:
                print("User found, returning booking data.")
                return booking_pb2.BookingUser(userid=booking['userid'], dates=[
                    booking_pb2.MovieDateBooking(
                        date=date['date'],
                        movies=date['movies']
                    ) for date in booking['dates']
                ])
        print("User not found, returning empty response.")
        
    def deleteBooking(self, request, context):
        userid = request.userid
        date = request.date
        moviesid = request.moviesid  # Get movie ID from request
        # Search for the user's booking
        user_booking = next((booking for booking in self.db if booking["userid"] == userid), None)

        if not user_booking:    
            return booking_pb2.DeleteBookingResponse(success=False, message="User booking not found")

        # Find the user's dates
        user_dates = user_booking["dates"]
        
        # Search for the date entry to delete
        for date_entry in user_dates:
            if date_entry["date"] == date:
                # Check if the movie ID exists in the movies for this date
                if moviesid in date_entry["movies"]:
                    # Remove the movie ID from the date entry
                    date_entry["movies"].remove(moviesid)

                    # If no movies are left for this date, remove the date entry
                    if not date_entry["movies"]:
                        user_dates.remove(date_entry)

                    # If no dates are left, remove the user booking entirely
                    if not user_dates:
                        self.db.remove(user_booking)

                    # Write the updated bookings to the JSON file
                    write_bookings(self.db)

                    return booking_pb2.DeleteBookingResponse(success=True, message="Booking deleted successfully")
                else:
                    return booking_pb2.DeleteBookingResponse(success=False, message="Movie ID not found for the specified date")

        return booking_pb2.DeleteBookingResponse(success=False, message="No booking found for the specified date")

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
