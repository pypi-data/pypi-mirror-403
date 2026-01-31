from tinydb import TinyDB, Query


def insert(
        save_data: dict,
        db_name: str = "db.json",
):
    db = TinyDB(db_name)
    return db.insert(save_data)


def insert_multiple(
        save_data: list,
        db_name: str = "db.json",
):
    db = TinyDB(db_name)
    return db.insert_multiple(save_data)


def get(
        db_name: str = "db.json",
        _all: bool = False,
        search_key: str = None,
        search_value = None
):
    db = TinyDB(db_name)
    tb = Query()
    if _all:
        return db.all()  # 输出所有
    else:
        if search_key is not None and search_value is not None:
            return db.search(eval(f"tb.{search_key}") == search_value)
        else:
            return db.all()


def get_all(db_name: str):
    db = TinyDB(db_name)
    return db.all()


def upsert(
        data: list,
        db_name: str = "db.json",
        key: str = None,
):
    db = TinyDB(db_name)
    tb = Query()
    for each_data in data:
        key_value = each_data.get(key)
        db.upsert(each_data, tb[key] == key_value)


if __name__ == '__main__':
    # print(insert_multiple([{"a": 2}, {"a": 2}]))
    # print(get({"name": "John"}))

    print(upsert(
        data=[
            {"a": 2, "b": 444},
            # {"a": 3, "b": 4, "c": 5, "d": 6, "e": 7},
        ],
        key="a"
    ))

    # print(get(
    #     search_key="a",
    #     search_value=2,
    # ))