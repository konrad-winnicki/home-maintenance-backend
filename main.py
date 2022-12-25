from json import JSONEncoder
from json import JSONDecoder
import jsonpickle
from flask import Flask, jsonify
from flask import request
from flask import current_app
from flask_cors import CORS
import json
import uuid


# TODO zwrocic tylko status, dodac zwrotny response do wyswietlenia
app = Flask('kitchen-maintenance')
CORS(app)

class ProductAlreadyExists(Exception):
    pass

class ProductDoesNotExists(Exception):
    pass

class ProductDoesNotExist(Exception):
    pass


class Error(Exception):
    pass

class Product:

    def __init__(self, product_id, name, quantity):
        self.id = product_id
        self.name = name
        self.quantity = quantity




    #def change_quantity(self, quantity):
       # self.quantity += quantity

    #def change_name(self, new_name):
        #self.name = new_name



barcode_database = {}

class MyEncoder(JSONEncoder):
    def defoult(self, o):
        return o.__dict__

def save_to_json(dictionary):
    encoded = jsonpickle.encode(dictionary)

    with open("product_list.json", "w", encoding="utf-8") as file:
        json.dump(encoded, file)

def for_frontend(dane):
    dictionary = []
    for k, v in dane.items():
        dictionary.append(vars(v))
    return json.dumps(dictionary)






def open_json():
    with open("product_list.json", "r", encoding="utf-8") as file:
        encoded_data = json.load(file)

        aa = jsonpickle.decode(encoded_data)

        return aa

def check_if_product_in_database(name, data_base):
    for id, object in data_base.items():
        if object.name == name:
            return True
    return False


def check_barcode_in_database(barcode):
    list_of_products = open_json()
    if list_of_products.get(barcode) is None:
        raise ProductDoesNotExist
    result = update_product_quantity(barcode, quantity=1)
    if list_of_products.get(barcode) is None:
        raise Error

    return result

def add_product_with_barcode(barcode, product_name):
    list_of_products = open_json()
    if check_if_product_in_database(product_name, list_of_products):
        raise ProductAlreadyExists
    list_of_products.update({barcode: Product(barcode, product_name, 1)})
    if list_of_products.get(barcode) is None:
        raise Error
    save_to_json(list_of_products)
    return vars(list_of_products.get(barcode))

def add_product(product_name, quantity):
    list_of_products = open_json()
    if check_if_product_in_database(product_name, list_of_products):
            raise ProductAlreadyExists
    id = uuid.uuid4().__str__()
    list_of_products.update({id: Product(id, product_name, quantity)})
    if list_of_products.get(id) is None:
        raise Error
    save_to_json(list_of_products)

    return vars(list_of_products.get(id))

def delete(product_id):
    product_list = open_json()
    check_if_product_exist = product_list.get(product_id)
    if check_if_product_exist is None:
        raise ProductDoesNotExist
    if check_if_product_exist is not None:
        del product_list[product_id]
    save_to_json(product_list)
    return jsonify({product_id: "deleted"})

def change_name(product_id, former_name, new_name):
    product_list = open_json()
    if product_list.get(product_id) is None:
        raise ProductDoesNotExist
    if check_if_product_in_database(new_name, product_list):
        raise ProductAlreadyExists
    product_list[product_id].name = new_name

    if product_list[product_id].name != new_name:
        raise Error
    save_to_json(product_list)
    return {"id": product_id, "new_name": product_list[product_id].name, "former_name": former_name}

def update_product_quantity(product_id, quantity):
    product_list = open_json()
    if product_list.get(product_id) is None:
        raise ProductDoesNotExist
    quantity_to_change = product_list[product_id].quantity
    print("to change", quantity_to_change)
    product_list[product_id].quantity += quantity
    print("after, ", product_list[product_id].quantity)
    if product_list[product_id].quantity == quantity_to_change:
        raise Error
    save_to_json(product_list)
    return vars(product_list.get(product_id))


@app.route("/products/", methods=["GET"])
def get_product():
    plik = open_json()
    res = for_frontend(plik), 200
    return res


@app.route("/products/", methods=["POST"])
def create_product():
    data = request.json
    product_name = data.get('name')
    quantity = data.get('quantity')
    barcode = data.get("barcode")
    if barcode is not None and product_name is None:
        try:
            result = check_barcode_in_database(barcode)
        except ProductDoesNotExist:
            return "Not exist", 404
        return result, 201

    if barcode is not None and product_name is not None:
        try:
            result = add_product_with_barcode(barcode, product_name)
        except ProductAlreadyExists:
            return product_name + " already exists", 409
        except Error:
            return 500
        return result, 201

    if product_name is None or quantity is None:
        return 400
    try:
        result = add_product(product_name, quantity)
    except ProductAlreadyExists:
        return product_name + " already exists", 409
    except Error:
        return 500
    return result, 201

@app.route("/products/<id>", methods=["DELETE"])
def delete_product(id):
    product_id = id
    if product_id is None:
        return 422
    try:
        result_of_deleting = delete(product_id)
    except ProductDoesNotExist:
        return "Product does not exist", 422
    except Error:
        return 500

    return result_of_deleting, 200

@app.route("/products/<id>", methods=["PUT", "PATCH"])
def update_product(id):
    request_data = request.json
    product_id = id
    if product_id is None:
        return 422
    try:
        if request.method == "PUT":
            quantity = request_data.get('quantity')
            if quantity is None:
                return 422
            result = update_product_quantity(product_id, quantity)
        if request.method == "PATCH":
            name_to_change = request_data.get('name_to_change')
            new_name = request_data.get('new_name')
            if new_name is None or name_to_change is None:
                return 422
            result = change_name(product_id, name_to_change, new_name)
    except ProductAlreadyExists:
        return new_name + " already exists", 409
    except ProductDoesNotExist:
        return 404
    except Error:
        return 500
    return result, 201


app.run(host="0.0.0.0", port=int("8080"), debug=True)



#list_of_products.update({1: Product(1, "sug", 2)})
#list_of_products.update({2: Product(2, "milk", 3)})


#gg=jsonpickle.encode(list_of_products)
#print(gg)







#wynik = serializers.serialize(cc, related={'list': {'fields': ['a']}})


#ee=json.dumps(wynik, cls=ProductEncoder,  check_circular=True)
#print("encoded", ee)



#gg=json.loads(ee, object_hook=obiekt)
#print("obiekt", gg.list)

#cc= json.dumps(dane)
#print(cc)
#with open("product_list.json", "w", encoding="utf-8") as file:
  #  json.dump(dane, file, cls=ProductEncoder)

#with open("product_list.json", "r", encoding="utf-8") as file:
   # dd=json.load(file, cls=ProductDecoder)
    #xx=json.dumps(dd)
    #print(jsonpickle.decode(xx))
#print(json.loads(cc, cls=ProductDecoder))
#gg=jsonpickle.encode(Aa.list)
#print(gg)
#with open("product_list.json", "w", encoding="utf-8") as file:
    #json.dump(gg, file, cls=ProductEncoder)
#vv=jsonpickle.decode(gg)
#print(vv)

class Person:
    all_names = {}

    def __init__(self, name, val):
        self.name = name
        self.val = val
        Person.all_names.update({self.name: self})

joe = Person('Joe', 3)
bob = Person('Bob', 4)
print (vars(Person.all_names.get("Bob")))
## ['Joe', 'Bob']