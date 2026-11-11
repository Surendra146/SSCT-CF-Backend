from fastapi import APIRouter, HTTPException
from ..schemas.register import RegistrationCreate, EnquiryCreate
from ..core.db import execute
from ..core.content import validate_selection
router = APIRouter(prefix='/api', tags=['public'])

@router.post('/registrations', status_code=201)
async def register(data: RegistrationCreate):
    if not data.consent:
        raise HTTPException(422, 'Consent is required')
    await validate_selection(data)
    id = await execute('INSERT INTO registrations(full_name,mobile,email,city,qualification,course_id,preferred_batch,training_mode,message,batch_id,internship_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)', (data.full_name, data.mobile, data.email, data.city, data.qualification, data.course_id, data.preferred_batch, data.training_mode, data.message, data.batch_id, data.internship_id))
    return {'id': id, 'message': 'Registration submitted'}

@router.post('/enquiries', status_code=201)
async def enquiry(data: EnquiryCreate):
    id = await execute('INSERT INTO enquiries(name,mobile,email,message,source) VALUES(?,?,?,?,?)', (data.name, data.mobile, str(data.email) if data.email else '', data.message, data.source))
    return {'id': id, 'message': 'Enquiry received'}
