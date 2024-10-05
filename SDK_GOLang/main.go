package main

import (
    "database/sql"
    "context"
    "fmt"
    "log"
    "time"
    _ "github.com/go-sql-driver/mysql"
)

// MindsDBClient represents a client for MindsDB.
type MindsDBClient struct {
    db *sql.DB
}

// NewMindsDBClient initializes a new MindsDB client.
func NewMindsDBClient(dsn string) (*MindsDBClient, error) {
    db, err := sql.Open("mysql", dsn)
    if err != nil {
        return nil, fmt.Errorf("failed to open database: %w", err)
    }

    // Test the connection with a timeout
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    if err := db.PingContext(ctx); err != nil {
        return nil, fmt.Errorf("failed to ping database: %w", err)
    }

    return &MindsDBClient{db: db}, nil
}

// Close closes the database connection.
func (client *MindsDBClient) Close() error {
    return client.db.Close()
}

// QueryPredictors retrieves a limited number of predictors from the database.
func (client *MindsDBClient) QueryPredictors(limit int) ([]string, error) {
    query := fmt.Sprintf("SELECT name FROM mindsdb.predictors LIMIT %d;", limit)
    rows, err := client.db.Query(query)
    if err != nil {
        return nil, fmt.Errorf("error executing query: %w", err)
    }
    defer rows.Close()

    var predictors []string
    for rows.Next() {
        var name string
        if err := rows.Scan(&name); err != nil {
            return nil, fmt.Errorf("error scanning row: %w", err)
        }
        predictors = append(predictors, name)
    }

    return predictors, nil
}

// CreatePredictorsTable creates the predictors table if it doesn't exist.
func (client *MindsDBClient) CreatePredictorsTable() error {
    query := `
    CREATE TABLE IF NOT EXISTS predictors (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );`

    _, err := client.db.Exec(query)
    return err
}

func main() {
    // Set the Data Source Name (DSN)
    dsn := "root@tcp(localhost:47334)/mindsdb?timeout=10s"
    log.Println("Attempting to connect to MindsDB...")

    client, err := NewMindsDBClient(dsn)
    if err != nil {
        log.Fatalf("Error creating MindsDB client: %v", err)
    }
    defer client.Close()

    fmt.Println("Successfully connected to MindsDB!")

    // Create the predictors table if it doesn't exist
    if err := client.CreatePredictorsTable(); err != nil {
        log.Fatalf("Error creating predictors table: %v", err)
    }

    // Optional: Insert sample data into the predictors table
    sampleData := []string{"Predictor 1", "Predictor 2", "Predictor 3"}
    for _, name := range sampleData {
        _, err := client.db.Exec("INSERT INTO predictors (name) VALUES (?);", name)
        if err != nil {
            log.Fatalf("Error inserting sample data: %v", err)
        }
    }

    // Query data from MindsDB
    predictors, err := client.QueryPredictors(10)
    if err != nil {
        log.Fatalf("Error querying predictors: %v", err)
    }

    // Print the query results
    fmt.Println("Predictors:")
    for _, predictor := range predictors {
        fmt.Println(predictor)
    }
}
