from pydantic import BaseModel,Field,EmailStr,AliasChoices,field_validator
from typing import Literal
class RegistrationCreate(BaseModel):
    full_name:str=Field(min_length=2,max_length=120)
    mobile:str=Field(pattern=r'^\d{10}$')
    email:EmailStr|Literal['']=''
    city:str=Field(min_length=2,max_length=120,validation_alias=AliasChoices('preferred_branch','city'))
    qualification:str=Field(min_length=1,max_length=120)
    course_id:str=Field(min_length=2,max_length=80)
    preferred_batch:str=Field(min_length=2,max_length=120)
    training_mode:Literal['Online','Offline','Hybrid','Classroom','Online if available','Discuss with counsellor']
    message:str=Field(default='',max_length=2000)
    batch_id:str|None=Field(default=None,max_length=100)
    internship_id:str|None=Field(default=None,max_length=100)
    consent:bool
class EnquiryCreate(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    mobile:str=Field(pattern=r'^\d{10}$')
    email:EmailStr|Literal['']|None=None
    message:str=Field(min_length=2,max_length=2000)
    source:Literal['website','contact','course','batch','internship','chatbot']='website'
class LoginRequest(BaseModel):
    username:str=Field(min_length=1,max_length=120)
    password:str=Field(min_length=1,max_length=128)
class StatusUpdate(BaseModel):
    status:Literal['New','Contacted','In Process','Enrolled','Closed']
