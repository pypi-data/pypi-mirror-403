# SciBite Toolkit

Python library for making API calls to [SciBite](https://www.scibite.com/)'s suite of products and processing the JSON responses.

## Supported Products

- **TERMite** - Entity recognition and semantic enrichment (version 6.x)
- **TERMite 7** - Next-generation entity recognition with modern OAuth2 authentication
- **TExpress** - Pattern-based entity relationship extraction
- **CENtree** - Ontology management, navigation, and integration
- **SciBite Search** - Semantic search, document and entity analytics 
- **Workbench** - Dataset annotation and management

## Installation

```bash
pip install scibite-toolkit
```

See versions on [PyPI](https://pypi.org/project/scibite-toolkit/)

## Quick Start Examples

- [TERMite 7](#termite-7-examples) - Modern client with OAuth2
- [TERMite 6](#termite-6-examples) - Legacy client
- [TExpress](#texpress-examples) - Pattern matching
- [SciBite Search](#scibite-search-example)
- [CENtree](#centree-examples) - Ontology navigation
- [Workbench](#workbench-example)

---

## TERMite 7 Examples

TERMite 7 is the modern version with enhanced OAuth2 authentication and improved API.

### OAuth2 Client Credentials (SaaS - Recommended)

For modern SaaS deployments using a separate authentication server:

```python
from scibite_toolkit import termite7

# Initialize with context manager for automatic cleanup
with termite7.Termite7RequestBuilder() as t:
    # Set URLs
    t.set_url('https://termite.saas.scibite.com')
    t.set_token_url('https://auth.saas.scibite.com')

    # Authenticate with OAuth2 client credentials
    if not t.set_oauth2('your_client_id', 'your_client_secret'):
        print("Authentication failed!")
        exit(1)

    # Annotate text
    t.set_entities('DRUG,INDICATION')
    t.set_subsume(True)
    t.set_text('Aspirin is used to treat headaches and reduce inflammation.')

    response = t.annotate_text()

    # Process the response
    df = termite7.process_annotation_output(response)
    print(df.head())
```

### OAuth2 Password Grant (Legacy)

For on-premise deployments using username/password authentication:

```python
from scibite_toolkit import termite7

t = termite7.Termite7RequestBuilder()

# Set main TERMite URL and token URL (same server for legacy)
t.set_url('https://termite.example.com')
t.set_token_url('https://termite.example.com')

# Authenticate with username and password
if not t.set_oauth2_legacy('client_id', 'username', 'password'):
    print("Authentication failed!")
    exit(1)

# Annotate a document
t.set_entities('INDICATION,DRUG')
t.set_parser_id('generic')
t.set_file('path/to/document.pdf')

response = t.annotate_document()

# Process the response
df = termite7.process_annotation_output(response)
print(df)

# Clean up file handles
t.close()
```

### Get System Status

```python
from scibite_toolkit import termite7

t = termite7.Termite7RequestBuilder()
t.set_url('https://termite.example.com')
t.set_token_url('https://auth.example.com')
t.set_oauth2('client_id', 'client_secret')

# Get system status
status = termite7.get_system_status(t.url, t.headers)
print(f"Server Version: {status['data']['serverVersion']}")

# Get available vocabularies
vocabs = termite7.get_vocabs(t.url, t.headers)
print(f"Available vocabularies: {len(vocabs['data'])}")

# Get runtime options
rtos = termite7.get_runtime_options(t.url, t.headers)
print(rtos)
```

---

## TERMite 6 Examples

For legacy TERMite 6.x deployments.

### SciBite Hosted (SaaS)

```python
from scibite_toolkit import termite

# Initialize
t = termite.TermiteRequestBuilder()

# Configure
t.set_url('https://termite.saas.scibite.com')
t.set_saas_login_url('https://login.saas.scibite.com')

# Authenticate
t.set_auth_saas('username', 'password')

# Set runtime options
t.set_entities('INDICATION')
t.set_input_format('medline.xml')
t.set_output_format('json')
t.set_binary_content('path/to/file.xml')
t.set_subsume(True)

# Execute and process
response = t.execute()
df = termite.get_termite_dataframe(response)
print(df.head(3))
```

### Local Instance (Customer Hosted)

```python
from scibite_toolkit import termite

t = termite.TermiteRequestBuilder()
t.set_url('https://termite.local.example.com')

# Basic authentication for local instances
t.set_basic_auth('username', 'password')

# Configure and execute
t.set_entities('INDICATION')
t.set_input_format('medline.xml')
t.set_output_format('json')
t.set_binary_content('path/to/file.xml')
t.set_subsume(True)

response = t.execute()
df = termite.get_termite_dataframe(response)
print(df.head(3))
```

---

## TExpress Examples

Pattern-based entity relationship extraction.

### SciBite Hosted

```python
from scibite_toolkit import texpress

t = texpress.TexpressRequestBuilder()

t.set_url('https://texpress.saas.scibite.com')
t.set_saas_login_url('https://login.saas.scibite.com')
t.set_auth_saas('username', 'password')

# Set pattern to find relationships
t.set_entities('INDICATION,DRUG')
t.set_pattern(':(DRUG):{0,5}:(INDICATION)')  # Find DRUG within 5 words of INDICATION
t.set_input_format('medline.xml')
t.set_output_format('json')
t.set_binary_content('path/to/file.xml')

response = t.execute()
df = texpress.get_texpress_dataframe(response)
print(df.head())
```

### Local Instance

```python
from scibite_toolkit import texpress

t = texpress.TexpressRequestBuilder()
t.set_url('https://texpress.local.example.com')
t.set_basic_auth('username', 'password')

t.set_entities('INDICATION,DRUG')
t.set_pattern(':(INDICATION):{0,5}:(INDICATION)')
t.set_input_format('pdf')
t.set_output_format('json')
t.set_binary_content('/path/to/file.pdf')

response = t.execute()
df = texpress.get_texpress_dataframe(response)
print(df.head())
```

---

## SciBite Search Example

Semantic search with entity-based queries and aggregations.

```python
from scibite_toolkit import scibite_search

# Configure
s = scibite_search.SBSRequestBuilder()
s.set_url('https://yourdomain-search.saas.scibite.com/')
s.set_auth_url('https://yourdomain.saas.scibite.com/')

# Authenticate with OAuth2
s.set_oauth2('your_client_id', 'your_client_secret')

# Search documents
query = 'schema_id="clinical_trial" AND (title~INDICATION$D011565 AND DRUG$*)'
# Preferred: request specific fields using the new 'fields' parameter (legacy: 'additional_fields')
response = s.get_docs(query=query, markup=True, limit=100, fields=['*'])

# Get co-occurrence aggregations
# Find top 50 genes co-occurring with psoriasis
response = s.get_aggregates(
    query='INDICATION$D011565',
    vocabs=['HGNCGENE'],
    limit=50
)
```

> **Note:** Preferred parameter name is `fields`. The legacy `additional_fields` is still supported for backward compatibility. When both are provided, `fields` takes precedence.

---

## CENtree Examples

Ontology navigation and search.

### Modern Client (Recommended)

The modern `centree_clients` module provides better error handling, retries, and context manager support.

```python
from scibite_toolkit.centree_clients import CENtreeReaderClient

# Use context manager for automatic cleanup
with CENtreeReaderClient(
    base_url="https://centree.example.com",
    bearer_token="your_token",
    timeout=(3.0, None)  # Quick connect, unlimited read
) as reader:

    # Search by exact label
    hits = reader.get_classes_by_exact_label("efo", "neuron")
    print(f"Found {len(hits)} matches")

    # Get ontology roots
    roots = reader.get_root_entities("efo", "classes", size=10)

    # Get paths from root to target (great for LLM grounding)
    paths = reader.get_paths_from_root("efo", "MONDO_0007739", as_="labels")
    for path in paths:
        print(" → ".join(path))

# Or authenticate with OAuth2
from scibite_toolkit.centree_clients import CENtreeReaderClient

reader = CENtreeReaderClient(base_url="https://centree.example.com")
if reader.set_oauth2(client_id="...", client_secret="..."):
    hits = reader.get_classes_by_exact_label("efo", "lung")
    print(hits)
```

---

## Workbench Example

Dataset management and annotation.

```python
from scibite_toolkit import workbench

# Initialize
wb = workbench.WorkbenchRequestBuilder()
wb.set_url('https://workbench.example.com')

# Authenticate
wb.set_oauth2('client_id', 'username', 'password')

# Create dataset
wb.set_dataset_name('My Analysis Dataset')
wb.set_dataset_desc('Dataset for clinical trial analysis')
wb.create_dataset()

# Upload file
wb.set_file_input('path/to/data.xlsx')
wb.upload_file_to_dataset()

# Configure and run annotation
vocabs = [[5, 6], [8, 9]]  # Vocabulary IDs
attrs = [200, 201]  # Attribute IDs
wb.set_termite_config('', vocabs, attrs)
wb.auto_annotate_dataset()
```

---

## Key Features

### Context Manager Support (TERMite 7, CENtree Clients)

Modern clients support context managers for automatic resource cleanup:

```python
with termite7.Termite7RequestBuilder() as t:
    t.set_url('...')
    # ... work with client ...
# File handles automatically closed
```

### Error Handling

All OAuth2 methods return boolean status for easy error handling:

```python
if not t.set_oauth2(client_id, client_secret):
    print("Authentication failed - check credentials")
    exit(1)
```

### Logging

Enable detailed logging for debugging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Or set per-client
t = termite7.Termite7RequestBuilder(log_level='DEBUG')
```

### Session Management

All clients use `requests.Session()` for efficient connection pooling and automatic retry handling.

---



## License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
