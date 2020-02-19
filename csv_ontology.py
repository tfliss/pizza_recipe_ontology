import pandas as pd
from io import StringIO
from owlready2 import *
import types
import yaml
import d3fdgraph
import pandas as pd
from rdflib import RDFS, OWL
from owlready2 import default_world

def ontology_from_yaml(yml, uri):
    ont = get_ontology(uri)

    with open(yml) as f:
        yaml_ontology = yaml.safe_load(f)

    create_classes(ont, yaml_ontology['Classes'])
    create_individuals(ont, yaml_ontology['Individuals'])
    create_properties(ont, yaml_ontology['ObjectProperties'])
    associations(ont, yaml_ontology['Associations'])
    
    return ont

# TODO: Need to write something similar to below for properties
def create_classes(ont, class_list, super_class=None):
    # Create some subclasses as a tree
    if super_class is None:
        super_class = Thing

    with ont:
        for clz in class_list:
            if isinstance(clz, dict):
                for scn, cl in clz.items():
                    NewClass = types.new_class(scn, (super_class,))
                    NewClass.label.en = scn
                    create_classes(ont, cl, NewClass)
            else:
                NewClass = types.new_class(clz, (super_class,))
                NewClass.label.en = clz

def create_properties(ont, prop_list, super_prop=None):
    if super_prop is None:
        super_prop = ObjectProperty

    with ont:
        for prop in prop_list:
            if isinstance(prop, dict):
                for spn, pl in prop.items():
                    NewProp = types.new_class(spn, (super_prop,))
                    NewProp.label.en = spn
                    NewProp.domain = []
                    NewProp.range = []
                    create_properties(ont, pl, NewProp)
            else:
                NewProp = types.new_class(prop, (super_prop,))
                NewProp.label.en = prop
                NewProp.domain = []
                NewProp.range = []


def associations(ont, dr_list):
    with ont:
        for prop,values in dr_list.items():
            print(prop)
            if 'domain' in values:
                ont[prop].domain.append(ont[values['domain']])
            if 'range' in values:
                ont[prop].range.append(ont[values['range']])

def create_individuals(ont, individual_dict):
    for super_class, individual_list in individual_dict.items():
        for individual in individual_list:
            i = ont[super_class](individual.lower())
            i.label.en = individual.lower()


def class_tree_df():
    graph = default_world.as_rdflib_graph()

    subclass_df = pd.DataFrame(
        graph.query('''
    SELECT ?c ?s WHERE {
        {
            ?c rdfs:subClassOf ?s .
            FILTER NOT EXISTS { ?c rdfs:label ?cl }
            FILTER NOT EXISTS { ?s rdfs:label ?sl }    
        } UNION {
            ?c rdfs:subClassOf ?s_ .
            FILTER NOT EXISTS { ?c rdfs:label ?cl }
            ?s_ rdfs:label ?s .
        } UNION {
            ?c_ rdfs:subClassOf ?s .
            FILTER NOT EXISTS { ?s rdfs:label ?sl }
            ?c_ rdfs:label ?c .
        } UNION {
            ?c_ rdfs:subClassOf ?s_ .
            ?c_ rdfs:label ?c .
            ?s_ rdfs:label ?s .
        }
    }
    ''',
            initNs={ 'rdfs': RDFS }
        ),
        columns=['source', 'target']
    )
    subclass_df['weight'] = 1

    return subclass_df