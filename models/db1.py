# coding: utf8
from gluon import *
from gluon.tools import Auth
from gluon import request, DAL, response, session

#from plugin_lazy_options_widget import lazy_options_widget
from plugin_suggest_widget import suggest_widget
from cascadedrop import CascadingSelect
from gluon.contrib.populate import populate

db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
auth = Auth(db)

db.define_table('school',
                Field('name', requires=IS_NOT_EMPTY()),
                auth.signature,
                format='%(name)s'
                )


db.define_table('department',
                Field('school', db.school), #, requires=IS_IN_DB(db, db.school.id, '%(name)s')),
                Field('name', requires=IS_NOT_EMPTY()),
                Field('HOD', 'reference auth_user'),
                auth.signature,
                format='%(name)s'
                )
db.define_table('program',
                Field('department', 'reference department'),
                Field('classification', requires=IS_IN_SET(['ND', 'HND', 'PRE-ND', 'PGD','NON-ND'])),
                Field('the_option', label='Option'),
                Field('name', requires=IS_NOT_EMPTY()),
                Field('fullname'),
                auth.signature,
                format='%(name)s'
                )

db.define_table('course_subject',
                Field('department', 'reference department'), #requires=IS_IN_DB(db.department.HOD, db.department, '%(name)s')),
                Field('title'),
                Field('code'),
                #auth.signature,
                 format='%(code)s'
                )

                
db.define_table('course_curriculum',
                Field('program', 'reference program'), #requires=IS_IN_DB(db, db.program.id, '%(name)s')),
                Field('course_subject', 'reference course_subject'), #requires=IS_IN_DB(db, db.course_subject.id, '%(code)s')),
                Field('semester', requires=IS_IN_SET(['1st', '2nd', '3rd', '4th'])),
                Field('levels', requires=IS_IN_SET(['Year-1', 'Year-2', 'Year-3', 'Year-4'])),
                Field('credit_unit', 'integer'),
                auth.signature,
                format='%(course_subject)s'
                
                )
db.course_curriculum.course_subject.widget = SQLFORM.widgets.autocomplete(request, db.course_subject.code, id_field=db.course_subject.id)

db.define_table('ngstate',
                Field('name'),
                format='%(name)s',
                )
db.define_table('lga',
                Field('ngstate', 'reference ngstate'),
                Field('name'),
                format='%(name)s',
                )


    
db.define_table('student',
                Field('matric_no', unique=True),
                Field('surname', requires=IS_NOT_EMPTY()),
                Field('firstname', requires=IS_NOT_EMPTY()),
                Field('lastname'),
                Field('service', comment='For civilians indicate employer'),
                Field('last_unit', comment='For civilians indicate last place of employement'),
                Field('rankk', label='Rank', comment='if applicable', default = 'None'),
                Field('marital', requires=IS_IN_SET(['Married', 'Single'])),
                Field('birth_day', 'date'),
                Field('nationality', requires=IS_IN_SET(['Nigerian', 'West Africa', 'International'])),
                Field('state_origin', comment='requires drop down'),
                Field('lga', 'reference lga'),
                Field('blood_group', requires=IS_IN_SET(['O', 'A', 'B'])),
                Field('phone_no', unique=True),
                Field('email', requires=IS_EMAIL()),
                Field('sex', requires=IS_IN_SET(['Male', 'Female']), widget=SQLFORM.widgets.radio.widget),
                #Field('program_of_study', requires=IS_IN_SET(['pre-ND','ND','pre-HND', 'HND', 'PGD'])),
                Field('program', 'reference program', label='Program_of_study'), 
                Field('school_level', requires=IS_IN_SET(['NDI', 'NDII', 'HNDI', 'HNDII', 'PGD'])),
                Field('photo', 'upload'),
                auth.signature,
                format='%(matric_no)s'
                )
cascade=CascadingSelect(db.department, db.program)
cascade.prompt = lambda table: "--choose "  + ("an " if str(table)[0] in 'aeiou' else "a ") + str(table) + "--"
db.student.program.widget = cascade.widget



db.define_table('school_session',
                Field('name', requires=IS_NOT_EMPTY()),
                Field('session_begin', 'date'),
                Field('session_close', 'date'),
                Field('status',requires=IS_IN_SET(['Open','Closed'])),
                auth.signature,
                format = '%(name)s'
                
                )
db.define_table('sessions_enrol',
                Field('student', 'reference student'),
                Field('sessions', 'reference school_session')
                )
db.sessions_enrol.sessions.requires=IS_NOT_IN_DB(db(db.sessions_enrol.student==request.vars.student), 'sessions_enrol.sessions')


def calcgradeII(m):
    #m = row.registered_course.scores
    if m>69 and m<101:
        t = 'A', 4, 'Excellent'
        return t
    elif m>64 and m<70:
        t = 'AB', 3.5, 'Very Good'
        return t
    elif m>59 and m<65:
        t = 'B', 3, 'Good'
        return t
    elif m>54 and m<60:
        t = 'BC', 2.75, 'Fairly Good'
        return t
    elif m>49 and m<55:
        t = 'C', 2.50, 'Very Fair'
        return t
    elif m>44 and m<50:
        t = 'CD', 2.25, 'Fair'
        return t
    elif m>39 and m<45:
        t = 'D', 2.0, 'Just Fair'
        return t
    elif m>=0 and m<40:
        t = 'E', 0, 'Fail'
        return t
    else:
       t='Nil', -1, 'No-Result'
       return t
    
