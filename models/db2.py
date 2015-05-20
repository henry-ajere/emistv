# coding: utf8
db.define_table('bank_pay',
                Field('student', 'reference student'),
                Field('bank', requires=IS_IN_SET(['UBA', 'GTB', 'FBN', 'Diamond', 'FCMB', 'Fidelity'])),
                Field('slip_no'),
                Field('date_paid', 'date'),
                Field('amount_paid', 'integer'),
                auth.signature,
                format='%(slip_no)s'
                )

db.define_table('etranzact',
                Field('student', 'reference student'),
                Field('bank', requires=IS_IN_SET(['UBA', 'GTB', 'FBN', 'Diamond', 'FCMB', 'Fidelity'])),
                Field('receipt_nos'),
                Field('confirmation_no'),
                Field('date_paid', 'date'),
                Field('amount_paid', 'integer'),
                auth.signature,
                format='%(receipt_nos)s'
                )
