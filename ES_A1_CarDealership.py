# Flask Server developed for Assignment 1 of the 2016
# Services Engineering course from the Masters in Informatics Engineering
# by Pedro Stamm
import time
from flask import *
from sqlalchemy import *
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

application = Flask(__name__)
application.secret_key = 'l\x07=J#\x160\xc9\xf46\x8c\xcc\xea\x85\xb9\x1d3\x93~>a\x9c\xc6:'

# Initializing DB engine
engine = create_engine(
    'postgresql+pg8000://FlaskServer:ES2016@mydbinstance.c47cb5fr7nsn.eu-central-1.rds.amazonaws.com:5432/ESDealership')
Base = declarative_base()


# Data-structure for DB
class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    district = Column(String, nullable=False)
    description = Column(String)

    def __repr__(self):
        return "<Client(id='%s', email='%s', password='%s', name='%s', district='%s', description='%s'>" % (
            self.id, self.email, self.password, self.name, self.district, self.description
        )

    @property
    def serialize(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'description': self.description,
        }


class Owner(Base):
    __tablename__ = 'owners'
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    cars = relationship("Car", cascade="save-update, delete")
    dealerships = relationship("Dealership", cascade="save-update, delete")

    def __repr__(self):
        return "<Owner(id='%s', email='%s', password='%s', name='%s', description='%s'>" % (
            self.id, self.email, self.password, self.name, self.description)


association_table = Table('dealer_car', Base.metadata,
                          Column('dealer_id', Integer, ForeignKey('dealerships.id')),
                          Column('car_id', Integer, ForeignKey('cars.id')))


class Car(Base):
    __tablename__ = 'cars'
    id = Column(Integer, primary_key=True)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    kilometers = Column(Integer, nullable=False)
    district = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    fuel = Column(String, nullable=False)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey('owners.id'))
    dealerships = relationship("Dealership", secondary=association_table)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'brand': self.brand,
            'model': self.model,
            'kilometers': self.kilometers,
            'district': self.district,
            'price': self.price,
            'fuel': self.fuel,
            'description': self.description,
            'owner_id': self.owner_id,
            'dealerships': self.serialize_many2many
        }

    @property
    def serialize_many2many(self):
        return [item.serialize for item in self.dealerships]


class Dealership(Base):
    __tablename__ = 'dealerships'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey('owners.id'))
    cars = relationship("Car", secondary=association_table)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'cars': self.serialize_many2many
        }

    @property
    def serialize_many2many(self):
        return [item.serialize for item in self.cars]


# Convert Alchemy query Result to JSON
# Taken from http://stackoverflow.com/questions/5022066/how-to-serialize-sqlalchemy-result-to-json
class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)  # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


# Create tables, if not already there
Base.metadata.create_all(engine)
# Prepare sessionmaker
Session = sessionmaker(bind=engine)


def validate_login(email, token, type):
    ses = Session()
    if type == 'client':
        r = ses.query(Client).filter_by(email=email).first()
        if r and r.email == email:
            return True
    if type == 'owner':
        r = ses.query(Owner).filter_by(email=email).first()
        if r and r.email == email:
            return True
    return False


# Web app code from here downwards

@application.route('/')
def index():
    if 'email' in session:
        if validate_login(session['email'], session['token'], session['type']):
            if session['type'] == 'client':
                return redirect(url_for('client_dash'))
            elif session['type'] == 'owner':
                return redirect(url_for('owner_dash'))
    return render_template('login.html')


@application.route('/owner/login/')
def owner_login():
    return render_template('login_owner.html')


@application.route('/owner/dash/')
def owner_dash():
    if 'email' in session:
        if (session['type'] == 'owner') and validate_login(session['email'], session['token'], session['type']):
            return render_template('owner_dash.html')
    return redirect(url_for('index'))


@application.route('/owner/manage')
def owner_manage():
    if 'email' in session:
        if (session['type'] == 'owner') and validate_login(session['email'], session['token'], session['type']):
            return render_template('owner_manage.html')
    return redirect(url_for('index'))


@application.route('/owner/manage/<name>')
def owner_manage_dealer(name):
    if 'email' in session:
        if (session['type'] == 'owner') and validate_login(session['email'], session['token'], session['type']):
            ses = Session()
            res = ses.query(Owner).filter_by(email=session['email']).first()
            res2 = ses.query(Dealership).filter_by(name=name).first()
            if res.id == res2.owner_id:
                return render_template('dealership_manage.html', deal=name)
            else:
                redirect(url_for('owner_manage'))
    return redirect(url_for('index'))


@application.route('/owner/listclients')
def owner_list_clients():
    if 'email' in session:
        if (session['type'] == 'owner') and validate_login(session['email'], session['token'], session['type']):
            return render_template("owner_clientlist.html")
    return redirect(url_for('index'))


@application.route('/client/login/')
def client_login():
    return render_template('login_client.html')


@application.route('/client/dash/')
def client_dash():
    if 'email' in session:
        if (session['type'] == 'client') and validate_login(session['email'], session['token'], session['type']):
            return render_template('client_dash.html')
    return redirect(url_for('index'))


