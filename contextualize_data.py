"""Convert JSON data files in ./Data into RDF using the IOF ontology.

Usage:
  pip install rdflib
  python contextualize_data.py

Edit the `MAPPING` dict below to map JSON fields to ontology properties.
"""
import os
import glob
import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD


BASE_NS = "http://example.org/lead/"  # change to your preferred base URI
DATA_DIR = os.path.join("Data")
ONTO_DIR = os.path.join("ontology_tmp")
OUT_FILE = "contextualized_output.ttl"


# Simple mapping: filename -> class and field->property
# Update these to use URIs from your ontology (replace lead:... below)
MAPPING = {
    "Storedata.json": {
        "class": Namespace(BASE_NS).Store,
        "id_field": "store_id",
        # use dotted paths for nested fields (e.g. "location.city")
        "fields": {
            "store_name": RDFS.label,
            "store_type": Namespace(BASE_NS).storeType,
            "location.city": Namespace(BASE_NS).city,
            "location.state": Namespace(BASE_NS).state,
            "location.zip": Namespace(BASE_NS).postalCode,
            "store_size_sqft": Namespace(BASE_NS).storeSizeSqFt,
            "sku_count": Namespace(BASE_NS).skuCount,
            "operating_days_per_week": Namespace(BASE_NS).operatingDaysPerWeek,
            "service_level_target": Namespace(BASE_NS).serviceLevelTarget,
            "currency": Namespace(BASE_NS).currency,
        },
    },
    "MasterData.json": {
        "class": Namespace(BASE_NS).Masterdata,
        "id_field": "sku_id",
        "fields": {
            "sku_name": RDFS.label,
            "category": Namespace(BASE_NS).category,
            "perishable": Namespace(BASE_NS).perishable,
            "shelf_life_days": Namespace(BASE_NS).shelfLifeDays,
            "unit_of_measure": Namespace(BASE_NS).unitOfMeasure,
            "avg_unit_cost": Namespace(BASE_NS).avgUnitCost,
            "avg_retail_price": Namespace(BASE_NS).avgRetailPrice,
        },
    },
    # Add other files and their mappings here
}


def _title_case(name: str) -> str:
    parts = [p for p in name.replace('-', ' ').replace('_', ' ').split() if p]
    return ''.join(p.capitalize() for p in parts)


def _camel_case(name: str) -> str:
    parts = name.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:]) if len(parts) > 1 else name


def _flatten_keys(obj, prefix=''):
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys.update(_flatten_keys(v, path))
            else:
                keys.add(path)
    return keys


def auto_generate_mappings(data_dir=DATA_DIR):
    """Generate simple mappings for JSON files not explicitly mapped.

    For each JSON file, create a class URI based on the filename and map
    each top-level or nested key (using dotted paths) to `BASE_NS+camelCase`.
    """
    gen = {}
    json_files = glob.glob(os.path.join(data_dir, "*.json"))
    for jf in json_files:
        name = os.path.basename(jf)
        if name in MAPPING:
            continue

        with open(jf, 'r', encoding='utf-8') as fh:
            try:
                obj = json.load(fh)
            except Exception:
                continue

        # find a sample record to inspect structure
        sample = obj
        if isinstance(obj, dict):
            # try to use first list value or the dict itself
            for v in obj.values():
                if isinstance(v, list) and v:
                    sample = v[0]
                    break

        fields = {}
        if isinstance(sample, dict):
            for path in sorted(_flatten_keys(sample)):
                last = path.split('.')[-1].lower()
                # preferred property mappings for common field names
                PREFERRED_FIELD_MAP = {
                    'name': RDFS.label,
                    'store_name': RDFS.label,
                    'sku_name': RDFS.label,
                    'category': Namespace(BASE_NS).category,
                    'unit_of_measure': Namespace(BASE_NS).unitOfMeasure,
                    'avg_unit_cost': Namespace(BASE_NS).avgUnitCost,
                    'avg_retail_price': Namespace(BASE_NS).avgRetailPrice,
                    'perishable': Namespace(BASE_NS).perishable,
                    'shelf_life_days': Namespace(BASE_NS).shelfLifeDays,
                    'currency': Namespace(BASE_NS).currency,
                    'sku_count': Namespace(BASE_NS).skuCount,
                    'store_type': Namespace(BASE_NS).storeType,
                }

                if path.lower().endswith('name') or (last in PREFERRED_FIELD_MAP and PREFERRED_FIELD_MAP[last] == RDFS.label):
                    prop = RDFS.label
                elif last in PREFERRED_FIELD_MAP:
                    prop = PREFERRED_FIELD_MAP[last]
                else:
                    prop = Namespace(BASE_NS)[_camel_case(path.replace('.', '_'))]

                fields[path] = prop

        id_field = None
        # prefer explicit common id names first, then any *_id
        preferred_ids = ['id', 'sku_id', 'store_id', 'item_id']
        for pid in preferred_ids:
            for f in fields:
                if f.lower() == pid:
                    id_field = f
                    break
            if id_field:
                break

        if not id_field:
            for f in fields:
                if f.lower().endswith('_id') or f.lower() == 'id':
                    id_field = f
                    break

        # class naming: use PascalCase, singularize simple trailing 's'
        base_name = os.path.splitext(name)[0]
        parts = [p for p in base_name.replace('-', ' ').replace('_', ' ').split() if p]
        pascal = ''.join(p.capitalize() for p in parts)
        if pascal.endswith('s') and len(pascal) > 1:
            pascal = pascal[:-1]

        gen[name] = {
            'class': Namespace(BASE_NS)[pascal],
            'id_field': id_field,
            'fields': fields,
        }

    return gen


