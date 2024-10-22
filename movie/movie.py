from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, ObjectType, QueryType, MutationType
from flask import Flask, request, jsonify, make_response

import resolvers as r  # Import custom resolver functions from the 'resolvers' module

# Flask app configuration
PORT = 3001  # Define the port number on which the app will run
HOST = '0.0.0.0'  # Make the app accessible from any IP address
app = Flask(__name__)  # Create a new Flask web application instance

# --- Ariadne Schema and Resolvers Setup ---

# Load the GraphQL schema definition from a file (movie.graphql)
type_defs = load_schema_from_path('movie.graphql')

# Define the Query type and attach resolver for fetching a movie by ID
query = QueryType()  # Initialize a QueryType object for defining GraphQL queries
query.set_field('movie_with_id', r.movie_with_id)  # Assign the movie_with_id resolver function to the query

# Define the Movie type and attach resolvers for Movie-related fields
movie = ObjectType("Movie")  # Initialize ObjectType for the "Movie" type in the schema
movie.set_field('actors', r.resolve_actors_in_movie)  # Define a custom resolver for the "actors" field in Movie type

# Create the Mutation type and assign a resolver to update movie rating
mutation = MutationType()  # Initialize MutationType object for mutations
mutation.set_field('update_movie_rate', r.update_movie_rate)  # Attach the resolver for updating movie rating

# Create the Actor type and attach resolvers for Actor-related fields
actor = ObjectType('Actor')  # Initialize ObjectType for the "Actor" type in the schema

# Create the executable schema combining the type definitions and resolvers
schema = make_executable_schema(type_defs, movie, query, mutation, actor)

# --- Flask API Endpoints ---

# A root endpoint to check if the service is running
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Movie service!</h1>", 200)  # Send an HTML response

# GraphQL endpoint to handle incoming queries and mutations
@app.route('/graphql', methods=['POST'])
def graphql_server():
    data = request.get_json()  # Parse the incoming JSON request payload
    success, result = graphql_sync(
        schema,  # Use the Ariadne schema to process the query/mutation
        data,  # The GraphQL query or mutation data sent by the client
        context_value=None,  # Optionally pass context (e.g., authentication info) to the resolvers
        debug=app.debug  # Enable detailed error messages if Flask app is in debug mode
    )
    status_code = 200 if success else 400  # Return a 200 status code for successful queries, otherwise 400 for errors
    return jsonify(result), status_code  # Return the result as a JSON response

# Run the Flask app when the script is executed
if __name__ == "__main__":
    print("Server running in port %s" % (PORT))  # Print a message indicating the server's port
    app.run(host=HOST, port=PORT)  # Start the Flask server