@application.route('/register/')
@application.route('/register/<type>/')
def register(type=None):
    if type == 'client':
        return render_template('register_client.html')
    elif type == 'owner':
        return render_template('register_owner.html')
    return render_template('register.html')


# Everything API from here downwards


@application.route('/api/owner', methods=['GET', 'POST', 'PUT'])
@application.route('/api/owner/<email>', methods=['GET'])
def handle_owner(email=None):
    if request.method == 'POST':
        print("Received POST request")
        data = request.form.to_dict()
        email = data['email']
        password = data['password']
        name = data['name']
        description = data['description']
        newOwner = Owner(email=email, password=password, name=name, description=description)
        ses = Session()
        try:
            ses.add(newOwner)
            ses.commit()
            print("Owner " + name + " added to database")
            return jsonify(
                result="Owner added",
                bool=True
            )
        except Exception as e:
            ses.rollback()
            print("Issue adding Owner to DB")
            print(e)
            return jsonify(
                result="Failed to add Owner",
                bool=False
            )
    if request.method == 'PUT':
        if ('email' in session) and session['type'] == 'owner' and validate_login(session['email'], session['token'],
                                                                                  session['type']):
            data = request.form.to_dict()
            password = data['password']
            name = data['name']
            description = data['description']
            ses = Session()
            res = ses.query(Owner).filter_by(email=session['email']).first()
            res.name = name
            if password:
                res.password = password
            res.description = description
            try:
                ses.commit()
                print("Owner " + name + " updated")
                return jsonify(
                    result="Owner updated",
                    bool=True
                )
            except Exception as e:
                ses.rollback()
                print("Issue updating Owner")
                print(e)
                return jsonify(
                    result="Failed to update Owner",
                    bool=False
                )
        return jsonify(result="Unauthorized access");
    if request.method == 'GET':
        if ('email' in session) and session['type'] == 'owner' and validate_login(session['email'], session['token'],
                                                                                  session['type']):
            ses = Session()
            if email is None:
                result = ses.query(Owner)
                arr = []
                for i in result:
                    arr.append(i.serialize)
                return json.dumps(arr)
            else:
                result = ses.query(Owner).filter_by(email=email)
                return json.dumps(result.first(), cls=AlchemyEncoder)
        return jsonify(result="Unauthorized access")


@application.route('/api/owner/login', methods={'POST'})
def login_owner():
    if request.method == 'POST':
        data = request.form.to_dict()
        email = data['email']
        password = data['password']
        ses = Session()
        res = ses.query(Owner).filter_by(email=email).first()
        if res and password == res.password:
            session['email'] = email
            session['token'] = int(time.time() * 1000)
            session['type'] = 'owner'
            return jsonify(login=True)
        return jsonify(login=False)


@application.route('/api/owner/logout')
def logout_owner():
    session.pop('email', None)
    return jsonify(logout=True)


@application.route('/api/client', methods=['GET', 'POST', 'PUT', 'DELETE'])
@application.route('/api/client/<email>', methods=['GET'])
def handle_client(email=None):
    if request.method == 'POST':
        print("Received POST request")
        data = request.form.to_dict()
        email = data['email']
        password = data['password']
        name = data['name']
        district = data['district']
        description = data['description']
        newClient = Client(email=email, password=password, name=name, district=district, description=description)
        ses = Session()
        try:
            ses.add(newClient)
            ses.commit()
            print("Client " + name + " added to database")
            return jsonify(
                result="Client added",
                bool=True
            )
        except Exception as e:
            ses.rollback()
            print("Issue adding Client to DB")
            print(e)
            return jsonify(
                result="Failed to add Client",
                bool=False
            )
    if request.method == 'PUT':
        if ('email' in session) and session['type'] == 'client' and validate_login(session['email'], session['token'],
                                                                                   session['type']):
            data = request.form.to_dict()
            password = data['password']
            name = data['name']
            district = data['district']
            description = data['description']
            ses = Session()
            res = ses.query(Client).filter_by(email=session['email']).first()
            res.name = name
            if password:
                res.password = password
            res.district = district
            res.description = description
            try:
                ses.commit()
                print("Client " + name + " updated")
                return jsonify(
                    result="Client updated",
                    bool=True
                )
            except Exception as e:
                ses.rollback()
                print("Issue updating Client")
                print(e)
                return jsonify(
                    result="Failed to update Client",
                    bool=False
                )
        return jsonify(result="Unauthorized access");
    if request.method == 'DELETE':
        if ('email' in session) and session['type'] == 'client' and validate_login(session['email'], session['token'],
                                                                                   session['type']):
            ses = Session()
            res = ses.query(Client).filter_by(email=session['email']).first()
            try:
                ses.delete(res)
                ses.commit()
                print("Client " + session['email'] + " deleted")
                session.pop('email', None)
                session.pop('token', None)
                session.pop('type', None)
                return jsonify(
                    result="Client deleted",
                    bool=True
                )
            except Exception as e:
                ses.rollback()
                print("Issue deleting Client")
                print(e)
                return jsonify(
                    result="Failed to delete Client",
                    bool=False
                )
    if request.method == 'GET':
        if 'email' in session and validate_login(session['email'], session['token'], session['type']):
            ses = Session()
            if email is None:
                result = ses.query(Client)
                arr = []
                for i in result:
                    arr.append(i.serialize)
                return json.dumps(arr)
            else:
                result = ses.query(Client).filter_by(email=email)
                return json.dumps(result.first(), cls=AlchemyEncoder)
        return jsonify(result="Unauthorized access");


