# DDSTAV

**DDSTAV** (Document Data Structure Analyzer & Visualizer) is a Python package for analyzing and visualizing the structure of document-based databases.

It helps you quickly understand:
- the shape of documents
- data types across collections
- count of separate data structures in collections

## 🚀 Usage

The main entry point of the package is the `ddstav` function.

### Function parameters

- **`uri`** (`str`)  
  MongoDB connection string specifying the deployment to connect to.

- **`database_name`** (`str`)  
  Name of the MongoDB database to be analyzed.

### Example

```python
from DDSTAV import ddstav

ddstav("mongodb://localhost:27017/", "test_database")
```






