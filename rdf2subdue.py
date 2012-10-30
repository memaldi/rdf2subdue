from rdflib import ConjunctiveGraph
from optparse import OptionParser
from django.core.validators import URLValidator
from rdflib import plugin
from rdflib import store
from time import strftime, localtime
from multiprocessing import Pool
from itertools import repeat
from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String
import os
import sys
import traceback

PREFIXES = {'http://rdfs.org/sioc/ns': 'sioc:', 'http://xmlns.com/foaf/0.1/': 'foaf:', 'http://www.daml.org/2001/10/html/airport-ont': 'daml:', 'http://swrc.ontoware.org/ontology': 'swrc:', 'http://purl.org/ontology/bibo/': 'bibo:', 'http://www.w3.org/2000/01/rdf-schema': 'rdf:', 'http://purl.org/dc/terms/': 'dcterms:', 'http://www.w3.org/2002/07/owl': 'owl:', 'http://purl.org/dc/elements/1.1/': 'dc:', 'http://purl.org/vocab/aiiso-roles/schema': 'aiiso:', 'http://purl.org/vocab/relationship/': 'rel:', 'http://www.w3.org/2000/10/swap/pim/contact': 'contact:', 'http://kota.s12.xrea.com/vocab/uranai': 'uranai:', 'http://webns.net/mvcb/': 'mvcb:'}

plugin.register('PostgreSQL', store.Store,'rdflib_postgresql.PostgreSQL', 'PostgreSQL')

def initialize(config_file):
    print '[%s] Initializing...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    
    config = __import__(config_file)
    
    try:
        g = ConjunctiveGraph(config.graph_store, config.graph_identifier)
        g.open(config.db_configstring, create=True)
        if config.input_file != None:
            print '[%s] Parsing %s...' % (strftime("%a, %d %b %Y %H:%M:%S", localtime()), config.input_file)
            sys.stdout.flush()
            g.parse(config.input_file, format=config.input_format)
            g.commit()
        else:
            dir_list = os.listdir(options.dir)
            for file_name in dir_list:
                print '[%s] Parsing %s...' % (strftime("%a, %d %b %Y %H:%M:%S", localtime()) ,file_name)
                sys.stdout.flush()
                g.parse(options.dir + '/' + file_name, format=options.format)
                g.commit()
    except Exception as e:
        traceback.print_exc()
        print e 
        print '"%s" not found, or incorrect RDF serialization.' % config.input_file
        sys.stdout.flush()
        exit(-1)
    return g, config

def calculate_edges((offset_limit, config)):
    g = ConjunctiveGraph(config['graph_store'], config['graph_identifier'])
    g.open(config['db_configstring'], create=False)
    engine = create_engine(config['alchemy_configstring'])
    connection = engine.connect()
    query = "SELECT id, uri FROM nodes WHERE type = 'subject' ORDER BY id OFFSET %s LIMIT %s" % offset_limit
    results = connection.execute(query)

    for result in results:
        query = "SELECT ?p ?o WHERE { <%s> ?p ?o }" % result['uri']
        items = g.query(query)
        for item in items:
            if item[0] != 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
                query = "SELECT id FROM nodes WHERE uri = '%s'" % item[1]
                ids = connection.execute(query)
                node_id = -1
                if ids.rowcount > 0:
                    for id_s in ids:
                        node_id = id_s[0]
                    query = "INSERT INTO edges (origin, destination, label) VALUES ('%s', '%s', '%s')" % (result['id'], node_id, item[0])
                    connection.execute(query)
    g.close()
    connection.close()

parser = OptionParser()
parser.add_option("-c", dest="config", help="Configuration file", metavar="CONFIG")

(options, args) = parser.parse_args()

if options.config:

    g, config = initialize(options.config)
    engine = create_engine(config.alchemy_configstring)
    connection = engine.connect()
    
    '''Table('nodes', MetaData(None),
            Column('id', Integer, primary_key = True),
            Column('label', String(200)),
            Column('uri', String(500)),
            Column('type', String(20)))
    Table('edges', MetaData(None),
            Column('id', Integer, primary_key = True),
            Column('destination', Integer),
            Column('origin', Integer),
            Column('label', String(200)))'''

    connection.execute('DELETE FROM edges')
    connection.execute('DELETE FROM nodes')
    connection.execute('ALTER SEQUENCE nodes_id_seq RESTART WITH 1')
    
    print '[%s] FINISHED!' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    print '[%s] Generating subdue graph file...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    f = open(config.output_file, 'w')
    print '[%s] Retrieving subjects...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    query = 'SELECT DISTINCT ?s WHERE {?s ?p ?o}'
    subjects = g.query(query)
    print '[%s] Retrieving objects...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    query = 'SELECT DISTINCT ?o WHERE {?s ?p ?o}'
    objects = g.query(query)

    print '[%s] Inserting subjects into database...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    for item in subjects:
        item_type_list = g.query('SELECT ?o WHERE { <%s> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?o } LIMIT 1' % item[0])
        s_type = None
        if len(item_type_list) > 0:
            for item_type in item_type_list:
                s_type = item_type[0]
            connection.execute("INSERT INTO nodes (uri, label, type) VALUES ('%s', '%s', '%s')" % (str(item[0].encode('utf-8')), s_type.encode('utf-8'), "subject"))

    print '[%s] Inserting objects into database...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    
    validator = URLValidator(verify_exists=False)
    
    for item in objects:
        results = connection.execute("SELECT id FROM nodes WHERE uri = '%s'" % str(item[0].encode('utf-8')))
        if results.rowcount <= 0:
            try:
                validator(item[0])
                connection.execute("INSERT INTO nodes (uri, label, type) VALUES ('%s', '%s', '%s')" % (str(item[0].encode('utf-8')), "URI", "object"))
            except:
                connection.execute("INSERT INTO nodes (uri, label, type) VALUES ('%s', '%s', '%s')" % (str(item[0].encode('utf-8')), "Literal", "object"))

    print '[%s] Calculating offsets and limits for multiprocessing...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()

    results = connection.execute("SELECT MAX(id) FROM nodes WHERE type = 'subject'")
    max_rows = -1
    for result in results:
        max_rows = result[0]

    cluster_size = max_rows / config.max_branches
    mod_size = max_rows % config.max_branches
    offset_limit = []
    for i in range(config.max_branches-1):
        offset = i * cluster_size
        offset_limit.append((offset, cluster_size))
    offset = (config.max_branches - 1) * cluster_size
    limit = cluster_size + mod_size
    offset_limit.append((offset, limit))

    print '[%s] Launching parallel queries...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    pool = Pool(config.max_branches)
    config_dict ={'graph_identifier': config.graph_identifier, 'graph_store': config.graph_store, 'db_configstring': config.db_configstring, 'alchemy_configstring': config.alchemy_configstring}
    pool.map(calculate_edges, zip(offset_limit, repeat(config_dict)))

    print '[%s] Writing files...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()

    nodes = connection.execute("SELECT id, label FROM nodes ORDER BY id")
    for node in nodes:
        f.write('v %s %s\n' % (node['id'], node['label']))

    edges = connection.execute("SELECT origin, destination, label FROM edges")
    for edge in edges:
        f.write('e %s %s %s\n' % (edge['origin'], edge['destination'], edge['label'])) 

    connection.close()
    f.close()
    g.destroy(config.db_path)
    g.close()
    print '[%s] Subdue file generated!' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
else:
    parser.print_help()
    exit(-1)
