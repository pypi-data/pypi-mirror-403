/*****************************************************************************
 * INCLUDED FILES & MACRO DEFINITIONS
 *****************************************************************************/

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <netinet/sctp.h>

#define SCTP_INFO_PYMODULE
#include <sctp_info_capi.h>

/*****************************************************************************
 * OBJECT(s) DEFINITION(s)
 *****************************************************************************/

/* SCTPSndInfo OBJECT, defined in file `sctp_info_capi.h' */

/*****************************************************************************
 * LOCAL VARIABLES DECLARATIONS
 *****************************************************************************/

/*****************************************************************************
 * LOCAL FUNCTIONS DECLARATIONS
 *****************************************************************************/

int SCTPInfo_add_constants(PyObject *);

/*****************************************************************************
 * EXPORTED FUNCTIONS DECLARATIONS
 *****************************************************************************/

static void SCTPSndInfo2C(SCTPSndInfoObject *, struct sctp_sndinfo *);
static void SCTPPrInfo2C(SCTPPrInfoObject *, struct sctp_prinfo *);
static void SCTPAuthInfo2C(SCTPAuthInfoObject *, struct sctp_authinfo *);
static void SCTPSendvSpa2C(SCTPSendvSpaObject *, struct sctp_sendv_spa *);
static SCTPRcvInfoObject *SCTPC2RcvInfo(struct sctp_rcvinfo *);
static SCTPNxtInfoObject *SCTPC2NxtInfo(struct sctp_nxtinfo *);
static SCTPRecvvRnObject *SCTPC2RecvvRn(struct sctp_recvv_rn *);

/*****************************************************************************
 * SCTPSndInfo OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(SCTPSndInfoDoc, "Python wrapper for `struct sctp_sndinfo'");

/* METHODS */

/* MEMBERS */

/* GET/SET */

/* SPECIAL METHODS */

static int
SCTPSndInfoObject_init(SCTPSndInfoObject *self, PyObject *args, PyObject *kwds)
{
    static char *kf[][6] = {
	{
	    "snd_sid",
	    "snd_flags",
	    "snd_ppid",
	    "snd_context",
	    "snd_assoc_id",
	    NULL
	},
	{"H", "H", "I", "I", "i", NULL}
    };
    int values[5] = {0}, pos = 0;
    char fmt[] = {'|', '$', kf[1][0][0], kf[1][1][0], kf[1][2][0], kf[1][3][0],
	kf[1][4][0], 0};

    if (!PyArg_ParseTupleAndKeywords(
	    args, kwds, fmt, kf[0], &values[0], &values[1], &values[2],
	    &values[3], &values[4]))
	return -1;
    for (char **pk = kf[0], **pf = kf[1]; *pk; pk++, pf++, pos++)
	if (PyDict_SetItemString(
		(PyObject *) self, *pk, Py_BuildValue(*pf, values[pos])) < 0)
	    return -1;
    return 0;
}

/* TYPE */

static PyTypeObject SCTPSndInfoType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sctp_sndinfo",
    .tp_doc = SCTPSndInfoDoc,
    .tp_basicsize = sizeof(SCTPSndInfoObject),
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_init = (initproc) SCTPSndInfoObject_init
};

/*****************************************************************************
 * SCTPPrInfo OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(SCTPPrInfoDoc, "Python wrapper for `struct sctp_prinfo'");

/* METHODS */

/* MEMBERS */

/* GET/SET */

/* SPECIAL METHODS */

static int
SCTPPrInfoObject_init(SCTPPrInfoObject *self, PyObject *args, PyObject *kwds)
{
    static char *kf[][3] = {
	{
	    "pr_policy",
	    "pr_value",
	    NULL
	},
	{"H", "I", NULL}
    };
    int values[2] = {SCTP_PR_SCTP_NONE}, pos = 0;
    char fmt[] = {'|', '$', kf[1][0][0], kf[1][1][0], 0};

    if (!PyArg_ParseTupleAndKeywords(
	    args, kwds, fmt, kf[0], &values[0], &values[1]))
	return -1;
    if (values[0] != SCTP_PR_SCTP_NONE && values[0] != SCTP_PR_SCTP_TTL) {
	(void) PyErr_Format(
	    PyExc_ValueError,
	    "%s(): parameter `pr_policy' must be `SCTP_PR_SCTP_NONE' or "
	    "`SCTP_PR_SCTP_NONE'", Py_TYPE(self)->tp_name
	    );
	return -1;
    }
    for (char **pk = kf[0], **pf = kf[1]; *pk; pk++, pf++, pos++)
	if (PyDict_SetItemString(
		(PyObject *) self, *pk, Py_BuildValue(*pf, values[pos])) < 0)
	    return -1;
    return 0;
}

/* TYPE */

static PyTypeObject SCTPPrInfoType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sctp_prinfo",
    .tp_doc = SCTPPrInfoDoc,
    .tp_basicsize = sizeof(SCTPPrInfoObject),
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_init = (initproc) SCTPPrInfoObject_init
};

