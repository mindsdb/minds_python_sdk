package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "time"

    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"
    "go.mongodb.org/mongo-driver/bson"
    "github.com/gorilla/mux"
)

// MindsDBClient represents a client for MongoDB.
type MindsDBClient struct {
    collection *mongo.Collection
}

// Predictor represents the structure for predictor.
type Predictor struct {
    ID   string `json:"id" bson:"_id,omitempty"`
    Name string `json:"name" bson:"name"`
}

// NewMindsDBClient initializes a new MongoDB client for MindsDB using MongoDB Atlas.
func NewMindsDBClient(uri string, dbName string, collectionName string) (*MindsDBClient, error) {
    clientOptions := options.Client().ApplyURI(uri)
    client, err := mongo.NewClient(clientOptions)
    if err != nil {
        return nil, fmt.Errorf("failed to create MongoDB client: %v", err)
    }

    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    err = client.Connect(ctx)
    if err != nil {
        return nil, fmt.Errorf("failed to connect to MongoDB: %v", err)
    }

    collection := client.Database(dbName).Collection(collectionName)

    return &MindsDBClient{collection: collection}, nil
}

// CreatePredictor creates a new predictor in the MongoDB collection.
func (client *MindsDBClient) CreatePredictor(predictor Predictor) error {
    _, err := client.collection.InsertOne(context.TODO(), predictor)
    return err
}

// GetPredictors retrieves all predictors from the collection.
func (client *MindsDBClient) GetPredictors() ([]Predictor, error) {
    var predictors []Predictor
    cursor, err := client.collection.Find(context.TODO(), bson.M{})
    if err != nil {
        return nil, err
    }
    defer cursor.Close(context.TODO())

    for cursor.Next(context.TODO()) {
        var predictor Predictor
        err := cursor.Decode(&predictor)
        if err != nil {
            return nil, err
        }
        predictors = append(predictors, predictor)
    }
    return predictors, nil
}

// CreatePredictorHandler handles the creation of a predictor via POST request.
func CreatePredictorHandler(client *MindsDBClient, w http.ResponseWriter, r *http.Request) {
    var predictor Predictor
    err := json.NewDecoder(r.Body).Decode(&predictor)
    if err != nil {
        http.Error(w, "Invalid input", http.StatusBadRequest)
        return
    }

    err = client.CreatePredictor(predictor)
    if err != nil {
        http.Error(w, "Failed to create predictor", http.StatusInternalServerError)
        return
    }

    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(predictor)
}

// GetPredictorsHandler handles retrieving the list of predictors via GET request.
func GetPredictorsHandler(client *MindsDBClient, w http.ResponseWriter, r *http.Request) {
    predictors, err := client.GetPredictors()
    if err != nil {
        http.Error(w, "Failed to retrieve predictors", http.StatusInternalServerError)
        return
    }

    json.NewEncoder(w).Encode(predictors)
}

func main() {
    // MongoDB Atlas connection string
    uri := "mongodb+srv://<username>:<password>@cluster0.kpxtb.mongodb.net/<dbname>?retryWrites=true&w=majority"

    // Replace with your own credentials and database name
    dbName := "mindsdb"
    collectionName := "predictors"

    client, err := NewMindsDBClient(uri, dbName, collectionName)
    if err != nil {
        log.Fatalf("Failed to connect to MongoDB: %v", err)
    }

    // Set up router
    r := mux.NewRouter()
    r.HandleFunc("/predictors", func(w http.ResponseWriter, r *http.Request) {
        GetPredictorsHandler(client, w, r)
    }).Methods("GET")
    r.HandleFunc("/predictors", func(w http.ResponseWriter, r *http.Request) {
        CreatePredictorHandler(client, w, r)
    }).Methods("POST")

    log.Println("Server is running on port 8080")
    log.Fatal(http.ListenAndServe(":8080", r))
}
