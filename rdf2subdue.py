from rdflib import ConjunctiveGraph
from optparse import OptionParser
from django.core.validators import URLValidator
from rdflib import plugin
from rdflib import store
from time import strftime, localtime
from multiprocessing import Process, Pipe, Value
from itertools import repeat
from sqlalchemy import create_engine
import traceback
import os
import sys
import traceback
import string
from ctypes import c_int, c_char_p

PREFIXES = {'http://rdfs.org/sioc/ns': 'sioc:', 'http://xmlns.com/foaf/0.1/': 'foaf:', 'http://www.daml.org/2001/10/html/airport-ont': 'daml:', 'http://swrc.ontoware.org/ontology': 'swrc:', 'http://purl.org/ontology/bibo/': 'bibo:', 'http://www.w3.org/2000/01/rdf-schema': 'rdf:', 'http://purl.org/dc/terms/': 'dcterms:', 'http://www.w3.org/2002/07/owl': 'owl:', 'http://purl.org/dc/elements/1.1/': 'dc:', 'http://purl.org/vocab/aiiso-roles/schema': 'aiiso:', 'http://purl.org/vocab/relationship/': 'rel:', 'http://www.w3.org/2000/10/swap/pim/contact': 'contact:', 'http://kota.s12.xrea.com/vocab/uranai': 'uranai:', 'http://webns.net/mvcb/': 'mvcb:'}

plugin.register('PostgreSQL', store.Store,'rdflib_postgresql.PostgreSQL', 'PostgreSQL')

def prefix(uri):
    if '#' in uri:
        prefix = uri.split('#')[0]
        pred = uri.split('#')[1]
    else:
        prefix = ""
        token_list = uri.split('/')
        for token, i in zip(token_list, range(len(token_list) - 1)):
            prefix += token + '/'
        pred = token_list[len(token_list)-1]
    #print prefix
    if prefix in PREFIXES.keys():
        return PREFIXES[prefix] + pred
    else:
        return uri

def rdfcollection2list(collection, conn):
    result_list = [str(x[0].encode('utf-8')) for x in collection]
    conn.send(result_list)
    conn.close()

def subjects2nodes(subjects_list, nodes_dict, nodes_str, edges_wrapper):
    g = ConjunctiveGraph(store='PostgreSQL', identifier='http://rdf2subdue/')
    g.open("user=postgres,password=p0stgr3s,host=localhost,db=rdfstore", create=False)
    for subject in subjects_list:
        query = 'SELECT ?p ?o WHERE {<%s> ?p ?o}' % subject
        
        result = g.query(query)
        
        rdf_type = "Unknown"
        for p, o in result:
            
            p = str(p.encode('utf-8'))
            o = str(o.encode('utf-8'))
            if p == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
                rdf_type = o
            else:
                edges_wrapper.value += 'u %s %s "%s"\n' % (nodes_dict[subject], nodes_dict[o], p)
        nodes_str.value += 'v %s "%s"\n' % (nodes_dict[subject], rdf_type)
    print nodes_str
    print len(nodes_str.value)
    print edges_wrapper
    print len(edges_wrapper.value)
    g.close()

def objects2nodes(objects_list, nodes_dict, nodes_str):
    #nodes_str = ""
    val = URLValidator(verify_exists=False)
    for obj in objects_list:
        try:
            val(obj)
            nodes_str.value += 'v %s "URI"\n' % nodes_dict[obj]
        except:
            nodes_str.value += 'v %s "Literal"\n' % nodes_dict[obj]
    print nodes_str
    print len(nodes_str.value)
    #conn.send(nodes_str)
    #conn.close()

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
        print '"%s" not found, or incorrect RDF serialization.' % options.input
        sys.stdout.flush()
        exit(-1)
    return g, config

parser = OptionParser()
#parser.add_option("-i", dest="input", help="Input RDF file.", metavar="INPUT")
#parser.add_option("-d", dest="dir", help="Input RDF files dir", metavar="INPUTDIR")
#parser.add_option("-o", dest="output", help="Output graph file", metavar="OUTPUT")
#parser.add_option("-f", dest="format", help="Format of input file", metavar="FORMAT")
parser.add_option("-c", dest="config", help="Configuration file", metavar="CONFIG")

(options, args) = parser.parse_args()

if options.config:

    g, config = initialize(options.config)
    engine = create_engine(config.alchemy_configstring)
    connection = engine.connect()
    connection.execute('DELETE FROM nodes')
    connection.execute('DELETE FROM edges')
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
    #print '[%s] Merging nodes...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    #sys.stdout.flush()
    
    #subjects_list = [str(s[0].encode('utf-8')) for s in subjects]

    print '[%s] Inserting subjects into database...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    for item in subjects:
        item_type_list = g.query('SELECT ?o WHERE { <%s> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?o } LIMIT 1' % item[0])
        s_type = None
        if len(item_type_list) > 0:
            for item_type in item_type_list:
                s_type = item_type[0]
            connection.execute("INSERT INTO nodes (uri, label) VALUES ('%s', '%s')" % (str(item[0].encode('utf-8')), s_type.encode('utf-8')))

    print '[%s] Inserting objects into database...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    
    validator = URLValidator(verify_exists=False)
    
    for item in objects:
        results = connection.execute("SELECT id FROM nodes WHERE uri = '%s'" % str(item[0].encode('utf-8')))
        if results.rowcount <= 0:
            try:
                validator(item[0])
                connection.execute("INSERT INTO nodes (uri, label) VALUES ('%s', '%s')" % (str(item[0].encode('utf-8')), "URI"))
            except:
                connection.execute("INSERT INTO nodes (uri, label) VALUES ('%s', '%s')" % (str(item[0].encode('utf-8')), "Literal"))

    '''objects_list = [str(o[0].encode('utf-8')) for o in objects]
    objects_list = [o for o in objects_list if o not in subjects_list]
    nodes = subjects_list + objects_list
    nodes_dict = {}
    i = 1
    print '[%s] Assigning IDs to nodes...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    for node in nodes:
        #f.write('v %s node%s\n' % (i, i))
        nodes_dict[node] = i
        i += 1
    
    edges = ""
    nodes_str = ""
    '''
    print '[%s] Generating nodes and edges...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()

    results = connection.execute("SELECT * FROM NODES ORDER BY id ASC LIMIT 1 OFFSET 100")

    '''for subject in subjects_list:
        query = 'SELECT ?p ?o WHERE {<%s> ?p ?o}' % subject
        result = g.query(query)
        rdf_type = "Unknown"
        for p, o in result:
            p = str(p.encode('utf-8'))
            o = str(o.encode('utf-8'))
            #print p
            if p == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
                rdf_type = o
            else:
                edges += 'u %s %s "%s"\n' % (nodes_dict[subject], nodes_dict[o], p)
        #print subject, rdf_type
        nodes_str += 'v %s "%s"\n' % (nodes_dict[subject], rdf_type)

    val = URLValidator(verify_exists=False)

    for obj in objects_list:
        try:
            val(obj)
            nodes_str += 'v %s "URI"\n' % nodes_dict[obj]
        except:
            nodes_str += 'v %s "Literal"\n' % nodes_dict[obj]
            #nodes_str += 'v %s "Literal"\n' % nodes_dict[obj]
    '''

    print '[%s] Writing files...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    f.write(nodes_str)
    f.write(edges)

    connection.close()
    f.close()
    g.destroy(None)
    g.close()
    print '[%s] Subdue file generated!' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
else:
    parser.print_help()
    exit(-1)
