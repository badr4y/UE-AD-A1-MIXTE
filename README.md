# UE-AD-A1-MIXTE
# Mixed API Project (GraphQL & gRPC)

This repository contains a fully implemented project that combines GraphQL and gRPC APIs. The project consists of several microservices, including **Movie**, **Booking**, **Times**, and **User**. Some services use GraphQL, others use gRPC, and the system functions as a mixed API architecture.

## Project Overview

This project implements:
- A **GraphQL** API for the **Movie** service.
- **gRPC** APIs for the **Booking** and **Times** services.
- The **User** service, which interacts with the other services using both GraphQL and gRPC.

The architecture demonstrates how to build a scalable system using multiple API types in a microservices environment.

## Service Breakdown

### 1. Movie Service (GraphQL)

The **Movie** service provides a GraphQL API. It is responsible for managing movie-related data and is queried using GraphQL from the **User** service.

- The service replaces the original REST API with GraphQL.
- It is accessed via POST requests at `/graphql`.

**Example GraphQL Query**:
```graphql
{
  movie(id: 1) {
    title
    director
    releaseDate
  }
}
```
### 2. Booking Service (gRPC)

The **Booking** service provides a gRPC API that manages booking information. It interacts with the **Times** service via gRPC for time slot data.

- Booking acts as both a gRPC client (for **Times** service) and a gRPC server (serving the **User** service).
- It handles booking-related logic and communicates with other services via remote procedure calls.

### 3. ShowTime Service (gRPC)

The **ShowTime** service also provides a gRPC API, handling time slot information for bookings.

- It serves time data required by the **Booking** service via gRPC.
- The service uses gRPC stubs for inter-service communication.
### 4. User Service (GraphQL + gRPC)

The **User** service is a REST API that interacts with the **Movie** service using GraphQL and with the **Booking** service using gRPC.

- The service sends GraphQL queries to the **Movie** service for movie-related data.
- It sends gRPC requests to the **Booking** service for managing bookings.

## Usage

To run the services, you will use `pymon`, a Python monitoring tool that helps to automatically restart the services whenever a change is made to the code.

### Steps to Run Services

1. **Install `pymon`** if it's not already installed:
   ```bash
   pip install pymon

2. pymon movie.py
3. pymon user.py
4.  pymon booking.py
5.  pymon showtime.py


