# MindsDB GO SDK

git:- https://github.com/Zedoman/MINDS_GO_SDK

This project implements a simple REST API for managing **Predictors** using Go and MongoDB Atlas. The API allows users to create and retrieve predictors from a MongoDB collection.

<img width="929" alt="Screenshot 2024-10-05 at 22 33 28" src="https://github.com/user-attachments/assets/c9e0f2f1-55ac-4675-8fcf-e86094ca540e">
<img width="706" alt="Screenshot 2024-10-05 at 22 33 17" src="https://github.com/user-attachments/assets/e50b84ad-3367-4eb1-8e80-fbdc01ab78e8">
<img width="554" alt="Screenshot 2024-10-05 at 22 33 02" src="https://github.com/user-attachments/assets/67dca533-7658-4f5a-bde0-1fd69642fbc0">


## Prerequisites

To run this project, ensure that you have the following tools installed on your machine:

- Go (version 1.16 or above)
- MongoDB Atlas account and cluster (or a MongoDB URI for connection)
- Git (to clone the repository)

## Features

- **Create a Predictor**: Add a new predictor to the MongoDB collection.
- **Retrieve Predictors**: Get a list of all predictors stored in the MongoDB collection.

## Endpoints

### 1. **Create a Predictor**

- **Endpoint**: `POST /predictors`
- **Description**: Add a new predictor to the MongoDB collection.
- **Request Body** (JSON format):
  ```json
  {
    "name": "Predictor Name"
  }
  ```
- **Response**:
  - `201 Created` on success with the newly created predictor in the response body.

- **Example cURL Command**:
  ```bash
  curl -X POST http://localhost:8080/predictors \
  -H "Content-Type: application/json" \
  -d '{"name": "Predictor 1"}'
  ```

### 2. **Retrieve Predictors**

- **Endpoint**: `GET /predictors`
- **Description**: Retrieve all predictors from the MongoDB collection.
- **Response** (JSON format):
  ```json
  [
    {
      "id": "some_id",
      "name": "Predictor 1"
    },
    {
      "id": "some_other_id",
      "name": "Predictor 2"
    }
  ]
  ```

- **Example cURL Command**:
  ```bash
  curl http://localhost:8080/predictors
  ```

## Project Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mindsdb-predictors-api.git
cd mindsdb-predictors-api
```

### 2. Install Dependencies

Run the following command to install the Go dependencies required for the project:

```bash
go mod tidy
```

### 3. Update MongoDB URI

In the `main.go` file, update the `uri` with your MongoDB Atlas connection string. For example:

```go
uri := "mongodb+srv://<username>:<password>@cluster0.kpxtb.mongodb.net/<dbname>?retryWrites=true&w=majority"
```

### 4. Run the Application

Start the server by running:

```bash
go run main.go
```

You should see a message like:

```
Server is running on port 8080
```

### 5. Testing the API

Use tools like **Postman**, **Insomnia**, or **cURL** to test the API.

- To **create a new predictor**, send a `POST` request to `http://localhost:8080/predictors`.
- To **retrieve the list of predictors**, send a `GET` request to `http://localhost:8080/predictors`.

## Code Overview

### `main.go`

The main Go file that defines the API and MongoDB client.

- **MindsDBClient**: Represents a MongoDB client connected to the specified collection.
- **Predictor**: A struct that defines the schema for predictors, containing an ID and a Name.
- **NewMindsDBClient**: Function to initialize and connect to MongoDB Atlas using a provided URI.
- **CreatePredictorHandler**: HTTP handler for adding a new predictor via `POST` request.
- **GetPredictorsHandler**: HTTP handler for retrieving predictors via `GET` request.

### Dependencies

- `go.mongodb.org/mongo-driver/mongo`: MongoDB driver for Go.
- `github.com/gorilla/mux`: A powerful router for handling HTTP requests.

## MongoDB Setup

1. Create a free MongoDB Atlas account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Create a new cluster and database.
3. Obtain your MongoDB connection string (URI) from the MongoDB Atlas dashboard.
4. Ensure that your cluster is properly configured with IP whitelisting and credentials.



## License

This project is licensed under the MIT License.
