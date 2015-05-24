# coding: utf8
# try something like
#app_root/controllers/your_controller.py
import math
from gluon import *
from gluon.tools import Auth
from gluon import request, DAL, response, session
db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
auth = Auth(db)

def resultreport():
    #message= request.args[:5]
    student_id = request.vars.id_no
    smester = request.vars.sem
    sessn = request.vars.sessn

    student = db.student(student_id)
    result = db((db.registered_course.student==student_id) & (db.registered_course.sessions==request.vars.sessn_id)).select()
    semesters = db((db.registered_course.student==student_id) & (db.registered_course.sessions==request.vars.sessn_id)).select(db.registered_course.semester, distinct=True)
    departid = db.program(student.program).department
    progname = db.program(student.program).fullname
    schoolid = db.department(departid).school

    return dict(student=student, results=result, sessn = sessn, departid=departid, schoolid=schoolid, smester=smester, semesters=semesters, program=progname)

def transcriptor():
     #message= request.args[:5]
    student_id = request.vars.id_no
    smester = request.vars.sem
    sessn = request.vars.sessn

    student = db.student(student_id)
    query = db.archresult.student == student.id
    result = db(query).select()
    semesters = db(query).select(db.archresult.semester, db.archresult.sessions, distinct=True)
    departid = db.program(student.program).department
    progname = db.program(student.program).fullname
    schoolid = db.department(departid).school

    return dict(student=student, results=result, sessn = sessn, departid=departid, schoolid=schoolid, smester=smester, semesters=semesters, program=progname)
@auth.requires_membership('hod')
def getdeptsession():
    depart = db.department(HOD=auth.user.id)

    inputform = SQLFORM.factory(Field('department', 'reference department', requires=IS_IN_DB(db(db.department.id==depart.id), db.department.name)),
                                Field('session', 'reference school_session', requires=IS_IN_DB(db, db.school_session.name, '%(name)s')),
                                Field('levels', requires=IS_IN_SET(['NDI', 'NDII', 'HNDI', 'HNDII', 'PGD'])),
                                )
    if inputform.process().accepted:
        #departid = db.department(name=inputform.vars.department).id or redirect(URL(c='default', f='reportnone'))
        departid = depart.id
        sessionid = db.school_session(name=inputform.vars.session).id or redirect(URL(c='default', f='reportnone'))
        levels = inputform.vars.levels

        redirect(URL('resultlistperdept', vars={'departid':departid, 'sessionid':sessionid, 'levels':levels, 'rpt':'RESULT LISTS' }))
        #response.flash ="Good"
    else:
        response.flash = "error"
    return dict(form=inputform)
@auth.requires_membership('hod')
def resultlistperdept():
    #Get all programs in the department referenced by vars.departid
    programs=db(db.program.department == request.vars.departid).select()
    #Get all students belonging to all programs in the department
    studentlistA = db(db.student.program.belongs(programs)).select()
    #Get all students who enrolled from the students referenced by studentlistA
    enrollist = db(db.sessions_enrol.student.belongs(studentlistA))._select(db.sessions_enrol.student)
    #studentlist =

    myquery=db.registered_course.student.belongs(enrollist) #._select(db.registered_course.student)
    resultlist = db(myquery).select()

    form=SQLFORM.grid(myquery, orderby=db.registered_course.student|db.registered_course.semester)
    return dict(form=form) #programs=programs, studentlist=studentlist, results=resultlist)


@auth.requires_membership('hod')
def print_resultlist():

    programs=db(db.program.department == request.vars.departid).select()
    studentlistA = db(db.student.program.belongs(programs)).select()
    studentlistB = db(db.sessions_enrol.student.belongs(studentlistA))._select(db.sessions_enrol.student)
    studentlist = db(db.student.id.belongs(studentlistB)).select()
    myquery=db.registered_course.student.belongs(studentlist)
    resultlist = db(myquery).select()
    semesters = db(myquery).select(db.registered_course.semester, distinct=True)

    courses = db(myquery).select(db.registered_course.course_subject,db.registered_course.semester, distinct=True)

    return dict(students=studentlist, semesters=semesters, courses = courses, results=resultlist, departid=request.vars.departid, sessionid=request.vars.sessionid)



