# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
from gluon import *
from gluon.tools import Auth
from gluon import request, DAL, response, session
#from plugin_sqleditable.editable import SQLEDITABLE


db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
auth = Auth(db)
#SQLEDITABLE.init()
REPORT_TITLE = ''
@auth.requires_membership('misofficer')
def index():
    grid=''
    form=SQLFORM.factory(Field('matric_number', label='Find Matric Number'))
    if form.accepts(request.vars, session):
        record=db.student(db.student.matric_no == form.vars.matric_number)
        if record != None:
            grid=SQLFORM(db.student, record)

        else:
            gride = None
            response.flash = 'No record found!'


    return dict(form=form, grid=grid)

@auth.requires_login()
def student_page():

    return locals()

def examrecord_page():

    return locals()

@auth.requires_membership('registry')
def addstudent():
    form=SQLFORM(db.student)

    if form.accepts(request.vars,session):
        response.flash = "Student " + form.vars.matric_no + " added"
        #redirect(URL('studentmanager'))
    elif form.errors:
        response.flash = str(form.errors)

    return dict(form=form)

@auth.requires_membership('admin')
def addschool():

    form=SQLFORM.grid(db.school, csv=True)
    return dict(form=form)

@auth.requires_membership('hod')
def department():

    return locals()

@auth.requires_membership('dean')
def add_dept():
    form=SQLFORM(db.department)
    return locals()

@auth.requires_membership('hod')
def man_dept():
    department = db.department(HOD=auth.user.id)
    form=SQLFORM.grid(db.program.department == department.id, csv=False,
                      maxtextlength=80

                      )
    return dict(form=form, department=department)

@auth.requires_membership('hod')
def add_course():
    department = db.department(HOD=auth.user.id)
    coursequery = db.course_subject.department == department.id
    form=SQLFORM.grid(coursequery, csv=False, maxtextlength=100)

    return dict(form=form)
@auth.requires_membership('hod')
def setcurriculum():
    department = db.department(HOD=auth.user.id)
    qry = db.course_curriculum.program.belongs(db.program.department==department.id)
    form=SQLFORM.grid(qry, orderby=db.course_curriculum.semester)

    return dict(form=form, department=department)

@auth.requires_membership('registry')
def studentmanager():

    form=SQLFORM.grid(db.student,
                      user_signature=True,
                      maxtextlength=50,
                      formstyle ='bootstrap3',
                      #fields=('matric_no', 'surname', 'service', 'program')

                      ) #create=False, editable=True)
    return locals()

################### Account Section #################################################################

@auth.requires_membership('account')
def afitpay():
    bankselect = SQLFORM.factory(
                Field('method_of_pay', requires=IS_IN_SET(['BankTeller', 'Etranzact'])) #default='BankTeller')
                )

    if bankselect.accepts(request.vars,session):
        if bankselect.vars.method_of_pay == 'BankTeller':
            response.flash = 'Bank Details'
            redirect(URL('bankpay'))

        elif bankselect.vars.method_of_pay == 'Etranzact':
            response.flash = 'etranzact details'
            redirect(URL('epay'))
        else:
            response.flash = 'error processing form inner'

    else:
        response.flash = 'select mode of payment'

    return locals()

@auth.requires_membership('account')
def bankpay():
    form = SQLFORM.grid(db.bank_pay,
                        maxtextlength=50

                        )
    return locals()

@auth.requires_membership('account')
def epay():
    form = SQLFORM.grid(db.etranzact,
                        maxtextlength=50

                        )
    return locals()
#####################Account Section End ########################
def load_curriculum(student_id, smester):
    course=db.registered_course
    curriculumdb = db.course_curriculum
    curriculums = db(curriculumdb.program == db.student(id=student_id).program)(curriculumdb.semester == smester).select()
    if curriculums:
        for curriculum in curriculums:
            course.insert(student=student_id, course_subject=curriculum.course_subject, credit_unit=curriculum.credit_unit, semester=curriculum.semester, sessions=CURRENT_SESSION, types='M', status='CP', scores=0.0)
    else:
        return None
#load results into archresults from registered_course
def load_result(student_id):
    course=db.archresult
    resultdb = db.registered_course
    results = db(resultdb.student == student_id).select()
    if results:
        for result in results:
            course.insert(student=result.student, course_subject=result.course_subject, credit_unit=result.credit_unit, semester=result.semester, sessions=result.sessions, types=result.types, status=result.status, scores=result.scores, grade=result.grade, wp=result.wp, Wgp=result.Wgp, remark=result.remark)
    else:
        return None
@auth.requires_membership('hod')
def load_main_courses():
    department = db.department(HOD=auth.user.id) or redirect(URL('reportnone'))
    form=SQLFORM.factory(Field('program', 'reference program', requires=IS_IN_DB(db(db.program.department==department.id), db.program.id, '%(name)s %(classification)s %(the_option)s')),
                         Field('semester', requires=IS_IN_SET(['1st', '2nd', '3rd', '4th']))

                         )
    #progs = db(db.program(id=form.vars.program).select())

    if form.process().accepts:
        studentss = db(db.student.program == form.vars.program).select()
        enrolleds = db(db.sessions_enrol.student.belongs(studentss)).select()

        for enrolled in enrolleds:
            load_curriculum(enrolled.student, form.vars.semester)

    else:
        response.flash = 'error'

    return dict(form=form, department=department)

