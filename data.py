#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import codecs
import json

from audit import update_name
from audit import update_postcode
from audit import update_housenumber

import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
"""
Your task is to wrangle the data and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. 

Note that in this exercise we do not use the 'update street name' procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to 
update the street names before you save them to JSON. 

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if the second level tag "k" value contains problematic characters, it should be ignored
- if the second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if the second level tag "k" value does not start with "addr:", but contains ":", you can
  process it in a way that you feel is best. For example, you might split it into a two-level
  dictionary like with "addr:", or otherwise convert the ":" to create a valid key.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
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


    node = {}
    # you should process only 2 types of top level tags: "node" and "way"
    if element.tag == "node" or element.tag == "way" :
        for key in element.attrib.keys():
            val = element.attrib[key]
            node["type"] = element.tag
            if key in CREATED:
                if not "created" in node.keys():
                    node["created"] = {}
                node["created"][key] = val
            elif key == "lat" or key == "lon":
                if not "pos" in node.keys():
                    node["pos"] = [0.0, 0.0]
                old_pos = node["pos"]
                if key == "lat":
                    new_pos = [float(val), old_pos[1]]
                else:
                    new_pos = [old_pos[0], float(val)]
                node["pos"] = new_pos
            else:
                node[key] = val
            for tag in element.iter("tag"):
                tag_key = tag.attrib['k']
                tag_val = tag.attrib['v']
                if problemchars.match(tag_key):
                    continue
                elif tag_key.startswith("addr:"):
                    if not "address" in node.keys():
                        node["address"] = {}
                    addr_key = tag.attrib['k'][len("addr:") : ]
                    if lower_colon.match(addr_key):
                        continue
                    else:
                        if tag_val.split(' ')[0] in expected:
                            node["address"][addr_key] = tag_val
                        elif tag_key.endswith("street"):
                            node["address"][addr_key] = update_name(tag_val, mapping)
                        elif tag_key.endswith("postcode"):
                            node["address"][addr_key] = update_postcode(tag_val)
                        elif tag_key.endswith("housenumber"):
                            node["address"][addr_key] = update_housenumber(tag_val)
                        else:
                            node["address"][addr_key] = tag_val
                            
                elif lower_colon.match(tag_key):
                    node[tag_key] = tag_val
                else:
                    node[tag_key] = tag_val
        for tag in element.iter("nd"):
            if not "node_refs" in node.keys():
                node["node_refs"] = []
            node_refs = node["node_refs"]
            node_refs.append(tag.attrib["ref"])
            node["node_refs"] = node_refs

        return node
    else:
        return None


def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        fo.write("[")
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+",\n")
                else:
                    fo.write(json.dumps(el) + ",\n")
        fo.write("]")

    return data