#Utility
#without scores
@auth.requires_membership('hod')
def print_resultlistwts():
    request.vars.rpt = 'RESULT LIST - NOTICE BOARD'
    programs=db(db.program.department == request.vars.departid).select()
    studentlistA = db(db.student.program.belongs(programs)).select()
    studentlistB = db(db.sessions_enrol.student.belongs(studentlistA))._select(db.sessions_enrol.student)
    studentlist = db(db.student.id.belongs(studentlistB)).select()
    myquery=db.registered_course.student.belongs(studentlist)
    resultlist = db(myquery).select()
    semesters = db(myquery).select(db.registered_course.semester, distinct=True)

    courses = db(db.registered_course.student.belongs(studentlist)).select(db.registered_course.course_subject,db.registered_course.semester, distinct=True)

    #resultincuclm = db(db.registered_course.course_subject.belongs(curricourse, resultlist)).select()



    return dict(students=studentlist, semesters=semesters, courses = courses, results=resultlist, departid=request.vars.departid, sessionid=request.vars.sessionid)

@auth.requires_membership('hod')
def scoresheet():
    request.vars.rpt = 'MASTER SCORE SHEET'
    programs=db(db.program.department == request.vars.departid).select()
    studentqry = (db.student.school_level == request.vars.levels) & (db.student.program.belongs(programs))
    studentlist = db(studentqry).select()
    myquery=db.registered_course.student.belongs(studentlist)
    resultlist = db(myquery).select()
    distinctcourses = db(myquery).select(db.registered_course.course_subject, distinct=True)
    semesters = db(myquery).select(db.registered_course.semester, distinct=True)

    courses = db(db.registered_course.student.belongs(studentlist)).select(db.registered_course.course_subject,db.registered_course.semester, distinct=True)

    return dict(students=studentlist, semesters=semesters, courses = courses, results=resultlist, departid=request.vars.departid, sessionid=request.vars.sessionid)

@auth.requires_membership('hod')
def course_scoresheet():
    request.vars.rpt = 'COURSE SCORE SHEET'
    programs=db(db.program.department == request.vars.departid).select()
    studentqry = (db.student.school_level == request.vars.levels) & (db.student.program.belongs(programs))
    studentlist = db(studentqry).select()
    myquery=db.registered_course.student.belongs(studentlist)
    resultlist = db(myquery).select()
    distinctcourses = db(myquery).select(db.registered_course.course_subject, distinct=True)
    semesters = db(myquery).select(db.registered_course.semester, db.registered_course.sessions, distinct=True)

    courses = db(db.registered_course.student.belongs(studentlist)).select(db.registered_course.course_subject,db.registered_course.semester, distinct=True)

    return dict(students=studentlist, semesters=semesters, courses = courses, results=resultlist, departid=request.vars.departid, sessionid=request.vars.sessionid)


def biodataform():
    departid = 4 #request.vars.departid
    request.vars.rpt = 'STUDENT BIODATA LISTS'
    sessionid=5 #request.vars.sessionid
    #students=db(db.student.program==db.program(department=departid).id).select(orderby=db.student.matric_no)
    students=db(db.student.id > 0).select(orderby=db.student.matric_no)
    return dict(students=students, departid=departid, sessionid=sessionid)

def resultanalysis():
    departid = request.vars.departid
    sessionid = request.vars.sessionid
    levels = 'NDI' #request.vars.levels
    request.vars.rpt = 'RESULT ANALYSIS'
    programs=db(db.program.department == departid).select()
    program = programs.first()
    studentqry = (db.student.school_level == levels) & (db.student.program.belongs(programs))
    studentlist = db(studentqry).select()
    myquery=db.registered_course.student.belongs(studentlist)
    resultlist = db(myquery).select(db.registered_course.course_subject, db.registered_course.scores, db.registered_course.semester, db.registered_course.grade)
    #distinctcourses = db(myquery).select(db.registered_course.course_subject, distinct=True)
    semesters = db(myquery).select(db.registered_course.semester, db.registered_course.sessions, distinct=True)

    courses = db(db.registered_course.student.belongs(studentlist)).select(db.registered_course.course_subject,db.registered_course.semester,  distinct=True)
    grades=['AA', 'A', 'AB', 'B', 'BC', 'C', 'CD', 'D', 'E']
    std = []
    i=0
    #number = len(courses)

    for course in courses:
        diff = 0
        #count = db.registered_course.scores.count()
        average = db.registered_course.scores.avg()
        mean = db(db.registered_course.course_subject == course.course_subject).select(average).first()[average]
        #number = db(db.registered_course.course_subject == course.course_subject).select(count).first()[count]
        resultsub = resultlist.find(lambda result: result.course_subject==course.course_subject)
        number = len(resultsub) - 1
        for result in resultsub:
            
            diff += round(math.fabs(result.scores - mean)**2, 2)

        variance = round(math.sqrt(diff/number), 1)
        std.append(variance)

    #std = [6.0, 10.9, 5.8, 8.4, 7.9, 13.4, 5.9, 7.8, 9.0, 9.4, 1.1]

    return dict(grades=grades, students=studentlist, semesters=semesters, courses = courses, results=resultlist, departid=departid, sessionid=sessionid, std=std, program=program.fullname)
