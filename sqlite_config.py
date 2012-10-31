## RDFLib Graph configuration
graph_identifier = 'http://rdfstore/'
graph_store = "SQLite"

## Multiprocessing cofinguration

max_branches = 10

## Postgresql configuration
db_engine = 'MySQL'
db_configstring = "/tmp/bd.sqlite"
db_identifier = "rdfstore"
db_path = "/tmp/bd.sqlite"

## SQLAlchemy configuration
alchemy_configstring = "sqlite:///bd.sqlite"

## Input file(s) configuration

input_file = "morelab.rdf"
input_dir = None
input_format = "xml"

## Output file configuration

output_file = "morelab.g"
