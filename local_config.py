## RDFLib Graph configuration
graph_identifier = 'http://rdfstore/'
graph_store = "PostgreSQL"

## Multiprocessing cofinguration

max_branches = 10

## Postgresql configuration
db_configstring = "user=postgres,password=p0stgr3s,host=localhost,db=rdfstore"
db_identifier = "rdfstore"

## SQLAlchemy configuration
alchemy_configstring = "postgresql://postgres:p0stgr3s@localhost:5432/rdf2subdue"

## Input file(s) configuration

input_file = "morelab.rdf"
input_dir = None
input_format = "xml"

## Output file configuration

output_file = "morelab.g"
