# Flask Server developed for Assignment 1 of the 2016
# Services Engineering course from the Masters in Informatics Engineering
# by Pedro Stamm
import time
from flask import *
from sqlalchemy import *
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

app = Flask(__name__)
app.secret_key = 'l\x07=J#\x160\xc9\xf46\x8c\xcc\xea\x85\xb9\x1d3\x93~>a\x9c\xc6:'

engine = create_engine('postgresql+pg8000://FlaskServer:ES2016@localhost:5432/ESDealership')
Base = declarative_base()


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


class Owner(Base):
    __tablename__ = 'owners'
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    cars = relationship("Car")
    dealerships = relationship("Dealership")

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


class Dealership(Base):
    __tablename__ = 'dealerships'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey('owners.id'))
    cars = relationship("Car", secondary=association_table)


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


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

# Example code
"""
ses = Session()

dio_client = Client(email='dio@adventure.jp', password='TheWorld',
                    name='Dio Brando', district='London',
                    description='Za Warudo')

ses.add(dio_client)
try:
    ses.commit()
except Exception as e:
    ses.rollback()
    print("Issue adding user to DB")
    print(e)

our_client = ses.query(Client).filter_by(name='Dio Brando').first()
print(our_client)

try:
    ses.delete(our_client)
    ses.commit()
    print("DIO WAS DELETED")
except Exception as e:
    ses.rollback()
    print("DIO LIVES")
    print(e)
"""


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


@app.route('/')
def index():
    if 'email' in session:
        if validate_login(session['email'], session['token'], session['type']):
            return "Logged in as %s" % escape(session['email'])
    return render_template('login.html')


@app.route('/owner/login')
def owner_login():
    return render_template('login_owner.html')


@app.route('/client/login')
def client_login():
    return render_template('login_client.html')


@app.route('/register/')
@app.route('/register/<type>')
def register(type=None):
    if type == 'client':
        return render_template('register_client.html')
    elif type == 'owner':
        return render_template('register_owner.html')
    return render_template('register.html')


# Everything API from here downwards


@app.route('/api/owner/', methods=['GET', 'POST', 'PUT'])
@app.route('/api/owner/<email>', methods=['GET'])
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
        if ('email' in session) and session['type'] == 'owner' and validate_login(session['email'], session['token'], session['type']):
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
        if 'email' in session and validate_login(session['email'], session['token'], session['type']):
            ses = Session()
            if email is None:
                result = ses.query(Owner)
                arr = []
                for r in result:
                    arr.append(json.dumps(r, cls=AlchemyEncoder))
                return Response(json.dumps(arr), mimetype='application/json', headers={'Cache-Control': 'no-cache'})
            else:
                result = ses.query(Owner).filter_by(email=email)
                return json.dumps(result.first(), cls=AlchemyEncoder)
        return jsonify(result="Unauthorized access")


@app.route('/api/owner/login', methods={'POST'})
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


@app.route('/api/owner/logout')
def logout_owner():
    if 'email' in session:
        session.pop('email', None)
        return redirect(url_for('index'))


@app.route('/api/client/', methods=['GET', 'POST', 'PUT'])
@app.route('/api/client/<email>', methods=['GET'])
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
        if 'email' in session and validate_login(session['email'], session['token'], session['type']):
            ses = Session()
            if email is None:
                result = ses.query(Client)
                arr = []
                for r in result:
                    arr.append(json.dumps(r, cls=AlchemyEncoder))
                return Response(json.dumps(arr), mimetype='application/json', headers={'Cache-Control': 'no-cache'})
            else:
                result = ses.query(Client).filter_by(email=email)
                return json.dumps(result.first(), cls=AlchemyEncoder)
        return jsonify(result="Unauthorized access");


@app.route('/api/client/login', methods={'POST'})
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


@app.route('/api/client/logout')
def logout_client():
    if 'email' in session:
        session.pop('email', None)
        session.pop('token', None)
        session.pop('type', None)
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