/*****************************************************************************
 * SCTPAuthInfo OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(SCTPAuthInfoDoc, "Python wrapper for `struct sctp_authinfo'");

/* METHODS */

/* MEMBERS */

/* GET/SET */

/* SPECIAL METHODS */

static int
SCTPAuthInfoObject_init(
    SCTPAuthInfoObject *self, PyObject *args, PyObject *kwds)
{
    static char *kf[][2] = {
	{
	    "auth_keynumber",
	    NULL
	},
	{"H", NULL}
    };
    int values[1] = {0}, pos = 0;
    char fmt[] = {'|', '$', kf[1][0][0], 0};

    if (!PyArg_ParseTupleAndKeywords(
	    args, kwds, fmt, kf[0], &values[0]))
	return -1;
    for (char **pk = kf[0], **pf = kf[1]; *pk; pk++, pf++, pos++)
	if (PyDict_SetItemString(
		(PyObject *) self, *pk, Py_BuildValue(*pf, values[pos])) < 0)
	    return -1;
    return 0;
}

/* TYPE */

static PyTypeObject SCTPAuthInfoType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sctp_authinfo",
    .tp_doc = SCTPAuthInfoDoc,
    .tp_basicsize = sizeof(SCTPAuthInfoObject),
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_init = (initproc) SCTPAuthInfoObject_init
};

/*****************************************************************************
 * SCTPSendvSpa OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(SCTPSendvSpaDoc, "Python wrapper for `struct sctp_sendv_spa'");

/* METHODS */

/* MEMBERS */

/* GET/SET */

static PyObject *
SCTPSendvSpaObject_get_sndinfo(SCTPSendvSpaObject *self, void *closure)
{
    if (!self->sndinfo)
	Py_RETURN_NONE;
    Py_INCREF(self->sndinfo);
    return (PyObject *) self->sndinfo;
}

static int
SCTPSendvSpaObject_set_sndinfo(
    SCTPSendvSpaObject *self, PyObject *value, void *closure)
{
     SCTPSndInfoObject *tmp;
    
    if (!value) {
	(void) PyErr_Format(
	    PyExc_TypeError, "%s.sndinfo: attribute can't be deleted",
	    Py_TYPE(self)->tp_name
	    );
        return -1;
    }
    if (!SCTPSndInfoObject_Check(value) && value != Py_None) {
        (void) PyErr_Format(
	    PyExc_TypeError,
	    "%s.sndinfo: attribute value must be a `sctp_sndinfo'"
	    " object or None", Py_TYPE(self)->tp_name
	    );
        return -1;
    }
    tmp = self->sndinfo;
    if (value == Py_None)
	value = NULL;
    Py_XINCREF(value);
    self->sndinfo = (SCTPSndInfoObject *) value;
    Py_XDECREF(tmp);
    return 0;
}

static PyObject *
SCTPSendvSpaObject_get_prinfo(SCTPSendvSpaObject *self, void *closure)
{
    if (!self->prinfo)
	Py_RETURN_NONE;
    Py_INCREF(self->prinfo);
    return (PyObject *) self->prinfo;
}

static int
SCTPSendvSpaObject_set_prinfo(
    SCTPSendvSpaObject *self, PyObject *value, void *closure)
{
     SCTPPrInfoObject *tmp;
    
    if (!value) {
	(void) PyErr_Format(
	    PyExc_TypeError, "%s.prinfo: attribute can't be deleted",
	    Py_TYPE(self)->tp_name
	    );
        return -1;
    }
    if (!SCTPPrInfoObject_Check(value) && value != Py_None) {
        (void) PyErr_Format(
	    PyExc_TypeError,
	    "%s.prinfo: attribute value must be a `sctp_prinfo' object or None",
	    Py_TYPE(self)->tp_name
	    );
        return -1;
    }
    tmp = self->prinfo;
    if (value == Py_None)
	value = NULL;
    Py_XINCREF(value);
    self->prinfo = (SCTPPrInfoObject *) value;
    Py_XDECREF(tmp);
    return 0;
}

static PyObject *
SCTPSendvSpaObject_get_authinfo(SCTPSendvSpaObject *self, void *closure)
{
    if (!self->authinfo)
	Py_RETURN_NONE;
    Py_INCREF(self->authinfo);
    return (PyObject *) self->authinfo;
}

static int
SCTPSendvSpaObject_set_authinfo(
    SCTPSendvSpaObject *self, PyObject *value, void *closure)
{
     SCTPAuthInfoObject *tmp;
    
    if (!value) {
	(void) PyErr_Format(
	    PyExc_TypeError, "%s.authinfo: attribute can't be deleted",
	    Py_TYPE(self)->tp_name
	    );
        return -1;
    }
    if (!SCTPAuthInfoObject_Check(value) && value != Py_None) {
        (void) PyErr_Format(
	    PyExc_TypeError,
	    "%s.authinfo: attribute value must be a `sctp_authinfo' "
	    "object or None", Py_TYPE(self)->tp_name
	    );
        return -1;
    }
    tmp = self->authinfo;
    if (value == Py_None)
	value = NULL;
    Py_XINCREF(value);
    self->authinfo = (SCTPAuthInfoObject *) value;
    Py_XDECREF(tmp);
    return 0;
}