STATUS_SET = ['ABS', 'NT', 'EM,', 'AE', 'PI', 'NA', 'SK','CO','CP', 'IS', 'EX', 'NR', 'DE']
CURRENT_SESSION = 5

db.define_table('registered_course',
                Field('student', 'reference student'),
                Field('course_subject', 'reference course_subject'),
                Field('credit_unit', 'float', default = 0.0),
                Field('semester', requires=IS_IN_SET(['1st', '2nd', '3rd', '4th'])),
                Field('sessions', 'reference school_session'),
                Field('types', requires=IS_IN_SET(['M', 'CO', 'EL'], zero=('--choose type--'))),
                Field('status', requires=IS_IN_SET(STATUS_SET)),
                Field('scores', 'float', default=0.0),
                Field('grade', readable=True, compute=lambda r: calcgradeII(r['scores'])[0] ),
                #Field.Virtual('grade', lambda row: calcgradeII(row)[0]), 
                Field('wp', 'float',compute=lambda r: calcgradeII(r['scores'])[1]),
                #Field.Virtual('wp', lambda row: calcgradeII(row)[1]),
                Field('Wgp', 'float', compute=lambda r: r['credit_unit']*r['wp']),
                #Field.Virtual('Wgp', lambda row: row.registered_course.credit_unit*row.registered_course.wp),
                Field('remark', readable=True, compute=lambda r: calcgradeII(r['scores'])[2] )
                #Field.Virtual('remark', lambda row: calcgradeII(row)[2]),
                )
db.registered_course.student.widget = SQLFORM.widgets.autocomplete(request, db.student.matric_no, id_field=db.student.id)
db.registered_course.course_subject.widget = SQLFORM.widgets.autocomplete(request, db.course_subject.code, id_field=db.course_subject.id)

db.define_table('result_raw',
                Field('student'),
                Field('sessions'),
                Field('semester'),
                Field('subject'),
                Field('scores', 'float'),
                )





#query=db(db.registered_course.student == student_id)
#db.registered_course.course_subject.requires=IS_NOT_IN_DB(db(db.registered_course.student == (lambda row: row.student)), db.registered_course.course_subject)
db.define_table('archresult',
               Field('student', 'reference student'),
               Field('course_subject', 'reference course_subject'),
               Field('credit_unit', 'float', default=2.0), 
               Field('semester', requires=IS_IN_SET(['1st', '2nd', '3rd', '4th'])),
               Field('sessions', 'reference school_session'),
               Field('types', requires=IS_IN_SET(['M', 'CO', 'EL'], zero=('--choose type--'))),
               Field('status', requires=IS_IN_SET(STATUS_SET)),
               Field('scores', 'float', default=56.0),
               Field('grade'), #lambda row: calcgradeII(row)[0]), 
               #Field('grade', readable=True, compute=lambda r: calcgradeII(r['scores'])[0] ),
               Field('wp', 'float'), #lambda row: calcgradeII(row)[1]),
               #Field('wp', 'float',compute=lambda r: calcgradeII(r['scores'])[1]),
               Field('Wgp', 'float'), # lambda row: row.registered_course.credit_unit*row.registered_course.wp),
               #Field('Wgp', 'float', compute=lambda r: r['credit_unit']*r['wp']),
               Field('remark'), #lambda row: calcgradeII(row)[2]),
               #Field('remark', readable=True, compute=lambda r: calcgradeII(r['scores'])[2] ),
               
               )

db.archresult.student.widget = SQLFORM.widgets.autocomplete(request, db.student.matric_no, id_field=db.student.id)
db.archresult.course_subject.widget = SQLFORM.widgets.autocomplete(request, db.course_subject.code, id_field=db.course_subject.id)

#populate(db.archresult,100)

LIST_ENCUMB = ['repeat', 'absent', 'sick', 'travelled', 'exam-malpractise']

db.define_table('encumbrance',
                Field('student', requires=IS_IN_DB(db, db.student.id)),
                Field('name'),
                Field('sessions', 'reference school_session'),
                Field('semester', requires=IS_IN_SET(['1st', '2nd', '3rd', '4th'])),
                )
def load_curriculum(student_id):
    course=db.registered_course
    curriculumdb = db.course_curriculum
    curriculums = db(curriculumdb.program == db.student(id=student_id).program).select()
    if curriculums:
        for curriculum in curriculums:
            course.insert(student=student_id, course_subject=curriculum.course_subject, credit_unit=curriculum.credit_unit, semester=curriculum.semester, sessions=CURRENT_SESSION, types='M', status='CP', scores=0.0)
    else:
        return None
    
    
def remark(cgp):
    
    if cgp>3.49 and cgp<4:
        return 'Distinction'
    elif cgp>2.99 and cgp<3.50:
        return 'Upper Credit'
    elif cgp>2.49 and cgp<3.00:
        return 'Lower Credit'
    elif cgp>1.99 and cgp<2.50:
        return 'Pass'
    else:
        return 'fail'
