from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///finbiz.db')
Session = sessionmaker(bind=engine)

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    cin = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    industry = Column(String(255))
    incorporation_year = Column(Integer)
    status = Column(String(50))
    address = Column(Text)
    financials = relationship('Financial', back_populates='company')
    directors = relationship('Director', back_populates='company')
    charges = relationship('Charge', back_populates='company')

class Financial(Base):
    __tablename__ = 'financials'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    turnover = Column(Float)
    net_profit = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    year = Column(Integer, nullable=False)
    company = relationship('Company', back_populates='financials')

class Director(Base):
    __tablename__ = 'directors'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    name = Column(String(255), nullable=False)
    designation = Column(String(255))
    din = Column(String(50))
    company = relationship('Company', back_populates='directors')

class Charge(Base):
    __tablename__ = 'charges'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    charge_amount = Column(Float)
    status = Column(String(50))
    charge_holder = Column(String(255))
    company = relationship('Company', back_populates='charges')
