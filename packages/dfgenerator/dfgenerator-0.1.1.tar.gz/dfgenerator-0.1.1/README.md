# dfgenerator

Lightweight helpers to build deterministic test datasets for Pandas and PySpark, with Faker-powered generators, YAML-based reusable configs, and JSON Schema support.

## Features

- 🎲 **Deterministic data generation** with seed support for reproducible tests
- 📊 **Multiple input formats**: YAML configs, JSON Schema, Spark/Iceberg DataFrames, or programmatic Python API
- 🌍 **Multi-locale support** with Faker integration (50+ locales)
- 🔗 **Relational data** with primary/foreign key support for joinable datasets
- 📤 **Multiple export formats**: CSV, JSON, Pandas DataFrame, PySpark DataFrame
- 🎯 **Smart inference** from JSON Schema formats, property names, and existing Spark DataFrames
- ⚡ **Spark/Iceberg support** - Generate test data from production schemas
- 🚀 **CLI and Python API** for flexible usage

## Quick Start

### From Spark/Iceberg DataFrame

```python
from pyspark.sql import SparkSession
from dfgenerator import build_from_spark

# Load production Iceberg table
spark = SparkSession.builder.getOrCreate()
prod_df = spark.read.format("iceberg").load("prod.users")

# Generate test data with same schema
test_data = build_from_spark(prod_df, rows=100, seed=42)

# Export for testing
test_data.to_file("test_users.csv")
test_df = test_data.to_spark(spark)
```

### From JSON Schema

```bash
# Generate data from a JSON Schema file
dfgenerator --schema user.schema.json --rows 100 --seed 42 --output users.csv
```

```python
from dfgenerator import build_from_jsonschema

schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer", "minimum": 18, "maximum": 65}
    }
}

dataset = build_from_jsonschema(schema, rows=100, seed=42)
dataset.to_file("users.csv")
```

### From YAML Config

```bash
dfgenerator --config people.yaml --rows 50 --output people.json
```

### Programmatic API

```python
from dfgenerator import DataFrameBuilder, RowTemplate, ColumnSpec, sequence, choices

template = RowTemplate([
    ColumnSpec("id", sequence(1)),
    ColumnSpec("city", choices(["Paris", "Berlin", "Boston"])),
])

dataset = DataFrameBuilder().from_template(template, 10).build()
df = dataset.to_pandas()
```

## Architecture

dfgenerator uses a **lightweight adapter pattern** for extensibility:

- **Core Domain**: Pure business logic for data generation
- **Input Adapters**: YAML, JSON Schema, Spark DataFrames (easily extensible!)
- **Output Adapters**: CSV, JSON, Pandas, PySpark

Want to add support for Protobuf, Avro, or GraphQL schemas? Just create a new adapter!

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Documentation

- [User Guide](docs/index.md) - Complete documentation and examples
- [Architecture](docs/ARCHITECTURE.md) - Design patterns and extensibility guide

