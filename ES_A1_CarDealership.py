from flask import *
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

app = Flask(__name__)

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

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

dio_client = Client(email='dio@adventure.jp', password='TheWorld',
                    name='Dio Brando', district='London',
                    description='Za Warudo')

session.add(dio_client)
try:
    session.commit()
except Exception as e:
    session.rollback()
    print("Issue adding user to DB")
    print(e)


our_client = session.query(Client).filter_by(name='Dio Brando').first()
print(our_client)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/register/owner', methods=['GET', 'POST'])
def register_owner():
    return render_template('register_owner2.html')


@app.route('/api/user/owner')
def handle_owner():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        newOwner = Owner(email=email, password=password)
        session = Session()
        try:
            session.add(newOwner)
            session.commit()
        except Exception as e:
            session.rollback()
            return False
        return True


if __name__ == '__main__':
    app.run()