# DashVector Client Python Library

DashVector is a scalable and fully-managed vector-database service for building various machine learning applications. The DashVector client SDK is your gateway to access the DashVector service.

For more information about DashVector, please visit: https://help.aliyun.com/document_detail/2510225.html

## Installation
To install the DashVector client Python SDK, simply run:
```shell
pip install dashvector
```

## QuickStart

```python
import numpy as np
import dashvector

# Use DashVector `Client` api to communicate with the backend vectorDB service.
client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')

# Create a collection named "quickstart" with dimension of 4, using the default Cosine distance metric
rsp = client.create(name='quickstart', dimension=4)
assert rsp

# Get a collection by name
collection = client.get(name='quickstart')

# Operations on 'Collection' includes Inert/Query/Upsert/Update/Delete/Fetch of docs
# Here we insert sample data (4-dimensional vectors) in batches of 16
collection.insert(
    [
        dashvector.Doc(id=str(i), vector=np.random.rand(4), fields={'anykey': 'anyvalue'}) 
        for i in range(16)
    ]
)

# Query a vector from the collection
docs = collection.query([0.1, 0.2, 0.3, 0.4], topk=5)
print(docs)

# Get statistics about collection
stats = collection.stats()
print(stats)

# Delete a collection by name
client.delete(name='quickstart')
```

## Reference

### Create a Client
`Client` host various APIs for interacting with DashVector `Collection`.

```python
dashvector.Client(
    api_key: str,
    endpoint: str = 'dashvector.cn-hangzhou.aliyuncs.com',
    protocal: dashvector.DashVectorProtocol = dashvector.DashVectorProtocol.GRPC, 
    timeout: float = 10.0
) -> Client
```

| Parameters | Type               | Required | Description                                                                                  |
|------------|--------------------|----------|----------------------------------------------------------------------------------------------|
| api_key    | str                | Yes      | Your DashVector API-KEY                                                                      |
| endpoint   | str                | No       | Service Endpoint. <br/>Default value: `dashvector.cn-hangzhou.aliyuncs.com`                  |
| protocol   | DashVectorProtocol | No       | Communication protocol, support HTTP and GRPC. <br/>Default value: `DashVectorProtocol.GRPC` |
| timeout    | float              | No       | Timeout period (in seconds), -1 means no timeout. <br/>Default value: `10.0`                 |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
assert client
```

### Create Collection
```python
Client.create(
    name: str,
    dimension: int,
    dtype: Union[Type[int], Type[float]] = float,
    fields_schema: Optional[Dict[str, Union[Type[str], Type[int], Type[float], Type[bool]]]] = None,
    metric: str = 'cosine',
    timeout: Optional[int] = None
) -> DashVectorResponse
```

| Parameters     | Type                                                                       | Required | Description                                                                                                      |
|----------------|----------------------------------------------------------------------------|----------|------------------------------------------------------------------------------------------------------------------|
| name           | str                                                                        | Yes      | The name of the Collection to create.                                                                            |
| dimension      | int                                                                        | Yes      | The dimensions of the Collection's vectors. Valid values:  1-20,000                                              |
| dtype          | Union[Type[int], Type[float]]                                              | No       | The date type of the Collection's vectors.<br/>Default value: `Type[float]`                                      |
| fields_schema  | Optional[Dict[str, Union[Type[str], Type[int], Type[float], Type[bool]]]]  | No       | Fields schema of the Collection.<br/>Default value: `None`<br/>e.g. `{"name": str, "age": int}`                  |
| metric         | str                                                                        | No       | Vector similarity metric. For `cosine`, dtype must be `float`.<br/>Valid values:<br/> 1. (Default)`cosine`<br/>2. `dotproduct`<br/>3. `euclidean`    |
| timeout        | Optional[int]                                                              | No       | Timeout period (in seconds), -1 means asynchronous creation collection.<br/>Default value: `None`                |


Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')

rsp = client.create('YOUR-COLLECTION-NAME', dimension=4)
assert rsp
```

### List Collections
`Client.list() -> DashVectorResponse`

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')

collections = client.list()

for collection in collections:
    print(collection)
# outputs:
# 'quickstart'
```

### Describe Collection
`Client.describe(name: str) -> DashVectorResponse`

| Parameters | Type  | Required | Description                             |
|------------|-------|----------|-----------------------------------------|
| name       | str   | Yes      | The name of the Collection to describe. |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
rsp = client.describe('YOUR-COLLECTION-NAME')

print(rsp)
# example output:
# {
#   "request_id": "8d3ac14e-5382-4736-b77c-4318761ddfab",
#   "code": 0,
#   "message": "",
#   "output": {
#     "name": "quickstart",
#     "dimension": 4,
#     "dtype": "FLOAT",
#     "metric": "dotproduct",
#     "fields_schema": {
#       "name": "STRING",
#       "age": "INT",
#       "height": "FLOAT"
#     },
#     "status": "SERVING",
#     "partitions": {
#       "default": "SERVING"
#     }
#   }
# }
```