@application.route('/api/client/login', methods={'POST'})
def login_client():
    if request.method == 'POST':
        data = request.form.to_dict()
        email = data['email']
        password = data['password']
        ses = Session()
        res = ses.query(Client).filter_by(email=email).first()
        if res and password == res.password:
            session['email'] = email
            session['token'] = int(time.time() * 1000)
            session['type'] = 'client'
            return jsonify(login=True)
        return jsonify(login=False)


@application.route('/api/client/logout')
def logout_client():
    if 'email' in session:
        session.pop('email', None)
        session.pop('token', None)
        session.pop('type', None)
        return redirect(url_for('index'))


@application.route('/api/ownerdealership', methods=['GET'])
def handle_dealership_owner():
    if ('email' in session) and session['type'] == 'owner' and validate_login(session['email'], session['token'],
                                                                              session['type']):
        ses = Session()
        curowner = ses.query(Owner).filter_by(email=session['email']).first()
        res = ses.query(Dealership).filter_by(owner_id=curowner.id).order_by(Dealership.name)
        arr = []
        for i in res:
            arr.append(i.serialize)
        return json.dumps(arr)


@application.route('/api/dealership', methods=['GET', 'POST'])
@application.route('/api/dealership/<name>', methods=['GET', 'PUT'])
def handle_dealership(name=None):
    if ('email' in session) and session['type'] == 'owner' and validate_login(session['email'], session['token'],
                                                                              session['type']):
        if request.method == 'POST':
            print("Received POST request")
            data = request.form.to_dict()
            name = data['name']
            description = data['description']
            ses = Session()
            owner = ses.query(Owner).filter_by(email=session['email']).first()
            newDeal = Dealership(name=name, description=description, owner_id=owner.id)
            try:
                ses.add(newDeal)
                ses.commit()
                print("Dealership " + name + " added to database")
                return jsonify(
                    result="Dealership added",
                    bool=True
                )
            except Exception as e:
                ses.rollback()
                print("Issue adding Dealership to DB")
                print(e)
                return jsonify(
                    result="Failed to add Dealership",
                    bool=False
                )
        if request.method == 'PUT':
            data = request.form.to_dict()
            newname = data['name']
            description = data['description']
            ses = Session()
            curOwner = ses.query(Owner).filter_by(email=session['email']).first()
            res = ses.query(Dealership).filter_by(name=name).first()
            if res.owner_id == curOwner.id:
                res.name = newname
                res.description = description
                try:
                    ses.commit()
                    print("Dealership " + name + " updated")
                    return jsonify(
                        result="Dealership updated",
                        newname=newname,
                        bool=True
                    )
                except Exception as e:
                    ses.rollback()
                    print("Issue updating Dealership")
                    print(e)
                    return jsonify(
                        result="Failed to update Dealership",
                        bool=False
                    )
        if request.method == 'GET':
            ses = Session()
            if name is None:
                result = ses.query(Dealership).order_by(Dealership.name)
                arr = []
                for i in result:
                    arr.append(i.serialize)
                return json.dumps(arr)
            else:
                result = ses.query(Dealership).filter_by(name=name)
                return json.dumps(result.first(), cls=AlchemyEncoder)
    return jsonify(result="Unauthorized access");


@application.route('/api/car', methods=['GET', 'POST'])
@application.route('/api/car/<id>', methods=['GET', 'PUT', 'DELETE'])
def handle_car():
    if ('email' in session) and session['type'] == 'owner' and validate_login(session['email'], session['token'],
                                                                              session['type']):
        if request.method == 'POST':
            print("Received POST request")
            data = request.form.to_dict()
            brand = data['brand']
            model = data['model']
            kilometers = data['kilometers']
            district = data['district']
            price = data['price']
            fuel = data['fuel']
            description = data['description']
            ses = Session()
            owner = ses.query(Owner).filter_by(email=session['email']).first()
            newCar = Dealership(brand=brand, model=model, kilometers=kilometers,
                                district=district, price=price, fuel=fuel,
                                description=description, owner_id=owner.id)
            try:
                ses.add(newCar)
                ses.commit()
                print("Car " + brand + " added to database")
                return jsonify(
                    result="Car added",
                    bool=True
                )
            except Exception as e:
                ses.rollback()
                print("Issue adding Car to DB")
                print(e)
                return jsonify(
                    result="Failed to add Car",
                    bool=False
                )


def fibonacci(n):
    if n <= 2:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)


@application.route('/computefibonacci')
def httpfibonacci():
    try:
        n = int(request.args['n'])
    except:
        return 'Wrong arguments', 200
    return 'Fibonacci(' + str(n) + ') = ' + str(fibonacci(n))


if __name__ == '__main__':
    application.run()
# debug=True