static PyGetSetDef  SCTPSendvSpaGetSet[] = {
    {"sndinfo", (getter) SCTPSendvSpaObject_get_sndinfo,
     (setter) SCTPSendvSpaObject_set_sndinfo, "sndinfo field", NULL},
    {"prinfo", (getter) SCTPSendvSpaObject_get_prinfo,
     (setter) SCTPSendvSpaObject_set_prinfo, "prinfo field", NULL},
    {"authinfo", (getter) SCTPSendvSpaObject_get_authinfo,
     (setter) SCTPSendvSpaObject_set_authinfo, "authinfo field", NULL},
    {NULL, NULL, NULL, NULL, NULL}
};

/* SPECIAL METHODS */

static void
SCTPSendvSpaObject_dealloc(SCTPSendvSpaObject *self)
{
    Py_XDECREF(self->sndinfo);
    Py_XDECREF(self->prinfo);
    Py_XDECREF(self->authinfo);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
SCTPSendvSpaObject_str(SCTPSendvSpaObject *self)
{
    PyObject *snd_obj, *pr_obj, *auth_obj;

    if (self->sndinfo)
	snd_obj = (PyObject *) self->sndinfo;
    else {
	Py_INCREF(Py_None);
	snd_obj = Py_None;
    }
    if (self->prinfo)
	pr_obj = (PyObject *) self->prinfo;
    else {
	Py_INCREF(Py_None);
	pr_obj = Py_None;
    }
    if (self->authinfo)
	auth_obj = (PyObject *) self->authinfo;
    else {
	Py_INCREF(Py_None);
	auth_obj = Py_None;
    }
    return PyUnicode_FromFormat(
	"{'sndinfo': %S, 'prinfo': %S, 'authinfo': %S}",
	snd_obj, pr_obj, auth_obj
	);
}

static int
SCTPSendvSpaObject_init(
    SCTPSendvSpaObject *self, PyObject *args, PyObject *kwds)
{
    int ret = 0, count = 0;
    PyObject *item, *iter, *arg;

    if (!PyArg_ParseTuple(args, "O", &arg))
	return -1;
    iter = PyObject_GetIter(arg);
    if (!iter) {
	(void) PyErr_Format(
	    PyExc_TypeError, "%s(): arg1 must be an iterable of "
	    "`sctp_[snd|pr|auth]info' objects", Py_TYPE(self)->tp_name
	    );
	return -1;
    }
    while ((item = PyIter_Next(iter))) {
	if (SCTPSndInfoObject_Check(item)) {
	    if (self->sndinfo) {
		(void) PyErr_Format(
		    PyExc_ValueError,
		    "%s(): arg1: found duplicate item `sctp_sndinfo'",
		    Py_TYPE(self)->tp_name
		    );
		Py_DECREF(item);
		ret = -1;
		goto err;
	    }
	    self->sndinfo = (SCTPSndInfoObject *) item;
	}
	else if (SCTPPrInfoObject_Check(item)) {
	    if (self->prinfo) {
		(void) PyErr_Format(
		    PyExc_ValueError,
		    "%s(): arg1: found duplicate item `sctp_prinfo'",
		    Py_TYPE(self)->tp_name
		    );
		Py_DECREF(item);
		ret = -1;
		goto err;
	    }
	    self->prinfo = (SCTPPrInfoObject *) item;
	}
	else if (SCTPAuthInfoObject_Check(item)) {
	    if (self->authinfo) {
		(void) PyErr_Format(
		    PyExc_ValueError,
		    "%s(): arg1: found duplicate item `sctp_authinfo'",
		    Py_TYPE(self)->tp_name
		    );
		Py_DECREF(item);
		ret = -1;
		goto err;
	    }
	    self->authinfo = (SCTPAuthInfoObject *) item;
	}
	else {
	    (void) PyErr_Format(
		PyExc_TypeError,
		"%s(): arg1: invalid item#%d: must be "
		"`sctp_[snd|pr|auth]info'", Py_TYPE(self)->tp_name, count
		);
	    Py_DECREF(item);
	    ret = -1;
	    goto err;
	}
	count += 1;
    }
err:
    Py_DECREF(iter);
    return ret;
}

static PyObject *
SCTPSendvSpaObject_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    SCTPSendvSpaObject *self;
    
    self = (SCTPSendvSpaObject *) type->tp_alloc(type, 0);
    if (self) {
	self->sndinfo = NULL;
	self->prinfo = NULL;
	self->authinfo = NULL;
    }
    return (PyObject *) self;
}

/* TYPE */