def updatescore(regno,subject,score ):
    std = db.student(matric_no = regno)
    sub = db.course_subject(code=subject)

    if not std:
        return False
    elif not sub:
        return False
    else:
        getresult = db(db.registered_course.student == std.id)(db.registered_course.course_subject == sub.id).select().first()
        #getresult.update(scores=score)
        getresult.update_record(scores=score)

    return True


@auth.requires_membership('hod')
def updatescores():
    department = db.department(HOD=auth.user.id) or redirect(URL('reportnone'))
    form=SQLFORM.factory(Field('program', 'reference program', requires=IS_IN_DB(db(db.program.department==department.id), db.program.id, '%(name)s %(classification)s %(the_option)s')))
    if form.process().accepts:
        studentss = db(db.student.program == form.vars.program)._select(db.student.matric_no)
        raw_matrics = db(db.result_raw.student.belongs(studentss)).select()
        for matric in raw_matrics:
            updatescore(matric.student, matric.subject, matric.scores)

    return dict(form=form)




@auth.requires_membership('registry')
def loadresults():
    form=SQLFORM.factory(Field('student', 'reference student', requires=IS_IN_DB(db, db.student.id, '%(matric_no)s'))) #widget=SQLFORM.widgets.string))
    #progs = db(db.program(id=form.vars.program).select())

    if form.process().accepts:
        load_result(form.vars.student)


    else:
        response.flash = 'error'

    return dict(form=form)


@auth.requires_membership('registry')
def add_result():

    form = SQLFORM(db.registered_course)
    if form.accepts(request.vars,session):
       response.flash = 'result added'
    return dict(editable=form)


############ Helper Funcations ###############################


############### End Helper Function #############################


def checkmatric(form):
    query = db.student.matric_no == form.vars.matric_no
    if query == None:
        form.errors.matric_no = 'Number do not exist'

    else:
        redirect(URL('reportnone'))


@auth.requires_membership('hod')
def findresult():
    #REPORT-TITLE =
    department = db.department(HOD=auth.user.id)
    prgm = db(db.program.department == department.id).select()
    inputbox = SQLFORM.factory(Field('matric_no', 'reference student', requires=IS_IN_DB(db(db.student.program.belongs(prgm)), db.student.matric_no)),
                               #Field('semester', requires=IS_IN_SET(['1st', '2nd', '3rd', '4th'])),
                               Field('sessions', 'reference school_session', requires=IS_IN_DB(db,db.school_session.name, '%(name)s'))

                               )
    if inputbox.process().accepted:

        record = db.student(matric_no = inputbox.vars.matric_no) or redirect(URL('reportnone'))
        #sessn_record=db(db.school_session.name == inputbox.vars.sessions).select().first() or redirect(URL('default','reportnone'))
        sessn_record = db.school_session(name=inputbox.vars.sessions) or redirect(URL('default','reportnone'))
        redirect(URL('showresults', vars={'id_no':record.id,'sessn':inputbox.vars.sessions, 'sessn_id':sessn_record.id, 'rpt': 'RESULT SLIP'}))
    return dict(inputbox=inputbox)

@auth.requires_membership('hod')
def process_trans():
    form = SQLFORM.factory(Field('matric_no', requires=IS_NOT_EMPTY()),
                               Field('sessions', 'reference school_session', requires=IS_IN_DB(db,db.school_session.name, '%(name)s' ))

                               )
    if form.process().accepted:
        record = db.student(matric_no = form.vars.matric_no) or redirect(URL('reportnone'))
        sessn_record = db.school_session(name=form.vars.sessions) or redirect(URL('default','reportnone'))
        redirect(URL('showtranscript', vars={'id_no':record.id,'sessn':form.vars.sessions, 'sessn_id':sessn_record.id, 'rpt':'TRANSCRIPT'}))

    return dict(form=form)

@auth.requires_membership('registry')
def showresults():

    query = ((db.registered_course.student==request.vars.id_no) & (db.registered_course.sessions==request.vars.sessn_id))
    form = SQLFORM.grid(query, orderby=db.registered_course.semester) #crud.select(db.registered_course, query)

    return dict(form = form)

def showtranscript():
    query = db.archresult.student==request.vars.id_no #& (db.registered_course.sessions==request.vars.sessn_id))
    form = SQLFORM.grid(query, orderby=db.archresult.semester)

    return dict(form=form)

#@auth.requires_membership('registry')
def reportnone():
    message="Information does not exist"

    return locals() #dict(message=message)


#Define my apis here
@request.restful()
def api():
    response.view = 'generic.'+request.extension
    def GET(*args,**vars):
        patterns = 'auto'
        parser = db.parse_as_rest(patterns,args,vars)
        if parser.status == 200:
            return dict(content=parser.response)
        else:
            raise HTTP(parser.status,parser.error)
    def POST(table_name,**vars):
        return db[table_name].validate_and_insert(**vars)
    return locals()


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