def load_ontology(graph: Graph, ont_dir: str):
    files = glob.glob(os.path.join(ont_dir, "*.rdf")) + glob.glob(os.path.join(ont_dir, "*.ttl"))
    for f in files:
        try:
            graph.parse(f)
            print(f"Loaded ontology: {f}")
        except Exception as e:
            print(f"Failed to load {f}: {e}")


def to_literal(value):
    if isinstance(value, int):
        return Literal(value, datatype=XSD.integer)
    if isinstance(value, float):
        return Literal(value, datatype=XSD.decimal)
    return Literal(value)


def process_file(graph: Graph, filepath: str, mapping: dict):
    name = os.path.basename(filepath)
    if name not in mapping:
        print(f"No mapping for {name}, skipping")
        return

    conf = mapping[name]
    with open(filepath, "r", encoding="utf-8") as fh:
        records = json.load(fh)
        if isinstance(records, dict):
            # common pattern: file contains {"items": [...]}
            # try to find list inside
            for v in records.values():
                if isinstance(v, list):
                    records = v
                    break
        # if still a dict, it may be a single record or a mapping id->record
        if isinstance(records, dict):
            # mapping of id->record (all values are dicts)
            if all(isinstance(v, dict) for v in records.values()):
                new_records = []
                for k, v in records.items():
                    rec = v.copy()
                    if conf.get("id_field") and conf["id_field"] not in rec:
                        rec[conf["id_field"]] = k
                    new_records.append(rec)
                records = new_records
            else:
                # single object -> wrap in list
                records = [records]

    for rec in records:
        if conf.get("id_field") and conf["id_field"] in rec:
            subj = URIRef(BASE_NS + str(rec[conf["id_field"]]))
        else:
            # fallback to blank node-like URI
            subj = URIRef(BASE_NS + os.path.splitext(name)[0] + "/" + str(records.index(rec)))

        graph.add((subj, RDF.type, conf["class"]))

        for src_field, prop in conf["fields"].items():
            # support nested dotted paths like "location.city"
            if "." in src_field:
                parts = src_field.split(".")
                val = rec
                for p in parts:
                    if isinstance(val, dict) and p in val:
                        val = val[p]
                    else:
                        val = None
                        break
            else:
                val = rec.get(src_field)

            if val not in (None, ""):
                graph.add((subj, prop, to_literal(val)))


def main():
    g = Graph()

    # load ontology files into graph so namespace and properties are resolved
    load_ontology(g, ONTO_DIR)

    # bind some useful prefixes
    g.bind("lead", BASE_NS)
    g.bind("rdfs", RDFS)

    # augment MAPPING with any auto-generated mappings for unmapped files
    auto_map = auto_generate_mappings(DATA_DIR)
    if auto_map:
        # merge but keep user-provided mappings
        for k, v in auto_map.items():
            if k not in MAPPING:
                MAPPING[k] = v

    # process JSON files in Data/
    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    for jf in json_files:
        process_file(g, jf, MAPPING)

    g.serialize(destination=OUT_FILE, format="turtle")
    print(f"Wrote RDF to {OUT_FILE}")


if __name__ == "__main__":
    main()
