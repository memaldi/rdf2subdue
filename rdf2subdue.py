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
    objects = g.query(query)
    subjects_list = [str(s[0].encode('utf-8')) for s in subjects]
    objects_list = [str(o[0].encode('utf-8')) for o in objects]
    objects_list = [o for o in objects_list if o not in subjects_list]
    nodes = subjects_list + objects_list
    nodes_dict = {}
    i = 1
    for node in nodes:
        f.write('v %s "%s"\n' % (i, node[0:82]))
        nodes_dict[node] = i
        i += 1
    edges = ""
    for subject in subjects_list:
        query = 'SELECT ?p ?o WHERE {<%s> ?p ?o}' % subject
        result = g.query(query)
        for p, o in result:
            o = str(o.encode('utf-8'))
            edges += 'u %s %s "%s"\n' % (nodes_dict[subject], nodes_dict[o], str(p.encode('utf-8')))
    f.write(edges)

else:
    parser.print_help()
    exit(-1)
