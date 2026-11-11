from datetime import date, time
from typing import Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict

class Content(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$', max_length=100)
    name: str = Field(min_length=2,max_length=160)
    status: Literal['draft','published','archived','cancelled'] = 'draft'
    description: str = Field(default='', max_length=5000)
    full_description: str = Field(default='', max_length=20000)
    categories: list[str] = Field(default_factory=list,max_length=20)
    tags: list[str] = Field(default_factory=list,max_length=50)
    modules: list[str] = Field(default_factory=list,max_length=100)
    featured: bool = False
    level: str|None = None
    technology_logo: str = Field(default='',max_length=500)
    image: str = Field(default='',max_length=1000)
    duration: str = Field(default='',max_length=120)
    duration_value: int|None = Field(default=None,ge=1)
    duration_unit: Literal['Days','Weeks','Months'] = 'Weeks'
    eligibility: str = Field(default='',max_length=2000)
    training_modes: list[str] = Field(default_factory=list,max_length=3)
    display_order: int = Field(default=0,ge=0)
    course_id: str|None = None
    start_date: date|None = None
    end_date: date|None = None
    start_time: time|None = None
    end_time: time|None = None
    schedule_days: list[str] = Field(default_factory=list,max_length=7)
    training_mode: Literal['Online','Offline','Hybrid'] = 'Offline'
    branch: Literal['','Tarnaka','Boduppal','Mallapur'] = ''
    timing: str = Field(default='',max_length=120)
    batch_code: str = Field(default='',max_length=100)
    trainer: str = Field(default='',max_length=200)
    mentor: str = Field(default='',max_length=500)
    available_seats: int|None = Field(default=None,ge=0)
    capacity: int|None = Field(default=None,ge=0)
    fees: str = Field(default='',max_length=120)
    closing_date: date|None = None
    applications_open: bool = True
    instructions: str = Field(default='',max_length=4000)
    skills_required: list[str] = Field(default_factory=list,max_length=50)
    skills_learned: list[str] = Field(default_factory=list,max_length=50)
    technologies: list[str] = Field(default_factory=list,max_length=50)
    projects: str = Field(default='',max_length=5000)
    outcomes: list[str] = Field(default_factory=list,max_length=50)
    certificate: bool = False

    @model_validator(mode='after')
    def dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError('End date must not precede start date')
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError('End time must be later than start time')
        if self.capacity is not None and self.available_seats is not None and self.available_seats > self.capacity:
            raise ValueError('Available seats cannot exceed capacity')
        if self.image and not self.image.startswith(('https://','/')):
            raise ValueError('Image must use HTTPS or a local asset path')
        return self
