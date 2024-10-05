# Minds SDK

### Installation

To install the SDK, use pip:

```bash
pip install minds-sdk
```

### Getting Started

1. Initialize the Client

To get started, you'll need to initialize the Client with your API key. If you're using a different server, you can also specify a custom base URL.

```python
from minds.client import Client

# Default connection to MindsDB Cloud
client = Client("YOUR_API_KEY")

# Custom MindsDB Cloud server
base_url = 'https://custom_cloud.mdb.ai/'
client = Client("YOUR_API_KEY", base_url)
```

2. Creating a Data Source

You can connect to various databases, such as PostgreSQL, by configuring your data source. Use the DatabaseConfig to define the connection details for your data source.

```python

from minds.datasources import DatabaseConfig

postgres_config = DatabaseConfig(
    name='my_datasource',
    description='<DESCRIPTION-OF-YOUR-DATA>',
    engine='postgres',
    connection_data={
        'user': 'demo_user',
        'password': 'demo_password',
        'host': 'samples.mindsdb.com',
        'port': 5432,
        'database': 'demo',
        'schema': 'demo_data'
    },
    tables=['<TABLE-1>', '<TABLE-2>']
)
```

3. Creating a Mind

You can create a `mind` and associate it with a data source.

```python

# Create a mind with a data source
mind = client.minds.create(name='mind_name', datasources=[postgres_config])

# Alternatively, create a data source separately and add it to a mind later
datasource = client.datasources.create(postgres_config)
mind2 = client.minds.create(name='mind_name', datasources=[datasource])
```

You can also add a data source to an existing mind:

```python

# Create a mind without a data source
mind3 = client.minds.create(name='mind_name')

# Add a data source to the mind
mind3.add_datasource(postgres_config)  # Using the config
mind3.add_datasource(datasource)       # Using the data source object
```

### Managing Minds

You can create a mind or replace an existing one with the same name.

```python

mind = client.minds.create(name='mind_name', replace=True, datasources=[postgres_config])
```

To update a mind, specify the new name and data sources. The provided data sources will replace the existing ones.

```python

mind.update(
    name='mind_name',
    datasources=[postgres_config]
)
```

#### List Minds

You can list all the minds you’ve created.

```python

print(client.minds.list())
```

#### Get a Mind by Name

You can fetch details of a mind by its name.

```python

mind = client.minds.get('mind_name')
```

#### Remove a Mind

To delete a mind, use the following command:

```python

client.minds.drop('mind_name')
```

### Managing Data Sources

To view all data sources:

```python

print(client.datasources.list())
```

#### Get a Data Source by Name

You can fetch details of a specific data source by its name.

```python

datasource = client.datasources.get('my_datasource')
```

#### Remove a Data Source

To delete a data source, use the following command:

```python

client.datasources.drop('my_datasource')
```
>Note: The SDK currently does not support automatically removing a data source if it is no longer connected to any mind.





####Other SDK

Here is the formatted content for `README.md`:

```markdown
# MindsDB Golang SDK

This project demonstrates how to build a client for MindsDB using Go and MySQL. The client connects to MindsDB, creates a table (if not already created), inserts sample data, and queries the `predictors` table. The solution emphasizes robustness, clarity, and ease of use.

## Features
1. **Database Connection**: Connect to MindsDB using a Data Source Name (DSN) and the MySQL driver.
2. **Table Management**: Create a `predictors` table if it doesn't exist.
3. **Sample Data Insertion**: Insert sample records into the table.
4. **Querying Data**: Retrieve a limited number of records from the `predictors` table.
5. **Error Handling**: Comprehensive error handling for connection failures and SQL execution issues.

## Setup Instructions

### Pre-requisites
- **Go** (version 1.16+)
- **MySQL Driver for Go** (`github.com/go-sql-driver/mysql`)
- **MindsDB** running locally or accessible via a TCP/IP connection

### Install Dependencies
Run the following command to install the MySQL driver:

```bash
go get -u github.com/go-sql-driver/mysql
```

### MindsDB Setup
Ensure that MindsDB is up and running. If using Docker, start the MindsDB container:

```bash
docker run -p 47334:47334 -d mindsdb/mindsdb
```

Confirm that MindsDB is accessible:

```bash
mysql -h localhost -P 47334 -u root
```

### Project Structure
- **`main.go`**: Contains the core logic for interacting with MindsDB.

---

## Code Walkthrough

### Connecting to MindsDB
The `NewMindsDBClient` function establishes a connection with MindsDB using the MySQL driver. It also tests the connection with a 10-second timeout.

```go
func NewMindsDBClient(dsn string) (*MindsDBClient, error) {
    db, err := sql.Open("mysql", dsn)
    if err != nil {
        return nil, fmt.Errorf("failed to open database: %w", err)
    }

    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    if err := db.PingContext(ctx); err != nil {
        return nil, fmt.Errorf("failed to ping database: %w", err)
    }

    return &MindsDBClient{db: db}, nil
}
```

---

### Creating the Predictors Table
The `CreatePredictorsTable` function checks if the `predictors` table exists. If not, it creates the table with fields for `id`, `name`, and timestamps.

```go
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
```

---

### Inserting Sample Data
Once the table is created, the program inserts sample records into the `predictors` table.

```go
sampleData := []string{"Predictor 1", "Predictor 2", "Predictor 3"}
for _, name := range sampleData {
    _, err := client.db.Exec("INSERT INTO predictors (name) VALUES (?);", name)
    if err != nil {
        log.Fatalf("Error inserting sample data: %v", err)
    }
}
```

---

### Querying the Predictors
The `QueryPredictors` function retrieves a limited number of records from the `predictors` table.

```go
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
```

---

## Running the Project

### Build the Project
Compile the Go program using the following command:

```bash
go build -o mindsdb-client
```

### Run the Program
Execute the binary:

```bash
./mindsdb-client
```

### Expected Output
You should see output similar to:

```bash
Successfully connected to MindsDB!
Predictors:
Predictor 1
Predictor 2
Predictor 3
```

---

## Error Handling
The project uses structured error handling for various steps, including database connection, table creation, data insertion, and query execution. The program logs any errors and exits if a critical issue is encountered.

---

## Testing

1. **Connection Timeout**: The connection uses a 10-second timeout to ensure the program doesn't hang indefinitely if MindsDB is unreachable.
2. **SQL Query Validation**: The program checks for SQL execution errors and logs any issues encountered during data manipulation.
3. **End-to-End Query**: After inserting data into the `predictors` table, the query ensures that the data is correctly stored and retrieved.

---

## Next Steps

- **Enhancements**: Consider adding more advanced queries or predictive capabilities from MindsDB.
- **Scaling**: Implement retry logic and connection pooling to handle larger datasets or more complex queries.
- **Testing**: Add unit tests to cover the critical paths, including table creation and data querying.

This project offers a foundational understanding of how to interact with MindsDB using Go and sets the stage for building more advanced machine learning applications on top of MindsDB.
```

This should serve as the README for your project. It includes setup instructions, an explanation of the code, running instructions, and further improvement suggestions.
