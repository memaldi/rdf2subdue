from rdflib import Graph
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-i", dest="input", help="Input RDF file.", metavar="INPUT")
parser.add_option("-o", dest="output", help="Output graph file", metavar="OUTPUT")
(options, args) = parser.parse_args()

if options.input and options.output:
    try:
        g = Graph()
        g.parse(options.input)
    except Exception as e:
        print '"%s" not found, or incorrect RDF serialization.' % options.input
        exit(-1)
    f = open(options.output, 'w')
    query = 'SELECT DISTINCT ?s WHERE {?s ?p ?o}'
    subjects = g.query(query)
    query = 'SELECT DISTINCT ?o WHERE {?s ?p ?o}'
    predicates = g.query(query)
    nodes = [predicate for predicate in predicates if predicate not in subjects]
    nodes_dict = {}
    i = 1
    for node in nodes:
        f.write('v %s %s' % (i, str(node[0].encode('utf-8'))))
        nodes_dict[str(node[0].encode('utf-8'))] = i
        i += 1
        print node
    edges = ""
    for subject in subjects:
        query = 'SELECT ?p ?o WHERE {<%s> ?p ?o}' % str(subject[0].encode('utf-8'))
        print query
        result = g.query(query)
        for p, o in result:
            edges += 'd %s %s %s\n' % (nodes_dict[str(subject[0].encode('utf-8'))], nodes_dict[str(o)], str(p))


else:
    parser.print_help()
    exit(-1)
