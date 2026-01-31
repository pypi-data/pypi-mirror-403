#ifndef SCTP_ERROR_H
#define SCTP_ERROR_H

#define __ObjName(o) \
    (PyModule_Check(o) ? PyModule_GetName((PyObject *) (o)) : \
     Py_TYPE(o)->tp_name)
#define __SCTPErr(obj, meth) \
    do { \
        PyObject *type, *value, *tb; \
        \
        PyErr_Fetch(&type, &value, &tb); \
        (void) PyErr_Format( \
            type,  "%s.%s(): %S", __ObjName(obj), meth, \
            value ? value : Py_None \
            ); \
    } while (0)
#define __FUNC__ (strchr(__func__, '_') + 1)

#endif /* SCTP_ERROR_H */