static PyTypeObject SCTPSendvSpaType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sctp_sendv_spa",
    .tp_doc = SCTPSendvSpaDoc,
    .tp_basicsize = sizeof(SCTPSendvSpaObject),
    .tp_repr = (reprfunc) SCTPSendvSpaObject_str,
    .tp_str = (reprfunc) SCTPSendvSpaObject_str,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_getset = SCTPSendvSpaGetSet,
    .tp_init = (initproc) SCTPSendvSpaObject_init,
    .tp_new = SCTPSendvSpaObject_new,
    .tp_dealloc = (destructor) SCTPSendvSpaObject_dealloc
};

/*****************************************************************************
 * SCTPRcvInfo OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(SCTPRcvInfoDoc, "Python wrapper for `struct sctp_rcvinfo'");

/* METHODS */

/* MEMBERS */

/* GET/SET */

/* SPECIAL METHODS */

static int
SCTPRcvInfoObject_init(SCTPRcvInfoObject *self, PyObject *args, PyObject *kwds)
{
    static char *kf[][9] = {
	{
	    "rcv_sid",
	    "rcv_ssn",
	    "rcv_flags",
	    "rcv_ppid",
	    "rcv_tsn",
	    "rcv_cumtsn",
	    "rcv_context",
	    "rcv_assoc_id",
	    NULL
	},
	{"H", "H", "H", "I", "I", "I", "I", "i", NULL}
    };
    int values[8] = {0}, pos = 0;
    char fmt[] = {'|', '$', kf[1][0][0], kf[1][1][0], kf[1][2][0], kf[1][3][0],
	kf[1][4][0], kf[1][5][0], kf[1][6][0], kf[1][7][0], 0};
        
    if (!PyArg_ParseTupleAndKeywords(
	    args, kwds, fmt, kf[0], &values[0], &values[1], &values[2],
	    &values[3], &values[4]))
	return -1;
    for (char **pk = kf[0], **pf = kf[1]; *pk; pk++, pf++, pos++)
	if (PyDict_SetItemString(
		(PyObject *) self, *pk, Py_BuildValue(*pf, values[pos])) < 0)
	    return -1;
    return 0;
}

/* TYPE */

static PyTypeObject SCTPRcvInfoType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sctp_rcvinfo",
    .tp_doc = SCTPRcvInfoDoc,
    .tp_basicsize = sizeof(SCTPRcvInfoObject),
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_init = (initproc) SCTPRcvInfoObject_init
};

/*****************************************************************************
 * SCTPNxtInfo OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(SCTPNxtInfoDoc, "Python wrapper for `struct sctp_nxtinfo'");

/* METHODS */

/* MEMBERS */

/* GET/SET */

/* SPECIAL METHODS */

static int
SCTPNxtInfoObject_init(SCTPNxtInfoObject *self, PyObject *args, PyObject *kwds)
{
    static char *kf[][6] = {
	{
	    "nxt_sid",
	    "nxt_flags",
	    "nxt_ppid",
	    "nxt_length",
	    "nxt_assoc_id",
	    NULL
	},
	{"H", "H", "I", "I", "i", NULL}
    };
    int values[5] = {0}, pos = 0;
    char fmt[] = {'|', '$', kf[1][0][0], kf[1][1][0], kf[1][2][0], kf[1][3][0],
	kf[1][4][0], 0};
        
    if (!PyArg_ParseTupleAndKeywords(
	    args, kwds, fmt, kf[0], &values[0], &values[1], &values[2],
	    &values[3], &values[4]))
	return -1;
    for (char **pk = kf[0], **pf = kf[1]; *pk; pk++, pf++, pos++)
	if (PyDict_SetItemString(
		(PyObject *) self, *pk, Py_BuildValue(*pf, values[pos])) < 0)
	    return -1;
    return 0;
}

/* TYPE */

static PyTypeObject SCTPNxtInfoType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sctp_nxtinfo",
    .tp_doc = SCTPNxtInfoDoc,
    .tp_basicsize = sizeof(SCTPNxtInfoObject),
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_init = (initproc) SCTPNxtInfoObject_init
};

/*****************************************************************************
 * SCTPNxtInfo OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(SCTPRecvvRnDoc, "Python wrapper for `struct sctp_recvv_rn'");

/* METHODS */

/* MEMBERS */

/* GET/SET */

static PyObject *
SCTPRecvvRnObject_get_rcvinfo(SCTPRecvvRnObject *self, void *closure)
{
    if (!self->rcvinfo)
	Py_RETURN_NONE;
    Py_INCREF(self->rcvinfo);
    return (PyObject *) self->rcvinfo;
}