### Delete Collection
`Client.delete(name: str) -> DashVectorResponse`

| Parameters | Type  | Required | Description                           |
|------------|-------|----------|---------------------------------------|
| name       | str   | Yes      | The name of the Collection to delete. |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
client.delete('YOUR-COLLECTION-NAME')
```

### Get a Collection Instance
`Collection` provides APIs for accessing `Doc` and `Partition`

`Client.get(name: str) -> Collection`

| Parameters | Type  | Required | Description                        |
|------------|-------|----------|------------------------------------|
| name       | str   | Yes      | The name of the Collection to get. |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')
assert collection
```

### Describe Collection Statistics
`Collection.stats() -> DashVectorResponse`

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')
rsp = collection.stats()

print(rsp)
# example output:
# {
#   "request_id": "14448bcb-c9a3-49a8-9152-0de3990bce59",
#   "code": 0,
#   "message": "Success",
#   "output": {
#     "total_doc_count": "26",
#     "index_completeness": 1.0,
#     "partitions": {
#       "default": {
#         "total_doc_count": "26"
#       }
#     }
#   }
# }
```

### Insert/Update/Upsert Docs
```python
Collection.insert(
    docs: Union[Doc, List[Doc], Tuple, List[Tuple]],
    partition: Optional[str] = None,
    async_req: False
) -> DashVectorResponse
```

| Parameters | Type                                      | Required | Description                                                            |
|------------|-------------------------------------------|----------|------------------------------------------------------------------------|
| docs       | Union[Doc, List[Doc], Tuple, List[Tuple]] | Yes      | The docs to Insert/Update/Upsert.                                      |
| partition  | Optional[str]                             | No       | Name of the partition to Insert/Update/Upsert.<br/>Default value: `None` |
| async_req  | bool                                      | No       | Enable async request or not.<br/>Default value: `False`                  |

Example:
```python
import dashvector
import numpy as np

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')

# insert a doc with Tuple
collection.insert(('YOUR-DOC-ID1', [0.1, 0.2, 0.3, 0.4]))
collection.insert(('YOUR-DOC-ID2', [0.2, 0.3, 0.4, 0.5], {'age': 30, 'name': 'alice', 'anykey': 'anyvalue'}))

# insert a doc with dashvector.Doc
collection.insert(
    dashvector.Doc(
        id='YOUR-DOC-ID3', 
        vector=[0.3, 0.4, 0.5, 0.6], 
        fields={'foo': 'bar'}
    )
)

# insert in batches
ret = collection.insert(
    [
        ('YOUR-DOC-ID4', [0.2, 0.7, 0.8, 1.3], {'age': 1}),
        ('YOUR-DOC-ID4', [0.3, 0.6, 0.9, 1.2], {'age': 2}),
        ('YOUR-DOC-ID6', [0.4, 0.5, 1.0, 1.1], {'age': 3})
    ]
)

# insert in batches
ret = collection.insert(
    [
        dashvector.Doc(id=str(i), vector=np.random.rand(4)) for i in range(10)
    ]
)

# async insert
ret_funture = collection.insert(
    [
        dashvector.Doc(id=str(i+10), vector=np.random.rand(4)) for i in range(10)
    ],
    async_req=True
)
ret = ret_funture.get()
```

### Query a Collection
```python
Collection.query(
    vector: Optional[Union[List[Union[int, float]], np.ndarray]] = None,
    id: Optional[str] = None,
    topk: int = 10,
    filter: Optional[str] = None,
    include_vector: bool = False,
    partition: Optional[str] = None,
    output_fields: Optional[List[str]] = None,
    async_req: False
) -> DashVectorResponse
```

| Parameters      | Type                                                 | Required | Description                                                                                                  |
|-----------------|------------------------------------------------------|----------|--------------------------------------------------------------------------------------------------------------|
| vector          | Optional[Union[List[Union[int, float]], np.ndarray]] | No       | The vector to query                                                                                          |
| id              | Optional[str]                                        | No       | The doc id to query.<br/>Setting `id` means searching by vector corresponding to the id                      |
| topk            | Optional[str]                                        | No       | Number of similarity results to return.<br/>Default value: `10`                                              |
| filter          | Optional[str]                                        | No       | Expression used to filter results <br/>Default value: None <br/>e.g. `age>20`                                |
| include_vector  | bool                                                 | No       | Return vector details or not.<br/>Default value: `False`                                                     |
| partition       | Optional[str]                                        | No       | Name of the partition to Query.<br/>Default value: `None`                                                    |
| output_fields   | Optional[List[str]]                                  | No       | List of field names to return.<br/>Default value: `None`, means return all fields<br/>e.g. `['name', 'age']` |
| async_req       | bool                                                 | No       | Enable async request or not.<br/>Default value: `False`                                                      |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')
match_docs = collection.query([0.1, 0.2, 0.3, 0.4], topk=100, filter='age>20', include_vector=True, output_fields=['age','name','foo'])
if match_docs:
    for doc in match_docs:
        print(doc.id)
        print(doc.vector)
        print(doc.fields)
        print(doc.score)
```

