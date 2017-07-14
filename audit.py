#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow
import re
from collections import defaultdict

street_type_re = re.compile(r'^\b\S+\.?', re.IGNORECASE)

expected = ["Calle", "CALLE", u"Barrio", u"Centro", "Calleja", "Centro Comercial", "Avenida", "Plaza", "Camino", "Estacion", "Parking", "Campus", "Carretera", 
            "Glorieta", "Paseo", "Rotonda", "Juan", "Gran", "Dante", "Maria", "Pasaje", u'Le\xf3n', u'Comisar\xeda', 
            "Edificio", "Vivero", "CARRETERA", "Centro", "Lope", u'pol\xedgono', u'Pol\xedgono', "Bajada", "Subida", "Grupo", "Rampa", 
            "Barrio", "AREA", "La", "Acceso", "POLIGONO", "Mercado", "Cuesta", u"Urbanizaci\xf3n", "Ernest", "Pol", "Puerto", "Jardines",
            "San",u"Autov\xeda", u"V\xeda", "MercaSantander", u"Traves\xeda", u"ISLA", u"Playa", "N-611", "BARRIO", "Las"]

# UPDATE THIS VARIABLE
mapping = { "C/": "Calle",
            "Barrio": "Barrio",
            "Calle": "Calle",
            "Calles": "Calle",
            "Avenidad" : "Avenida",
            "Avda.": "Avenida",
            u"Calla": "Calle",
            "name=Avenida": "Avenida",
            "name=Calle": "Calle",
            "AREA,": "Area",
            "Bajade": "Bajada",
            "Ramapa": "Rampa"
          }

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """
    Yield element if it is the right type of tag
    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def auditstreet(osmfile):
    #from collections import defaultdict

    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag): # Checking house name and street name
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

def update_name(name, mapping):

    m = street_type_re.search(name)
    better_name = name
    if m:
        #print mapping[m.group()]
        better_street_type = mapping[m.group()]        
        better_name = street_type_re.sub(better_street_type, name)

    return better_name


def audit_postcode(postcode_types, postcode):
    postcode_types[postcode].add(postcode)


def is_postcode(elem):
    return (elem.attrib['k'] == "addr:postcode" and len(elem.attrib['v']) != 5)

def auditpostcode(osmfile):
    osm_file = open(osmfile, "r")
    postcode_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_postcode(tag): # Here we check postcode > 5 number
                    audit_postcode(postcode_types, tag.attrib['v'])
    osm_file.close()
    return postcode_types


def update_postcode(postcode):
    """detects pattern and returns clean postcode"""
    clean_postcode = 's/n'
    if re.match(re.compile(r'^\d{5}$'), postcode):
        return postcode
    elif re.match(re.compile(r'^(\d{5}).+$'), postcode):
        clean_postcode = re.findall(re.compile(r'^(\d{5}).+$'), postcode)[0]
    return clean_postcode

def is_housenummer(elem):
    return (elem.attrib['k'] == "addr:housenumber")


def audit_housenummer(no_housenummer, house_nummer):
    if not house_nummer.isdigit():
        no_housenummer[house_nummer].add(house_nummer)
    

def audithousenumber(osmfile):
    osm_file = open(osmfile, "r")
    no_housenummer = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_housenummer(tag): # Checking house nummer
                    audit_housenummer(no_housenummer, tag.attrib['v'])
    osm_file.close()
    return no_housenummer


def update_housenumber(housenumber):
    num = re.findall('[a-zA-Z]*', housenumber)
    if num:
        num = num[0]

    if num == "Numero":
        housen = (re.findall(r'\d+', housenumber))
#        print re.findall(r'\d+', housenumber)
        if housen:
            return (re.findall(r'\d+', housenumber))