static int
SCTPRecvvRnObject_set_rcvinfo(
    SCTPRecvvRnObject *self, PyObject *value, void *closure)
{
     SCTPRcvInfoObject *tmp;
    
    if (!value) {
	(void) PyErr_Format(
	    PyExc_TypeError, "%s.rcvinfo: attribute can't be deleted",
	    Py_TYPE(self)->tp_name
	    );
        return -1;
    }
    if (!SCTPRcvInfoObject_Check(value) && value != Py_None) {
        (void) PyErr_Format(
	    PyExc_TypeError,
	    "%s.rcvinfo: attribute value must be a `sctp_rcvinfo' "
	    "object or None", Py_TYPE(self)->tp_name
	    );
        return -1;
    }
    tmp = self->rcvinfo;
    if (value == Py_None)
	value = NULL;
    Py_XINCREF(value);
    self->rcvinfo = (SCTPRcvInfoObject *) value;
    Py_XDECREF(tmp);
    return 0;
}

static PyObject *
SCTPRecvvRnObject_get_nxtinfo(SCTPRecvvRnObject *self, void *closure)
{
    if (!self->nxtinfo)
	Py_RETURN_NONE;
    Py_INCREF(self->nxtinfo);
    return (PyObject *) self->nxtinfo;
}

static int
SCTPRecvvRnObject_set_nxtinfo(
    SCTPRecvvRnObject *self, PyObject *value, void *closure)
{
     SCTPNxtInfoObject *tmp;
    
    if (!value) {
	(void) PyErr_Format(
	    PyExc_TypeError, "%s.nxtinfo: attribute can't be deleted",
	    Py_TYPE(self)->tp_name
	    );
        return -1;
    }
    if (!SCTPNxtInfoObject_Check(value) && value != Py_None) {
        (void) PyErr_Format(
	    PyExc_TypeError,
	    "%s.nxtinfo: attribute value must be a `sctp_nxtinfo' "
	    "object or None", Py_TYPE(self)->tp_name
	    );
        return -1;
    }
    tmp = self->nxtinfo;
    if (value == Py_None)
	value = NULL;
    Py_XINCREF(value);
    self->nxtinfo = (SCTPNxtInfoObject *) value;
    Py_XDECREF(tmp);
    return 0;
}

static PyGetSetDef  SCTPRecvvRnGetSet[] = {
    {"rcvinfo", (getter) SCTPRecvvRnObject_get_rcvinfo,
     (setter) SCTPRecvvRnObject_set_rcvinfo, "rcvinfo field", NULL},
    {"nxtinfo", (getter) SCTPRecvvRnObject_get_nxtinfo,
     (setter) SCTPRecvvRnObject_set_nxtinfo, "nxtinfo field", NULL},
    {NULL, NULL, NULL, NULL, NULL}
};

/* SPECIAL METHODS */

static void
SCTPRecvvRnObject_dealloc(SCTPRecvvRnObject *self)
{
    Py_XDECREF(self->rcvinfo);
    Py_XDECREF(self->nxtinfo);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
SCTPRecvvRnObject_str(SCTPRecvvRnObject *self)
{
    PyObject *rcv_obj, *nxt_obj;

    if (self->rcvinfo)
	rcv_obj = (PyObject *) self->rcvinfo;
    else {
	Py_INCREF(Py_None);
	rcv_obj = Py_None;
    }
    if (self->nxtinfo)
	nxt_obj = (PyObject *) self->nxtinfo;
    else {
	Py_INCREF(Py_None);
	nxt_obj = Py_None;
    }
    return PyUnicode_FromFormat(
	"{'rcvinfo': %S, 'nxtinfo': %S}", rcv_obj, nxt_obj
	);
}

static int
SCTPRecvvRnObject_init(
    SCTPRecvvRnObject *self, PyObject *args, PyObject *kwds)
{
    int ret = 0, count = 0;
    PyObject *item, *iter, *arg;

    if (!PyArg_ParseTuple(args, "O", &arg))
	return -1;
    iter = PyObject_GetIter(arg);
    if (!iter) {
	(void) PyErr_Format(
	    PyExc_TypeError, "%s(): arg1 must be an iterable of "
	    "`sctp_[rcv|nxt]info' objects", Py_TYPE(self)->tp_name
	    );
	return -1;
    }
    while ((item = PyIter_Next(iter))) {
	if (SCTPRcvInfoObject_Check(item)) {
	    if (self->rcvinfo) {
		(void) PyErr_Format(
		    PyExc_ValueError,
		    "%s(): arg1: found duplicate item `sctp_rcvinfo'",
		    Py_TYPE(self)->tp_name
		    );
		Py_DECREF(item);
		ret = -1;
		goto err;
	    }
	    self->rcvinfo = (SCTPRcvInfoObject *) item;
	}
	else if (SCTPNxtInfoObject_Check(item)) {
	    if (self->nxtinfo) {
		(void) PyErr_Format(
		    PyExc_ValueError,
		    "%s(): arg1: found duplicate item `sctp_nxtinfo'",
		    Py_TYPE(self)->tp_name
		    );
		Py_DECREF(item);
		ret = -1;
		goto err;
	    }
	    self->nxtinfo = (SCTPNxtInfoObject *) item;
	}
	else {
	    (void) PyErr_Format(
		PyExc_TypeError,
		"%s(): arg1: invalid item#%d: must be "
		"`sctp_[rcv|nxt]info'", Py_TYPE(self)->tp_name, count
		);
	    Py_DECREF(item);
	    ret = -1;
	    goto err;
	}
	count += 1;
    }
err:
    Py_DECREF(iter);
    return ret;
}

static PyObject *
SCTPRecvvRnObject_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    SCTPRecvvRnObject *self;
    
    self = (SCTPRecvvRnObject *) type->tp_alloc(type, 0);
    if (self) {
	self->rcvinfo = NULL;
	self->nxtinfo = NULL;
    }
    return (PyObject *) self;
}

