# coding=iso-8859-15
from rdflib import ConjunctiveGraph
from optparse import OptionParser
from django.core.validators import URLValidator
from rdflib import plugin
from rdflib import store
from time import strftime, localtime
from multiprocessing import Pool
from itertools import repeat
from sqlalchemy import create_engine, MetaData, Column, Integer, String, ForeignKey, func
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import sys
import traceback

metadata = MetaData()
Base = declarative_base(metadata=metadata)

class Node(Base):
    __tablename__ = 'node'

    node_id = Column(Integer, primary_key=True)
    node_label = Column(String)
    node_uri = Column(String)
    node_type = Column(String)

    def __init__(self, node_uri, node_label, node_type):
        self.node_uri = node_uri
        self.node_label = node_label
        self.node_type = node_type

    def add_neighbors(self, edge_label, *nodes):
        for node in nodes:
            Edge(self, node, edge_label=edge_label)
        return self

    def higher_neighbors(self):
        return [x.higher_node for x in self.lower_edges]

    def lower_neighbors(self):
        return [x.lower_node for x in self.higher_edges]

class Edge(Base):
    __tablename__ = 'edge'

    edge_label = Column(String)
    
    edge_id = Column(Integer, primary_key=True)

    lower_id = Column(Integer,
                        ForeignKey('node.node_id'))

    higher_id = Column(Integer,
                        ForeignKey('node.node_id'))

    lower_node = relationship(Node,
                                primaryjoin=lower_id==Node.node_id,
                                backref='lower_edges')
    higher_node = relationship(Node,
                                primaryjoin=higher_id==Node.node_id,
                                backref='higher_edges')

    # here we have lower.node_id <= higher.node_id
    def __init__(self, n1, n2, edge_label):
        if n1.node_id < n2.node_id:
            self.lower_node = n1
            self.higher_node = n2
        else:
            self.lower_node = n2
            self.higher_node = n1
        self.edge_label = edge_label

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
            dir_list = os.listdir(config.input_dir)
            for file_name in dir_list:
                print '[%s] Parsing %s...' % (strftime("%a, %d %b %Y %H:%M:%S", localtime()) ,file_name)
                sys.stdout.flush()
                g.parse(config.input_dir + '/' + file_name, format=config.input_format)
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
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    results = session.query(Node).filter_by(node_type="subject").order_by(Node.node_id.desc()).offset(offset_limit[0]).limit(offset_limit[1]).all()
    
    for result in results:
        query = "SELECT ?p ?o WHERE { <%s> ?p ?o }" % result.node_uri
        items = g.query(query)
        for item in items:
            if str(item[0]) != "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
                neighbors = session.query(Node).filter_by(node_uri=item[1]).all()
                if len(neighbors) > 0:                    
                    for neighbor in neighbors:
                        result.add_neighbors(str(item[0]), neighbor)
        session.commit()
    g.close()
    session.close()

parser = OptionParser()
parser.add_option("-c", dest="config", help="Configuration file", metavar="CONFIG")

(options, args) = parser.parse_args()

if options.config:

    g, config = initialize(options.config)
    engine = create_engine(config.alchemy_configstring)
    connection = engine.connect()
    
    Base.metadata.create_all(engine)

    if config.db_engine == 'Postgresql':
        connection.execute('ALTER SEQUENCE node_node_id_seq RESTART WITH 1')
    
    connection.close()
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    edges = session.query(Edge).delete()
    nodes = session.query(Node).delete()
    session.commit()
    
    print '[%s] FINISHED!' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    print '[%s] Generating subdue graph file...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    f = open(config.output_file, 'w')
    print '[%s] Retrieving subjects...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    query = 'SELECT DISTINCT ?s WHERE {?s ?p ?o}'
    subjects = g.query(query)
    
    print '[%s] Inserting subjects into database...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    for item in subjects:
        item_type_list = g.query('SELECT ?o WHERE { <%s> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?o } LIMIT 1' % item[0])
        s_type = None
        if len(item_type_list) > 0:
            for item_type in item_type_list:
                s_type = item_type[0]
            node = Node(node_uri=str(item[0].encode('utf-8')), node_label=s_type.encode('utf-8'), node_type="subject")
            session.add(node)
    session.commit()

    del subjects

    print '[%s] Retrieving objects...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    query = 'SELECT DISTINCT ?o WHERE {?s ?p ?o}'
    objects = g.query(query)

    print '[%s] Inserting objects into database...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    
    validator = URLValidator(verify_exists=False)
    
    for item in objects:
        results = session.query(Node).filter_by(node_uri=str(item[0].encode('utf-8'))).all()
        if len(results) <= 0:
            try:
                validator(item[0])
                node = Node(node_uri=str(item[0].encode('utf-8')), node_label="URI", node_type="object")
                session.add(node)
            except:
                node = Node(node_uri=str(item[0].encode('utf-8')), node_label="Literal", node_type="object")
                session.add(node)
    session.commit()
    print '[%s] Calculating offsets and limits for multiprocessing...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()

    del objects

    results = session.query(func.max(Node.node_id)).filter_by(node_type="subject").all()
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

    nodes = session.query(Node.node_id, Node.node_label).order_by(Node.node_id).all()
    for node in nodes:
        f.write('v %s %s\n' % (node.node_id, node.node_label))

    edges = session.query(Edge.lower_id, Edge.higher_id, Edge.edge_label).all()
    for edge in edges:
        f.write('e %s %s %s\n' % (edge.lower_id, edge.higher_id, edge.edge_label)) 

    session.close()
    f.close()
    g.destroy(config.db_path)
    g.close()
    print '[%s] Subdue file generated!' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
else:
    parser.print_help()
    exit(-1)
