# Initial schemas
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class UserSchema(BaseModel):
  id : int
  email : str
  
  created_at : datetime
  updated_at : datetime

  class Meta:
    from_attributes = True
class UserCreateSchema(BaseModel):
  email : str
  password : str

class ExpenseSchema(BaseModel):
  id : int
  amount : float

  user_id : int
  category_id : int 

  transaction_date : datetime
  created_at : datetime
  
  note: str

  class Meta:
    from_attributes = True
    
class ExpenseCreateSchema(BaseModel):
  amount : int
  user_id : int
  category : id
  transaction_date : datetime
  note : str
  
class CategorySchema(BaseModel):
  id : int
  name : str
  # TODO define color icon format -> color -> hex / icon -> url for svg/png?
  # TODO check if this table need the creaed_at and updated_at field as required at project_scope file, item #3
  color : Optional[str]
  icon : Optional[str]
  class Meta:
    from_attributes = True

class CategoryCreateSchema(BaseModel):
  name : str
  color : Optional[str]
  icon : Optional[str]
  

class BudgetSchema(BaseModel):
  id : int
  amount_limit : Decimal

  created_at : datetime
  budget_date : datetime 

  user_id : int
  category_id : Optional[int]

  class Meta:
    from_attributes = True

class BudgetCreateSchema(BaseModel):
  budget_date : datetime
  user_id : int
  category_id : Optional[int]