/* TYPE */

static PyTypeObject SCTPRecvvRnType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sctp_recvv_rn",
    .tp_doc = SCTPRecvvRnDoc,
    .tp_basicsize = sizeof(SCTPRecvvRnObject),
    .tp_repr = (reprfunc) SCTPRecvvRnObject_str,
    .tp_str = (reprfunc) SCTPRecvvRnObject_str,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_getset = SCTPRecvvRnGetSet,
    .tp_init = (initproc) SCTPRecvvRnObject_init,
    .tp_new = SCTPRecvvRnObject_new,
    .tp_dealloc = (destructor) SCTPRecvvRnObject_dealloc
};

/*****************************************************************************
 * MODULE METHODS
 *****************************************************************************/

/*****************************************************************************
 * MODULE INITIALIZATION
 *****************************************************************************/

PyDoc_STRVAR(
    SCTPInfoDoc,
    "Python wrapper for struct sctp_*info - C module `" MODS_DIR "."
    "sctp_info'"
    );

static PyModuleDef SCTPInfoModule = {
    PyModuleDef_HEAD_INIT,
    .m_name = MODS_DIR "." "sctp_info",
    .m_doc = SCTPInfoDoc,
    .m_size = -1,
};

PyMODINIT_FUNC
PyInit_sctp_info(void)
{
    PyObject* m, *sctp_info_capi_obj;
    static void *sctp_info_capi[] = {
	&SCTPSndInfoType, SCTPSndInfo2C,
	&SCTPPrInfoType, SCTPPrInfo2C,
	&SCTPAuthInfoType, SCTPAuthInfo2C,
	&SCTPSendvSpaType, SCTPSendvSpa2C,
	&SCTPRcvInfoType, SCTPC2RcvInfo,
	&SCTPNxtInfoType, SCTPC2NxtInfo,
	&SCTPRecvvRnType, SCTPC2RecvvRn
    };

    SCTPSndInfoType.tp_base = &PyDict_Type;
    if (PyType_Ready(&SCTPSndInfoType) < 0) {
        return NULL;
    }
    SCTPPrInfoType.tp_base = &PyDict_Type;
    if (PyType_Ready(&SCTPPrInfoType) < 0) {
        return NULL;
    }
    SCTPAuthInfoType.tp_base = &PyDict_Type;
    if (PyType_Ready(&SCTPAuthInfoType) < 0) {
        return NULL;
    }
    if (PyType_Ready(&SCTPSendvSpaType) < 0) {
        return NULL;
    }
    SCTPRcvInfoType.tp_base = &PyDict_Type;
    if (PyType_Ready(&SCTPRcvInfoType) < 0) {
        return NULL;
    }
    SCTPNxtInfoType.tp_base = &PyDict_Type;
    if (PyType_Ready(&SCTPNxtInfoType) < 0) {
        return NULL;
    }
    if (PyType_Ready(&SCTPRecvvRnType) < 0) {
        return NULL;
    }
    m = PyModule_Create(&SCTPInfoModule);
    if (!m) {
	return NULL;
    }
    if (SCTPInfo_add_constants(m) < 0) {
	Py_DECREF(m);
        return NULL;
    }
    sctp_info_capi_obj = PyCapsule_New(
        (void *) sctp_info_capi, SCTP_INFO_CAPSULE_NAME, NULL);
    if (!sctp_info_capi_obj) {
	Py_DECREF(m);
        return NULL;
    }
    if (PyModule_AddObject(m, SCTP_INFO_CAPI_NAME, sctp_info_capi_obj) < 0) {
        Py_DECREF(sctp_info_capi_obj);
        Py_DECREF(m);
        return NULL;
    }
    Py_INCREF(&SCTPSndInfoType);
    if (PyModule_AddObject(
	    m, "sctp_sndinfo", (PyObject *) &SCTPSndInfoType) < 0) {
	Py_DECREF(sctp_info_capi_obj);
	Py_DECREF(&SCTPSndInfoType);
	Py_DECREF(m);
        return NULL;
    }
    Py_INCREF(&SCTPPrInfoType);
    if (PyModule_AddObject(
	    m, "sctp_prinfo", (PyObject *) &SCTPPrInfoType) < 0) {
	Py_DECREF(sctp_info_capi_obj);
	Py_DECREF(&SCTPSndInfoType);
	Py_DECREF(&SCTPPrInfoType);
	Py_DECREF(m);
        return NULL;
    }
    Py_INCREF(&SCTPAuthInfoType);
    if (PyModule_AddObject(
	    m, "sctp_authinfo", (PyObject *) &SCTPAuthInfoType) < 0) {
	Py_DECREF(sctp_info_capi_obj);
	Py_DECREF(&SCTPSndInfoType);
	Py_DECREF(&SCTPPrInfoType);
	Py_DECREF(&SCTPAuthInfoType);
	Py_DECREF(m);
        return NULL;
    }
    Py_INCREF(&SCTPSendvSpaType);
    if (PyModule_AddObject(
	    m, "sctp_sendv_spa", (PyObject *) &SCTPSendvSpaType) < 0) {
	Py_DECREF(sctp_info_capi_obj);
	Py_DECREF(&SCTPSndInfoType);
	Py_DECREF(&SCTPPrInfoType);
	Py_DECREF(&SCTPAuthInfoType);
	Py_DECREF(&SCTPSendvSpaType);
	Py_DECREF(m);
        return NULL;
    }
    Py_INCREF(&SCTPRcvInfoType);
    if (PyModule_AddObject(
	    m, "sctp_rcvinfo", (PyObject *) &SCTPRcvInfoType) < 0) {
	Py_DECREF(sctp_info_capi_obj);
	Py_DECREF(&SCTPSndInfoType);
	Py_DECREF(&SCTPPrInfoType);
	Py_DECREF(&SCTPAuthInfoType);
	Py_DECREF(&SCTPSendvSpaType);
	Py_DECREF(&SCTPRcvInfoType);
	Py_DECREF(m);
        return NULL;
    }
    Py_INCREF(&SCTPNxtInfoType);
    if (PyModule_AddObject(
	    m, "sctp_nxtinfo", (PyObject *) &SCTPNxtInfoType) < 0) {
	Py_DECREF(sctp_info_capi_obj);
	Py_DECREF(&SCTPSndInfoType);
	Py_DECREF(&SCTPPrInfoType);
	Py_DECREF(&SCTPAuthInfoType);
	Py_DECREF(&SCTPSendvSpaType);
	Py_DECREF(&SCTPRcvInfoType);
	Py_DECREF(&SCTPNxtInfoType);
	Py_DECREF(m);
        return NULL;
    }
    Py_INCREF(&SCTPRecvvRnType);
    if (PyModule_AddObject(
	    m, "sctp_recvv_rn", (PyObject *) &SCTPRecvvRnType) < 0) {
	Py_DECREF(sctp_info_capi_obj);
	Py_DECREF(&SCTPSndInfoType);
	Py_DECREF(&SCTPPrInfoType);
	Py_DECREF(&SCTPAuthInfoType);
	Py_DECREF(&SCTPSendvSpaType);
	Py_DECREF(&SCTPRcvInfoType);
	Py_DECREF(&SCTPNxtInfoType);
	Py_DECREF(&SCTPRecvvRnType);
	Py_DECREF(m);
        return NULL;
    }
    return m;
}

