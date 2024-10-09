import grpc
import booking_pb2
import booking_pb2_grpc

def run():
    # Establish a channel to the server
    with grpc.insecure_channel('[::]:3003') as channel:
        stub = booking_pb2_grpc.BookingStub(channel)  # Create a stub (client)
        
        # Create the request for addBookingByUserId
        booking_info = booking_pb2.MovieDateBooking(
            date="20151201",
            movies=["a8034f44-aee4-44cf-b32c-74cf452aaaae"]
        )
        
        add_booking_request = booking_pb2.AddBooking(
            userid="dwight_schrute",
            bookingInfo=booking_info
        )
        
        # Call the addBookingByUserId method
        response = stub.addBookingByUserId(add_booking_request)

        # Print the response
        print("Booking response:", response)

if __name__ == '__main__':
    run()
