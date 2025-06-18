from sqlalchemy import Column, Integer, String, Date
from database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Integer)
    production_date = Column(Date)
    expiration_date = Column(Date)

class Weather(Base):
    __tablename__ = "weather"
    id = Column(Integer, primary_key=True, index=True)
    weather_date = Column(Date)
    weather_info = Column(String)
