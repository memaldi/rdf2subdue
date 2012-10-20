from rdflib import ConjunctiveGraph
from optparse import OptionParser
from django.core.validators import URLValidator
from rdflib import plugin
from rdflib import store
from time import strftime, localtime
import traceback
import os
import sys

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

parser = OptionParser()
parser.add_option("-i", dest="input", help="Input RDF file.", metavar="INPUT")
parser.add_option("-d", dest="dir", help="Input RDF files dir", metavar="INPUTDIR")
parser.add_option("-o", dest="output", help="Output graph file", metavar="OUTPUT")
parser.add_option("-f", dest="format", help="Format of input file", metavar="FORMAT")
(options, args) = parser.parse_args()

if (options.input or options.dir) and options.output and options.format:
    print '[%s] Initializing...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    try:
        g = ConjunctiveGraph(store='PostgreSQL', identifier='http://rdf2subdue/')
        g.open("user=postgres,password=p0stgr3s,host=localhost,db=rdfstore", create=True)
        if options.input != None:
            print '[%s] Parsing %s...' % (strftime("%a, %d %b %Y %H:%M:%S", localtime()) ,options.input)
	    sys.stdout.flush()
            g.parse(options.input, format=options.format)
        else:
            dir_list = os.listdir(options.dir)
            for file_name in dir_list:
                print 'Parsing %s...' % file_name
		sys.stdout.flush()
                g.parse(file_name, format=options.format)
    except Exception as e:
        traceback.print_exc()
        print e 
        print '"%s" not found, or incorrect RDF serialization.' % options.input
	sys.stdout.flush()
        exit(-1)
    print '[%s] FINISHED!' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    print '[%s] Generating subdue graph file...' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
    f = open(options.output, 'w')
    eq = open('%s.eq' % options.output, 'w')
    query = 'SELECT DISTINCT ?s WHERE {?s ?p ?o}'
    subjects = g.query(query)
    query = 'SELECT DISTINCT ?o WHERE {?s ?p ?o}'
    objects = g.query(query)
    subjects_list = [str(s[0].encode('utf-8')) for s in subjects]
    objects_list = [str(o[0].encode('utf-8')) for o in objects]
    objects_list = [o for o in objects_list if o not in subjects_list]
    nodes = subjects_list + objects_list
    nodes_dict = {}
    i = 1
    for node in nodes:
        #f.write('v %s node%s\n' % (i, i))
        #eq.write('%s "%s"\n' % (i, node))
        nodes_dict[node] = i
        i += 1
    edges = ""
    nodes_str = ""
    for subject in subjects_list:
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

    f.write(nodes_str)
    f.write(edges)

    f.close()
    eq.close()
    g.destroy(None)
    g.close()
    print '[%s] Subdue file generated!' % strftime("%a, %d %b %Y %H:%M:%S", localtime())
    sys.stdout.flush()
else:
    parser.print_help()
    exit(-1)