### Delete Docs
```python
collection.delete(
    ids: Union[str, List[str]],
    delete_all: bool = False,
    partition: Optional[str] = None,
    async_req: bool = False
) -> DashVectorResponse
```

| Parameters | Type                  | Required | Description                                                     |
|------------|-----------------------|----------|-----------------------------------------------------------------|
| ids        | Union[str, List[str]] | Yes      | The id (or list of ids) for the Doc(s) to Delete                |
| delete_all | bool                  | No       | Delete all vectors from partition.<br/>Default value: `False`    |
| partition  | Optional[str]         | No       | Name of the partition to Delete from.<br/>Default value: `None` |
| async_req  | bool                  | No       | Enable async request or not.<br/>Default value: `False`         |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')
collection.delete(['YOUR-DOC-ID1','YOUR-DOC-ID2'])
```

### Fetch Docs
```python
Collection.fetch(
    ids: Union[str, List[str]],
    partition: Optional[str] = None,
    async_req: bool = False
) -> DashVectorResponse
```

| Parameters | Type                  | Required | Description                                                    |
|------------|-----------------------|----------|----------------------------------------------------------------|
| ids        | Union[str, List[str]] | Yes      | The id (or list of ids) for the Doc(s) to Fetch                |
| partition  | Optional[str]         | No       | Name of the partition to Fetch from.<br/>Default value: `None` |
| async_req  | bool                  | No       | Enable async request or not.<br/>Default value: `False`        |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')
fetch_docs = collection.fetch(['YOUR-DOC-ID1', 'YOUR-DOC-ID2'])
if fetch_docs:
    for doc_id in fetch_docs:
        doc = fetch_docs[doc_id]
        print(doc.id)
        print(doc.vector)
        print(doc.fields)
```

### Create Collection Partition
`Collection.create_partition(name: str) -> DashVectorResponse`

| Parameters | Type           | Required | Description                                                                                           |
|------------|----------------|----------|-------------------------------------------------------------------------------------------------------|
| name       | str            | Yes      | The name of the Partition to Create.                                                                  |
| timeout    | Optional[int]  | No       | Timeout period (in seconds), -1 means asynchronous creation partition.<br/>Default value: `None`      |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')
rsp = collection.create_partition('YOUR-PARTITION-NAME')
assert rsp
```

### Delete Collection Partition
`Collection.delete_partition(name: str) -> DashVectorResponse`

| Parameters | Type  | Required | Description                          |
|------------|-------|----------|--------------------------------------|
| name       | str   | Yes      | The name of the Partition to Delete. |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')
rsp = collection.delete_partition('YOUR-PARTITION-NAME')
assert rsp
```

### List Collection Partitions
`Collection.list_partitions() -> DashVectorResponse`

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')
partitions = collection.list_partitions()

assert partitions
for pt in partitions:
    print(pt)
```

### Describe Collection Partition
`Collection.describe_partition(name: str) -> DashVectorResponse`

| Parameters | Type  | Required | Description                            |
|------------|-------|----------|----------------------------------------|
| name       | str   | Yes      | The name of the Partition to Describe. |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')

rsp = collection.describe_partition('shoes')
print(rsp)
# example output:
# {"request_id":"296267a7-68e2-483a-87e6-5992d85a5806","code":0,"message":"","output":"SERVING"}
```

### Statistics for Collection Partition
`Collection.stats_partition(name: str) -> DashVectorResponse`

| Parameters | Type  | Required | Description                                  |
|------------|-------|----------|----------------------------------------------|
| name       | str   | Yes      | The name of the Partition to get Statistics. |

Example:
```python
import dashvector

client = dashvector.Client(api_key='YOUR-DASHVECTOR-API-KEY')
collection = client.get('YOUR-COLLECTION-NAME')

rsp = collection.stats_partition('shoes')
print(rsp)
# example outptut:
# {
#     "code":0,
#     "message":"",
#     "requests_id":"330a2bcb-e4a7-4fc6-a711-2fe5f8a24e8c",
#     "output":{
#         "total_doc_count":0
#     }
# }
```


## Class
### dashvector.Doc
```python
@dataclass(frozen=True)
class Doc(object):
    id: str
    vector: Union[List[int], List[float], numpy.ndarray]
    fields: Optional[Dict[str, Union[Type[str], Type[int], Type[float], Type[bool]]]] = None 
    score: float = 0.0
```

### dashvector.DashVectorResponse

```python
class DashVectorResponse(object):
    code: DashVectorCode
    message: str
    request_id: str
    output: Any
```

## License
This project is licensed under the Apache License (Version 2.0).