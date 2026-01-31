from pymongo import MongoClient  # 4.15.5
from .ui import MongoApp


def get_doc_structure(doc):
    """Vrati dict s kľúčmi a typom hodnoty (ako list, aby sa dali spájať)."""
    schema = {}
    for k, v in doc.items():
        schema[k] = [type(v).__name__]
    return schema


def find_collection_structures(collection):
    """Vráti všetky štruktúry dokumentov v kolekcii so zjednotenými typmi."""
    structures = {}  # kľúč = frozenset(kľúčov dokumentu), hodnota = {"schema": dict, "count": int}

    for doc in collection.find():
        struct = get_doc_structure(doc)
        keyset = frozenset(struct.keys())

        if keyset not in structures:
            # vytvoríme nový záznam
            structures[keyset] = {"schema": struct, "count": 1}
        else:
            # update existujúcej štruktúry
            existing = structures[keyset]
            existing["count"] += 1
            for k, v in struct.items():
                for t in v:
                    if t not in existing["schema"][k]:
                        existing["schema"][k].append(t)

    # výsledok prevedieme do požadovaného formátu
    result = []
    type_count = 1
    for keyset, data in structures.items():
        result.append({
            f"DOCUMENT TYPE {type_count}": data["schema"],
            "count": data["count"]
        })
        type_count += 1

    return result


def get_collection_structures(uri, db_name):
    all_structures = {}
    client = MongoClient(uri)
    db = client[db_name]
    for coll_name in db.list_collection_names():
        coll = db[coll_name]
        all_structures[coll_name] = find_collection_structures(coll)

    return all_structures


def ddstav(uri, db_name):
    structures = get_collection_structures(uri, db_name)
    app = MongoApp(structures)
    app.mainloop()