/*****************************************************************************
 * LOCAL FUNCTION DEFINITIONS
 *****************************************************************************/

int
SCTPInfo_add_constants(PyObject *m)
{
    if (PyModule_AddIntConstant(m, "SCTP_UNORDERED", SCTP_UNORDERED) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_ADDR_OVER", SCTP_ADDR_OVER) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_ABORT", SCTP_ABORT) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_EOF", SCTP_EOF) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_SENDALL", SCTP_SENDALL) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SEND_SNDINFO_VALID", SCTP_SEND_SNDINFO_VALID) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SEND_PRINFO_VALID", SCTP_SEND_PRINFO_VALID) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SEND_AUTHINFO_VALID", SCTP_SEND_AUTHINFO_VALID) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_PR_SCTP_NONE", SCTP_PR_SCTP_NONE) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_PR_SCTP_TTL", SCTP_PR_SCTP_TTL) < 0)
	return -1;
#ifdef HAVE_FREEBSD
    if (PyModule_AddIntConstant(m, "SCTP_COMPLETE", SCTP_COMPLETE) < 0)
	return -1; /* (constant defined in RFC-6458, but not in Linux */
#endif /* HAVE_FREEBSD */
    if (PyModule_AddIntConstant(m, "SCTP_NOTIFICATION", SCTP_NOTIFICATION) < 0)
	return -1;
    return 0;
}

/*****************************************************************************
 * EXPORTED FUNCTIONS DEFINITIONS
 *****************************************************************************/

static void
SCTPSndInfo2C(SCTPSndInfoObject *info_obj, struct sctp_sndinfo *info)
{
    if (!info_obj)
	return;
    info->snd_sid = PyLong_AsLong(
	PyDict_GetItemString((PyObject *) info_obj, "snd_sid"));
    info->snd_flags = PyLong_AsLong(
	PyDict_GetItemString((PyObject *) info_obj, "snd_flags"));
    info->snd_ppid = PyLong_AsLong(
	PyDict_GetItemString((PyObject *) info_obj, "snd_ppid"));
    info->snd_context = PyLong_AsLong(
	PyDict_GetItemString((PyObject *) info_obj, "snd_context"));
    info->snd_assoc_id = PyLong_AsLong(
	PyDict_GetItemString((PyObject *) info_obj, "snd_assoc_id"));
}

static void
SCTPPrInfo2C(SCTPPrInfoObject *info_obj, struct sctp_prinfo *info)
{
    if (!info_obj)
	return;
    info->pr_policy = PyLong_AsLong(
	PyDict_GetItemString((PyObject *) info_obj, "pr_policy"));
    info->pr_value = PyLong_AsLong(
	PyDict_GetItemString((PyObject *) info_obj, "pr_value"));
}

static void
SCTPAuthInfo2C(SCTPAuthInfoObject *info_obj, struct sctp_authinfo *info)
{
    if (!info_obj)
	return;
    info->auth_keynumber = PyLong_AsLong(
	PyDict_GetItemString((PyObject *) info_obj, "auth_keynumber"));
}

static void
SCTPSendvSpa2C(SCTPSendvSpaObject *info_obj, struct sctp_sendv_spa *info)
{
    if (!info_obj)
	return;
    info->sendv_flags = 0;
    if (info_obj->sndinfo) {
	SCTPSndInfo2C(info_obj->sndinfo, &info->sendv_sndinfo);
	info->sendv_flags |= SCTP_SEND_SNDINFO_VALID;
    }
    if (info_obj->prinfo) {
	SCTPPrInfo2C(info_obj->prinfo, &info->sendv_prinfo);
	info->sendv_flags |= SCTP_SEND_PRINFO_VALID;
    }
    if (info_obj->authinfo) {
	SCTPAuthInfo2C(info_obj->authinfo, &info->sendv_authinfo);
	info->sendv_flags |= SCTP_SEND_AUTHINFO_VALID;
    }
}

static SCTPRcvInfoObject *
SCTPC2RcvInfo(struct sctp_rcvinfo *info)
{
    SCTPRcvInfoObject *ret;

    ret = (SCTPRcvInfoObject *) SCTPRcvInfoType.tp_new(
	&SCTPRcvInfoType, NULL,  NULL);
    if (!ret)
	return NULL;
    if (SCTPRcvInfoType.tp_init(
	    (PyObject *) ret, Py_BuildValue("()"), NULL) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "rcv_sid",
	    Py_BuildValue("H", info->rcv_sid)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "rcv_ssn",
	    Py_BuildValue("H", info->rcv_ssn)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "rcv_flags",
	    Py_BuildValue("H", info->rcv_flags)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "rcv_ppid",
	    Py_BuildValue("I", info->rcv_ppid)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "rcv_tsn",
	    Py_BuildValue("I", info->rcv_tsn)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "rcv_cumtsn",
	    Py_BuildValue("I", info->rcv_cumtsn)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "rcv_context",
	    Py_BuildValue("I", info->rcv_context)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "rcv_assoc_id",
	    Py_BuildValue("i", info->rcv_assoc_id)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    return ret; 
}

static SCTPNxtInfoObject *
SCTPC2NxtInfo(struct sctp_nxtinfo *info)
{
    SCTPNxtInfoObject *ret;

    ret = (SCTPNxtInfoObject *) SCTPNxtInfoType.tp_new(
	&SCTPNxtInfoType, NULL,  NULL);
    if (!ret)
	return NULL;
    if (SCTPNxtInfoType.tp_init(
	    (PyObject *) ret, Py_BuildValue("()"), NULL) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "nxt_sid",
	    Py_BuildValue("H", info->nxt_sid)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "nxt_flags",
	    Py_BuildValue("H", info->nxt_flags)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "nxt_ppid",
	    Py_BuildValue("I", info->nxt_ppid)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "nxt_length",
	    Py_BuildValue("I", info->nxt_length)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    (PyObject *) ret, "nxt_assoc_id",
	    Py_BuildValue("i", info->nxt_assoc_id)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    return ret;
}

static SCTPRecvvRnObject *
SCTPC2RecvvRn(struct sctp_recvv_rn *info)
{
    SCTPRecvvRnObject *ret;

    ret = (SCTPRecvvRnObject *) SCTPRecvvRnType.tp_new(
	&SCTPRecvvRnType, NULL,  NULL);
    if (!ret)
	return NULL;
    ret->rcvinfo = SCTPC2RcvInfo(&info->recvv_rcvinfo);
    if (!ret->rcvinfo) {
	Py_DECREF(ret);
	return NULL;
    }
    ret->nxtinfo = SCTPC2NxtInfo(&info->recvv_nxtinfo);
    if (!ret->nxtinfo) {
	Py_DECREF(ret->rcvinfo);
	Py_DECREF(ret);
	return NULL;
    }
    return ret;
}
