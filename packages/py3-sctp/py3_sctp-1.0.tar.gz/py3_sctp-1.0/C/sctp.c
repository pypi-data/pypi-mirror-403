/*****************************************************************************
 * INCLUDED FILES & MACRO DEFINITIONS
 *****************************************************************************/

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/sctp.h>

#include <sctp_info_capi.h>
#include <sctp_error.h>

#define SOCKADDR_GET_PORT(sa) ntohs((sa)->sa_family == AF_INET ? \
	((struct sockaddr_in *) (sa))->sin_port : \
	((struct sockaddr_in6 *) (sa))->sin6_port)

#define SOCKADDR_GET_SIZE(sa) ((sa)->sa_family == AF_INET ? \
	sizeof(struct sockaddr_in) : sizeof(struct sockaddr_in6))

typedef int (getlpaddrs_t)(int, sctp_assoc_t, struct sockaddr **);

/*****************************************************************************
 * OBJECT(s) DEFINITION(s)
 *****************************************************************************/

/* SCTP Socket OBJECT */

typedef struct {
    PyObject_HEAD
    PyObject *sock;
    int fd;
    int family;
    int type;
} SCTPSocketObject;

/*****************************************************************************
 * LOCAL VARIABLES DECLARATIONS
 *****************************************************************************/

static PyObject *SocketModule;
static PyObject *SCTPErr;

/*****************************************************************************
 * LOCAL FUNCTIONS DECLARATIONS
 *****************************************************************************/

static int SCTPModule_add_constants(PyObject *);
static int obj_to_iovec(PyObject *, struct iovec **, int *);
static void iovec_free(struct iovec *, int);
static int obj_to_sockaddrs(
    PyObject *, int, int, int, struct sockaddr **, int *);
static int obj_to_sockaddr(
    PyObject *, int, int, struct sockaddr *, socklen_t *);
static PyObject *sockaddr_to_obj(struct sockaddr *, socklen_t);
static PyObject *sctp_getlpaddrs(SCTPSocketObject *, PyObject *, getlpaddrs_t);
static PyObject *sockfd_to_sctpsock(int);

/*****************************************************************************
 * EXPORTED FUNCTIONS DECLARATIONS
 *****************************************************************************/

/*****************************************************************************
 * SCTP Socket OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(SCTPSocketDoc, "SCTP socket object");

/* METHODS */

PyDoc_STRVAR(SCTPSocketDoc_bindx, "sctp_bindx() method");

static PyObject *
SCTPSocketObject_sctp_bindx(SCTPSocketObject *self, PyObject *args)
{
    int flags, addrcnt, rcode;
    PyObject *addrs_obj;
    struct sockaddr *addrs;
    
    if (!PyArg_ParseTuple(args, "Oi", &addrs_obj, &flags))
	return NULL;
    if (flags != SCTP_BINDX_ADD_ADDR && flags != SCTP_BINDX_REM_ADDR) {
	PyErr_SetString(
	    PyExc_ValueError, "arg2 must be `SCTP_BINDX_ADD_ADDR' or "
	    "`SCTP_BINDX_REM_ADDR'"
	    );
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    if (obj_to_sockaddrs(
	    addrs_obj, self->family, self->type, 1, &addrs, &addrcnt) < 0) {
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    if (addrcnt > 1) {
	uint16_t first = SOCKADDR_GET_PORT(addrs);
	struct sockaddr *ptr = (struct sockaddr *)
	    ((char *) addrs + SOCKADDR_GET_SIZE(addrs));

	for (int i = 1; i < addrcnt; i++) {
	    uint16_t curr = SOCKADDR_GET_PORT(ptr);

	    if ((!first && curr) || (first && curr && curr != first)) {
		(void) PyErr_Format(
		    PyExc_ValueError,
		    "arg1: address#%d: port number must be %d", i + 1, first
		    );
		__SCTPErr(self, __FUNC__);
		PyMem_Free(addrs);
		return NULL;
	    }	
	    ptr = (struct sockaddr *) ((char *) ptr + SOCKADDR_GET_SIZE(ptr));
	}
    }
    Py_BEGIN_ALLOW_THREADS
    rcode = sctp_bindx(self->fd, addrs, addrcnt, flags);
    Py_END_ALLOW_THREADS
    if (rcode < 0) {
	(void) PyErr_Format(PyExc_OSError, "[%d, %s]", errno, strerror(errno));
	__SCTPErr(self, __FUNC__);
	PyMem_Free(addrs);
	return NULL;
    }
    PyMem_Free(addrs);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(SCTPSocketDoc_connectx, "sctp_connectx() method");

static PyObject *
SCTPSocketObject_sctp_connectx(
    SCTPSocketObject *self, PyObject *args, PyObject *kwds)
{
    int addrcnt, rcode;
    struct sockaddr *addrs;
    sctp_assoc_t id, *id_ptr; 
    PyObject *addrs_obj, *id_obj = Py_False;
    static char *kwlist[] = {"addrs", "assoc_id", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(
	    args, kwds, "O|$O!", kwlist, &addrs_obj, &PyBool_Type, &id_obj))
	return NULL;
    id_ptr = id_obj == Py_False ? NULL : &id;
    if (obj_to_sockaddrs(
	    addrs_obj, self->family, self->type, 1, &addrs, &addrcnt) < 0) {
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    Py_BEGIN_ALLOW_THREADS
    rcode = sctp_connectx(self->fd, addrs, addrcnt, id_ptr);
    Py_END_ALLOW_THREADS
    if (rcode < 0) {
	(void) PyErr_Format(PyExc_OSError, "[%d, %s]", errno, strerror(errno));
	__SCTPErr(self, __FUNC__);
	PyMem_Free(addrs);
	return NULL;
    }
    PyMem_Free(addrs);
    if (!id_ptr)
	Py_RETURN_NONE;
    return Py_BuildValue("i", id);
}

PyDoc_STRVAR(SCTPSocketDoc_getladdrs, "sctp_getladdrs() method");

static PyObject *
SCTPSocketObject_sctp_getladdrs(SCTPSocketObject *self, PyObject *args)
{
    return sctp_getlpaddrs(self, args, sctp_getladdrs);
}

PyDoc_STRVAR(SCTPSocketDoc_getpaddrs, "sctp_getpaddrs() method");

static PyObject *
SCTPSocketObject_sctp_getpaddrs(SCTPSocketObject *self, PyObject *args)
{
    return sctp_getlpaddrs(self, args, sctp_getpaddrs);
}

PyDoc_STRVAR(SCTPSocketDoc_recvv, "sctp_recvv() method");

static PyObject *
SCTPSocketObject_sctp_recvv(SCTPSocketObject *self, PyObject *args)
{
    int rcv_on, nxt_on, flags = 0, noc;
    unsigned int infotype = SCTP_RECVV_NOINFO;
    struct iovec iov;
    struct sockaddr_storage from;
    socklen_t fromlen = sizeof(from);
    socklen_t rcv_len = sizeof(rcv_on), nxt_len = sizeof(nxt_on), infolen = 0;
    void *info = NULL;
    union {
	struct sctp_rcvinfo rcv;
	struct sctp_nxtinfo nxt;
	struct sctp_recvv_rn rn;
    } info_un;
    PyObject *addr_obj = NULL, *info_obj = NULL, *bytes = NULL, *ret = NULL;

    if (!PyArg_ParseTuple(args, "n", &iov.iov_len))
	return NULL;
    if (getsockopt(
	    self->fd, IPPROTO_SCTP, SCTP_RECVRCVINFO, &rcv_on, &rcv_len) < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "getsockopt(): [%d, %s]", errno, strerror(errno)
	    );
	    __SCTPErr(self, __FUNC__);
	    return NULL;
    }
    if (getsockopt(
	    self->fd, IPPROTO_SCTP, SCTP_RECVNXTINFO, &nxt_on, &nxt_len) < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "getsockopt(): [%d, %s]", errno, strerror(errno)
	    );
	    __SCTPErr(self, __FUNC__);
	    return NULL;
    }
    (void) memset(&info_un, 0, sizeof(info_un));
    if (rcv_on)
	if (nxt_on) {
	    info = &info_un.rn;
	    infolen = sizeof(info_un.rn);
	    infotype = SCTP_RECVV_RN;
	}
	else {
	    info = &info_un.rcv;
	    infolen = sizeof(info_un.rcv);
	}
    else if (nxt_on) {
	info = &info_un.nxt;
	infolen = sizeof(info_un.nxt);
    }
    iov.iov_base = PyMem_Malloc(iov.iov_len);
    if (!iov.iov_base)
	return PyErr_NoMemory();
    Py_BEGIN_ALLOW_THREADS
    noc = sctp_recvv(
	self->fd, &iov, 1, (struct sockaddr *) &from, &fromlen, info,
	&infolen, &infotype, &flags);
    Py_END_ALLOW_THREADS
    if (noc < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	__SCTPErr(self, __FUNC__);
	goto err;
    }
    bytes = PyBytes_FromStringAndSize(iov.iov_base, noc);
    if (!bytes) {
	__SCTPErr(self, __FUNC__);
	goto err;
    }
    switch (infotype) {
    case SCTP_RECVV_NOINFO:
	Py_INCREF(Py_None);
	info_obj = Py_None;
	break;
    case SCTP_RECVV_RCVINFO:
	info_obj = (PyObject *) SCTPC2RcvInfo(&info_un.rcv);
	break;
    case SCTP_RECVV_NXTINFO:
	info_obj = (PyObject *) SCTPC2NxtInfo(&info_un.nxt);
	break;
    case SCTP_RECVV_RN:
	info_obj = (PyObject *) SCTPC2RecvvRn(&info_un.rn);
	break;
    }
    if (!info_obj) {
	__SCTPErr(self, __FUNC__);
	goto err;
    }
    addr_obj = sockaddr_to_obj((struct sockaddr *) &from, fromlen);
    ret = Py_BuildValue("(OOOIi)", bytes, addr_obj, info_obj, infotype, flags);
err:
    Py_XDECREF(bytes);
    Py_XDECREF(addr_obj);
    Py_XDECREF(info_obj);
    PyMem_Free(iov.iov_base);
    return ret;
}

PyDoc_STRVAR(SCTPSocketDoc_sendv, "sctp_sendv() method");

static PyObject *
SCTPSocketObject_sctp_sendv(SCTPSocketObject *self, PyObject *args)
{
    int iovcnt, addrcnt = 0, flags = 0, noc;
    unsigned int infotype;
    struct iovec *iov;
    struct sockaddr *addrs = NULL;
    void *info;
    union {
	struct sctp_sndinfo snd;
	struct sctp_prinfo pr;
	struct sctp_authinfo auth;
	struct sctp_sendv_spa spa;
    } info_un;
    socklen_t infolen;
    PyObject *iov_obj, *addrs_obj = Py_None, *info_obj = Py_None, *ret = NULL;
    
    if (!PyArg_ParseTuple(
	    args, "O|OOi", &iov_obj, &addrs_obj, &info_obj, &flags))
	return NULL;
    if (obj_to_iovec(iov_obj, &iov, &iovcnt) < 0) {
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    if (addrs_obj != Py_None)
	if (obj_to_sockaddrs(
		addrs_obj, self->family, self->type, 2, &addrs, &addrcnt) < 0) {
	    __SCTPErr(self, __FUNC__);
	    iovec_free(iov, iovcnt);
	    return NULL;
	}
    if (info_obj == Py_None) {
	info = NULL;
	infolen = 0;
	infotype = SCTP_SENDV_NOINFO;
    }
    else if (SCTPSndInfoObject_Check(info_obj)) {
	SCTPSndInfo2C((SCTPSndInfoObject *) info_obj, &info_un.snd);
	info = &info_un.snd;
	infolen = sizeof(info_un.snd);
	infotype = SCTP_SENDV_SNDINFO;
    }
    else if (SCTPPrInfoObject_Check(info_obj)) {
	SCTPPrInfo2C((SCTPPrInfoObject *) info_obj, &info_un.pr);
	info = &info_un.pr;
	infolen = sizeof(info_un.pr);
	infotype = SCTP_SENDV_PRINFO;
    }
    else if (SCTPAuthInfoObject_Check(info_obj)) {
	SCTPAuthInfo2C((SCTPAuthInfoObject *) info_obj, &info_un.auth);
	info = &info_un.auth;
	infolen = sizeof(info_un.auth);
	infotype = SCTP_SENDV_AUTHINFO;
    }
    else if (SCTPSendvSpaObject_Check(info_obj)) {
	SCTPSendvSpa2C((SCTPSendvSpaObject *) info_obj, &info_un.spa);
	info = &info_un.spa;
	infolen = sizeof(info_un.spa);
	infotype = SCTP_SENDV_SPA;
    }
    else {
	PyErr_SetString(
	    PyExc_TypeError, "arg3: must be an `sctp_[snd|pr|auth]info' "
	    "or a sctp_sendv_spa object or `None'"
	    );
	__SCTPErr(self, __FUNC__);
	goto err;
    }
    Py_BEGIN_ALLOW_THREADS
    noc = sctp_sendv(
	self->fd, iov, iovcnt, addrs, addrcnt, info, infolen, infotype, flags);
    Py_END_ALLOW_THREADS
    if (noc < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	    __SCTPErr(self, __FUNC__);
	goto err;
    }
    ret = Py_BuildValue("i", noc);
err:
    iovec_free(iov, iovcnt);
    PyMem_Free(addrs);
    return ret;
}

PyDoc_STRVAR(SCTPSocketDoc_peeloff, "sctp_peeloff() method");

static PyObject *
SCTPSocketObject_sctp_peeloff(SCTPSocketObject *self, PyObject *args)
{
    int sd;
    sctp_assoc_t assoc_id;
    PyObject *ret;
    
    if (!PyArg_ParseTuple(args, "i", &assoc_id))
	return NULL;
    Py_BEGIN_ALLOW_THREADS
    sd = sctp_peeloff(self->fd, assoc_id);
    Py_END_ALLOW_THREADS
    if (sd < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	    __SCTPErr(self, __FUNC__);
	    return NULL;
    }
    ret = sockfd_to_sctpsock(sd);
    if (!ret) {
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    return ret;
}

PyDoc_STRVAR(SCTPSocketDoc__getsockopt, "wrapper for libc getsockopt()");

static PyObject *
SCTPSocketObject__getsockopt(SCTPSocketObject *self, PyObject *args)
{
    int level, optname, rcode;
    char *buf;
    void *optval;
    Py_ssize_t optlen;
    PyObject *bytes, *ret = NULL;
    
    if (!PyArg_ParseTuple(
	    args, "iiO!", &level, &optname, &PyBytes_Type, &bytes))
	return NULL;
    if (PyBytes_AsStringAndSize(bytes, &buf, &optlen) < 0) {
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    optval = PyMem_Malloc(optlen);
    if (!optval)
	return PyErr_NoMemory();
    (void) memcpy(optval, buf, optlen);
    Py_BEGIN_ALLOW_THREADS
    rcode = getsockopt(self->fd, level, optname, optval, (socklen_t *) &optlen);
    Py_END_ALLOW_THREADS
    if (rcode < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	    __SCTPErr(self, __FUNC__);
	goto err;
    }
    ret = PyBytes_FromStringAndSize(optval, optlen);
err:
    PyMem_Free(optval);
    return ret;
}

/* For internal use only, method accept() must return a SCTPSocketObject */

static PyObject *
SCTPSocketObject_accept(SCTPSocketObject *self)
{
    int sd;
    struct sockaddr_storage addr;
    socklen_t addrlen = sizeof(addr);
    PyObject *ret = NULL, *py_sock = NULL, *py_addr = NULL;

    Py_BEGIN_ALLOW_THREADS
    sd = accept(self->fd, (struct sockaddr *) &addr, &addrlen);
    Py_END_ALLOW_THREADS
    if (sd < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    py_sock = sockfd_to_sctpsock(sd);
    if (!py_sock)
	goto err;
    py_addr = sockaddr_to_obj((struct sockaddr *) &addr, addrlen);
    if (!py_addr)
	goto err;
    ret = Py_BuildValue("(OO)", py_sock, py_addr);
err:
    if (!ret) {
	(void) close(sd);
	__SCTPErr(self, __FUNC__);
    }
    Py_XDECREF(py_sock);
    Py_XDECREF(py_addr);
    return ret;
}

/* For internal use only */

#define SCTP_HMAC_IDENT_MAX 64

static int
hmac_ident_conv(PyObject *obj, struct sctp_hmacalgo **shmac)
{
    int ok = 0;
    uint16_t *id;
    
    if (!PyTuple_Check(obj) || !PyTuple_Size(obj)) {
	PyErr_SetString(PyExc_TypeError, "arg3 must be a non empty tuple");
	return 0;
    }
    *shmac = PyMem_Calloc(
	sizeof(**shmac) + PyTuple_GET_SIZE(obj) * sizeof(uint16_t), 1);
    if (!*shmac) {
	(void) PyErr_NoMemory();
	return 0;
    }
    (*shmac)->shmac_number_of_idents = PyTuple_GET_SIZE(obj);
    id = (*shmac)->shmac_idents;
    for (Py_ssize_t pos = 0; pos < PyTuple_GET_SIZE(obj); pos++, id++) {
	PyObject *item = PyTuple_GET_ITEM(obj, pos);
	
	if (!PyLong_Check(item)) {
	    (void) PyErr_Format(
		PyExc_TypeError, "arg3: item#%zd is not an integer", pos + 1
		);
	    PyMem_Free(*shmac);
	    return 0;
	}
	*id = (uint16_t) PyLong_AsLong(item);
	if (*id == SCTP_AUTH_HMAC_ID_SHA1)
	    ok = 1;
    }
    if (!ok) {
	PyErr_SetString(
	    PyExc_ValueError,
	    "arg3: mandatory HMAC `SCTP_AUTH_HMAC_ID_SHA1' is missing"
	    );
	PyMem_Free(*shmac);
	return 0;
    }
    return 1;
}

static PyObject *
SCTPSocketObject_gso_hmac_ident(SCTPSocketObject *self, PyObject *args)
{
    int rcode;
    struct sctp_hmacalgo *shmac = NULL;
    socklen_t optlen;

    if (!PyArg_ParseTuple(args, "|O&", hmac_ident_conv, &shmac)) {
	__SCTPErr(self, "setsockopt");
	return NULL;
    }
    if (!shmac) {
	uint16_t *id;
	PyObject *ret = NULL;
	
	optlen = sizeof(*shmac) + SCTP_HMAC_IDENT_MAX * sizeof(uint16_t);
	shmac = PyMem_Calloc(optlen, 1);
	if (!shmac)
	    return PyErr_NoMemory();
	Py_BEGIN_ALLOW_THREADS
	rcode = getsockopt(
	    self->fd, IPPROTO_SCTP, SCTP_HMAC_IDENT, shmac, &optlen);
	Py_END_ALLOW_THREADS
	if (rcode < 0) {
	    (void) PyErr_Format(
		PyExc_OSError, "[%d, %s]", errno, strerror(errno)
		);
	    __SCTPErr(self, "getsockopt");
	    goto err;
	}
	ret = PyTuple_New(shmac->shmac_number_of_idents);
	if (!ret) {
	    __SCTPErr(self, "getsockopt");
	    goto err;
	}
	id = shmac->shmac_idents;
	for (Py_ssize_t pos = 0; pos < shmac->shmac_number_of_idents;
	     pos++, id++)
	    PyTuple_SET_ITEM(ret, pos, Py_BuildValue("H", *id));
      err:
	PyMem_Free(shmac);
	return ret;
    }
    optlen = sizeof(*shmac) + shmac->shmac_number_of_idents * sizeof(uint16_t);
    Py_BEGIN_ALLOW_THREADS
    rcode = setsockopt(
	    self->fd, IPPROTO_SCTP, SCTP_HMAC_IDENT, shmac, optlen);
    Py_END_ALLOW_THREADS
    if (rcode < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	__SCTPErr(self, "setsockopt");
	PyMem_Free(shmac);
	return NULL;
    }
    PyMem_Free(shmac);
    Py_RETURN_NONE;
}

/* For internal use only */

static PyObject *
SCTPSocketObject_gso_get_assoc_id_list(SCTPSocketObject *self)
{
    int rcode;
    uint32_t nids;
    sctp_assoc_t *id;
    struct sctp_assoc_ids *optval;
    socklen_t optlen = sizeof(nids);
    PyObject *ret = NULL;

    Py_BEGIN_ALLOW_THREADS
    rcode = getsockopt(
	self->fd, IPPROTO_SCTP, SCTP_GET_ASSOC_NUMBER, &nids, &optlen);
    Py_END_ALLOW_THREADS
    if (rcode < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	__SCTPErr(self, "getsockopt[IPPROTO_SCTP/SCTP_GET_ASSOC_NUMBER]");
	return NULL;
    }
    if (!nids)
	return PyTuple_New(0);
    optlen = sizeof(*optval) + nids * sizeof(optval->gaids_assoc_id[0]);
    optval = PyMem_Calloc(optlen, 1);
    if (!optval)
	return PyErr_NoMemory();
    Py_BEGIN_ALLOW_THREADS
    rcode = getsockopt(
	self->fd, IPPROTO_SCTP, SCTP_GET_ASSOC_ID_LIST, optval, &optlen);
    Py_END_ALLOW_THREADS
    if (rcode < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	__SCTPErr(self, "getsockopt[IPPROTO_SCTP/SCTP_GET_ASSOC_ID_LIST]");
	PyMem_Free(optval);
	goto err;
    }
    ret = PyTuple_New(nids);
    if (!ret) {
	__SCTPErr(self, __FUNC__);
	goto err;
    }
    id = optval->gaids_assoc_id;
    for (Py_ssize_t pos = 0; pos < nids; pos++, id++)
	PyTuple_SET_ITEM(ret, pos, Py_BuildValue("i", *id));
err:
    PyMem_Free(optval);
    return ret;
}

/* For internal use only */

static PyObject *
SCTPSocketObject_gso_get_auth_chunks(SCTPSocketObject *self, PyObject *args)
{
    int optname, rcode;
    sctp_assoc_t id = 0;
    uint8_t *gc;
    struct sctp_authchunks *optval;
    socklen_t optlen;
    PyObject *ret = NULL, *chunks;
    
    if (!PyArg_ParseTuple(args, "i|i", &optname, &id))
	return NULL;
    optlen = sizeof(*optval) + 256;
    optval = PyMem_Calloc(optlen, 1);
    if (!optval)
	return PyErr_NoMemory();
    optval->gauth_assoc_id = id;
    Py_BEGIN_ALLOW_THREADS
    rcode = getsockopt(self->fd, IPPROTO_SCTP, optname, optval, &optlen);
    Py_END_ALLOW_THREADS
    if (rcode < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	__SCTPErr(
	    self, "getsockopt[IPPROTO_SCTP/SCTP_(PEER|LOCAL)_AUTH_CHUNKS]"
	    );
	goto err;
    }
    ret = PyDict_New();
    if (!ret)
	goto err;
    if (PyDict_SetItemString(
	    ret, "gauth_assoc_id",
	    Py_BuildValue("i", optval->gauth_assoc_id)) < 0) {
	Py_DECREF(ret);
	ret = NULL;
	goto err;
    }
    chunks = PyTuple_New(optval->gauth_number_of_chunks);
    if (!chunks) {
	Py_DECREF(ret);
	ret = NULL;
	goto err;
    }
    gc = optval->gauth_chunks;
    for (Py_ssize_t pos = 0; pos < optval->gauth_number_of_chunks; pos++, gc++)
	PyTuple_SET_ITEM(chunks, pos, Py_BuildValue("B", *gc));
    if (PyDict_SetItemString(ret, "gauth_chunks", chunks) < 0) {
	Py_DECREF(chunks);
	Py_DECREF(ret);
	ret = NULL;
	goto err;
    }
err:
    PyMem_Free(optval);
    return ret;
}

/* For internal use only */

static PyObject *
SCTPSocketObject_gso_auth_key(SCTPSocketObject *self, PyObject *args)
{
    int rcode;
    socklen_t optlen;
    char *data;
    Py_ssize_t len = 0;
    PyObject *py_sca, *py_key;
    struct sctp_authkey *sca;
    
    if (!PyArg_ParseTuple(args, "O", &py_sca))
	return NULL;
    py_key = PyDict_GetItemString(py_sca, "sca_key");
    optlen = py_key == Py_None ? 0 : (socklen_t) PyTuple_GET_SIZE(py_key);
    if (optlen > 0)
	if (PyBytes_AsStringAndSize(py_key, &data, &len) < 0) {
	    __SCTPErr(self, "setsockopt[IPPROTO_SCTP/SCTP_AUTH_KEY]");
	    return NULL;
	}
    optlen += sizeof(*sca);
    sca = PyMem_Calloc(optlen, 1);
    if (!sca)
	return PyErr_NoMemory();
    sca->sca_assoc_id = (sctp_assoc_t) PyLong_AsLong(
	PyDict_GetItemString(py_sca, "sca_assoc_id"));
    sca->sca_keynumber = (uint16_t) PyLong_AsLong(
	PyDict_GetItemString(py_sca, "sca_keynumber"));
    sca->sca_keylength = (uint16_t) len;
    if (len > 0)
	(void) memcpy(sca->sca_key, data, len);
    Py_BEGIN_ALLOW_THREADS
    rcode = setsockopt(self->fd, IPPROTO_SCTP, SCTP_AUTH_KEY, sca, optlen);
    Py_END_ALLOW_THREADS
    if (rcode < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	__SCTPErr(self, "setsockopt[IPPROTO_SCTP/SCTP_AUTH_KEY]");
	PyMem_Free(sca);
	return NULL;
    }
    PyMem_Free(sca);
    Py_RETURN_NONE;
}

static PyMethodDef SCTPSocketMethods[] = {
    {"sctp_bindx", (PyCFunction) SCTPSocketObject_sctp_bindx,
     METH_VARARGS, SCTPSocketDoc_bindx},
    {"sctp_connectx", (PyCFunction) SCTPSocketObject_sctp_connectx,
     METH_VARARGS | METH_KEYWORDS, SCTPSocketDoc_connectx},
    {"sctp_getladdrs", (PyCFunction) SCTPSocketObject_sctp_getladdrs,
     METH_VARARGS, SCTPSocketDoc_getladdrs},
    {"sctp_getpaddrs", (PyCFunction) SCTPSocketObject_sctp_getpaddrs,
     METH_VARARGS, SCTPSocketDoc_getpaddrs},
    {"sctp_recvv", (PyCFunction) SCTPSocketObject_sctp_recvv, METH_VARARGS,
     SCTPSocketDoc_recvv},
    {"sctp_sendv", (PyCFunction) SCTPSocketObject_sctp_sendv, METH_VARARGS,
     SCTPSocketDoc_sendv},
    {"sctp_peeloff", (PyCFunction) SCTPSocketObject_sctp_peeloff, METH_VARARGS,
     SCTPSocketDoc_peeloff},
    {"_getsockopt", (PyCFunction) SCTPSocketObject__getsockopt, METH_VARARGS,
     SCTPSocketDoc__getsockopt},
    {"accept", (PyCFunction) SCTPSocketObject_accept, METH_NOARGS, NULL},
    {"gso_hmac_ident",
     (PyCFunction) SCTPSocketObject_gso_hmac_ident, METH_VARARGS, NULL},
    {"gso_get_assoc_id_list",
     (PyCFunction) SCTPSocketObject_gso_get_assoc_id_list, METH_NOARGS, NULL},
    {"gso_get_auth_chunks",
     (PyCFunction) SCTPSocketObject_gso_get_auth_chunks, METH_VARARGS, NULL},
    {"gso_auth_key",
     (PyCFunction) SCTPSocketObject_gso_auth_key, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}
};

/* MEMBERS */

/* GET/SET */

static PyObject *
SCTPSocketObject_get_sock(SCTPSocketObject *self, void *closure)
{
    Py_INCREF(self->sock);
    return self->sock;
}

static PyObject *
SCTPSocketObject_get_type(SCTPSocketObject *self, void *closure)
{
    return PyUnicode_FromString(
	self->type == SOCK_STREAM ? "one-to-one" : "one-to-many");
}

static PyGetSetDef SCTPSocketGetSet[] = {
    {"sctp_type", (getter) SCTPSocketObject_get_type, NULL,
     "SCTP type", NULL},
    {"sock", (getter) SCTPSocketObject_get_sock, NULL,
     "underlying socket", NULL},
    {NULL, NULL, NULL, NULL, NULL}
};

/* SPECIAL METHODS */

static void
SCTPSocketObject_dealloc(SCTPSocketObject *self)
{
    Py_XDECREF(self->sock);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
SCTPSocketObject_str(SCTPSocketObject *self)
{
    return PyUnicode_FromFormat(
	"<sctp_socket object, fd=%d, family=%d, type=%d [%s], proto=%d>",
	self->fd, self->family, self->type, self->type == SOCK_STREAM ?
	"one-to-one" : "one-to-many", IPPROTO_SCTP
	);
}

static int
SCTPSocketObject_init(SCTPSocketObject *self, PyObject *args, PyObject *kwds)
{
    int family, type, proto = IPPROTO_SCTP, fileno = -1;
    PyObject *fdo;

    if (!PyArg_ParseTuple(args, "ii|ii", &family, &type, &proto, &fileno))
	return -1;
    if (family != AF_INET && family != AF_INET6)  {
	PyErr_SetString(
	    SCTPErr, "invalid family, must be `AF_INET' or `AF_INET6'"
	    );
	return -1;
    }
    if (type != SOCK_STREAM && type != SOCK_SEQPACKET) {
	PyErr_SetString(
	    SCTPErr, "invalid type, must be `SOCK_STREAM' or `SOCK_SEQPACKET'"
	    );
	return -1;
    }
    if (proto != IPPROTO_SCTP) {
	PyErr_SetString(SCTPErr, "invalid protocol, must be `IPPROTO_SCTP'");
	return -1;
    }
    if (fileno < 0)
	self->sock = PyObject_CallMethod(
	    SocketModule, "socket", "iii", family, type, proto);
    else
	self->sock = PyObject_CallMethod(
	    SocketModule, "socket", "iiii", family, type, proto, fileno);
    if (!self->sock)
	return -1;
    fdo = PyObject_CallMethod(self->sock, "fileno", NULL);
    if (!fdo)
	return -1;
    self->fd = (int) PyLong_AsLong(fdo);
    self->family = family;
    self->type = type;
    return 0;
}

static PyObject *
SCTPSocketObject_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    SCTPSocketObject *self;
    
    self = (SCTPSocketObject *) type->tp_alloc(type, 0);
    if (self) {
	self->sock = NULL;
	self->fd = -1;
	self->family = 0;
	self->type = 0;
    }
    return (PyObject *) self;
}

static PyObject *
SCTPSocketObject_getattro(SCTPSocketObject *self, PyObject *name)
{
    PyObject *attr;

    attr = PyObject_GenericGetAttr((PyObject *) self, name);
    if (attr)
	return attr;
    PyErr_Clear();
    return PyObject_GetAttr(self->sock, name);
}

/* TYPE */

static PyTypeObject SCTPSocketType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sctp_socket_",
    .tp_doc = SCTPSocketDoc,
    .tp_basicsize = sizeof(SCTPSocketObject),
    .tp_repr = (reprfunc) SCTPSocketObject_str,
    .tp_str = (reprfunc) SCTPSocketObject_str,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_methods = SCTPSocketMethods,
    .tp_getset = SCTPSocketGetSet,
    .tp_init = (initproc) SCTPSocketObject_init,
    .tp_new = SCTPSocketObject_new,
    .tp_dealloc = (destructor) SCTPSocketObject_dealloc,
    .tp_getattro = (getattrofunc) SCTPSocketObject_getattro
};

/*****************************************************************************
 * MODULE METHODS
 *****************************************************************************/

PyDoc_STRVAR(
    SCTP_ipaddr_to_sockaddr_storageDoc,
    "convert an IP address to struct sockaddr_storage (bytes object)"
    );

static PyObject *
SCTP_ipaddr_to_sockaddr_storage(PyObject *self, PyObject *args)
{
    socklen_t sslen;
    struct sockaddr_storage ss;
    PyObject *addr_obj;

    if (!PyArg_ParseTuple(args, "O", &addr_obj))
	return NULL;
    (void) memset(&ss, 0, sizeof(ss));
    if (obj_to_sockaddr(
	    addr_obj, AF_UNSPEC, SOCK_STREAM,
	    (struct sockaddr *) &ss, &sslen) < 0) {
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    return PyBytes_FromStringAndSize((const char *) &ss, sizeof(ss));
}

PyDoc_STRVAR(
    SCTP_sockaddr_storage_to_ipaddrDoc,
    "convert a struct sockaddr_storage (bytes object) to an IP address"
    );

static PyObject *
SCTP_sockaddr_storage_to_ipaddr(PyObject *self, PyObject *args)
{
    char *buf;
    Py_ssize_t blen;
    PyObject *bytes;
    
    if (!PyArg_ParseTuple(args, "O!", &PyBytes_Type, &bytes))
	return NULL;
    if (PyBytes_AsStringAndSize(bytes, &buf, &blen) < 0) {
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    return sockaddr_to_obj((struct sockaddr *) buf, blen);
}

static PyMethodDef SCTPMethods[] = {
    {"ipaddr_to_sockaddr_storage",
     (PyCFunction) SCTP_ipaddr_to_sockaddr_storage, METH_VARARGS,
     SCTP_ipaddr_to_sockaddr_storageDoc},
    {"sockaddr_storage_to_ipaddr",
     (PyCFunction) SCTP_sockaddr_storage_to_ipaddr, METH_VARARGS,
     SCTP_sockaddr_storage_to_ipaddrDoc},
    {NULL, NULL, 0, NULL}
};

/*****************************************************************************
 * MODULE INITIALIZATION
 *****************************************************************************/

PyDoc_STRVAR(
    SCTPDoc, "Extension for SCTP sockets - C module `" MODS_DIR "." "sctp'"
    );

static PyModuleDef SCTPModule = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = MODS_DIR "." "sctp",
    .m_doc = SCTPDoc,
    .m_size = -1,
    .m_methods = SCTPMethods
};

PyMODINIT_FUNC
PyInit_sctp(void)
{
    PyObject* m;

    if (sctp_info_import_capi() < 0)
	return NULL;
    SocketModule = PyImport_ImportModule("socket");
    if (!SocketModule) {
	PyErr_SetString(PyExc_ImportError, "can't import module `socket'");
	return NULL;
    }
    if (PyType_Ready(&SCTPSocketType) < 0) {
	Py_DECREF(SocketModule);
        return NULL;
    }
    m = PyModule_Create(&SCTPModule);
    if (!m) {
	Py_DECREF(SocketModule);
        return NULL;
    }
    if (SCTPModule_add_constants(m) < 0) {
	Py_DECREF(m);
	return NULL;
    }
    SCTPErr = PyErr_NewException(PKG_NAME "." "error", NULL, NULL);
    Py_INCREF(SCTPErr);
    if (PyModule_AddObject(
	    m, "SCTPError", (PyObject *) SCTPErr) < 0) {
	Py_DECREF(SocketModule);
	Py_DECREF(m);
        Py_DECREF(&SCTPSocketType);
        return NULL;
    }
    Py_INCREF(&SCTPSocketType);
    if (PyModule_AddObject(
	    m, "sctp_socket_", (PyObject *) &SCTPSocketType) < 0) {
	Py_DECREF(SocketModule);
	Py_DECREF(m);
        Py_DECREF(&SCTPSocketType);
	Py_DECREF(SCTPErr);
        return NULL;
    }
    return m;
}

/*****************************************************************************
 * LOCAL FUNCTION DEFINITIONS
 *****************************************************************************/

static int
SCTPModule_add_constants(PyObject *m)
{
    if (PyModule_AddIntConstant(m, "IPPROTO_SCTP", IPPROTO_SCTP) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_FUTURE_ASSOC", SCTP_FUTURE_ASSOC) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_CURRENT_ASSOC", SCTP_CURRENT_ASSOC) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_ALL_ASSOC", SCTP_ALL_ASSOC) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_SNDINFO", SCTP_SNDINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_RECVRCVINFO", SCTP_RECVRCVINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_RECVNXTINFO", SCTP_RECVNXTINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_SENDV_NOINFO", SCTP_SENDV_NOINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SENDV_SNDINFO", SCTP_SENDV_SNDINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_SENDV_PRINFO", SCTP_SENDV_PRINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SENDV_AUTHINFO", SCTP_SENDV_AUTHINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_SENDV_SPA", SCTP_SENDV_SPA) < 0)
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
    if (PyModule_AddIntConstant(m, "SCTP_RECVV_NOINFO", SCTP_RECVV_NOINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_RECVV_RCVINFO", SCTP_RECVV_RCVINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_RECVV_NXTINFO", SCTP_RECVV_NXTINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_RECVV_RN", SCTP_RECVV_RN) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_INIT", SCTP_INIT) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_INITMSG", SCTP_INITMSG) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_BINDX_ADD_ADDR", SCTP_BINDX_ADD_ADDR) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_BINDX_REM_ADDR", SCTP_BINDX_REM_ADDR) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_GET_PEER_ADDR_INFO", SCTP_GET_PEER_ADDR_INFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_UNCONFIRMED", SCTP_UNCONFIRMED) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_ACTIVE", SCTP_ACTIVE) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_INACTIVE", SCTP_INACTIVE) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_PEER_ADDR_PARAMS", SCTP_PEER_ADDR_PARAMS) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SPP_HB_ENABLE", SPP_HB_ENABLE) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SPP_HB_DISABLE", SPP_HB_DISABLE) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SPP_HB_DEMAND", SPP_HB_DEMAND) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SPP_HB_TIME_IS_ZERO", SPP_HB_TIME_IS_ZERO) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SPP_PMTUD_ENABLE", SPP_PMTUD_ENABLE) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SPP_PMTUD_DISABLE", SPP_PMTUD_DISABLE) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SPP_IPV6_FLOWLABEL", SPP_IPV6_FLOWLABEL) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SPP_DSCP", SPP_DSCP) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_RTOINFO", SCTP_RTOINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_ASSOCINFO", SCTP_ASSOCINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_NODELAY", SCTP_NODELAY) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_AUTOCLOSE", SCTP_AUTOCLOSE) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_PRIMARY_ADDR", SCTP_PRIMARY_ADDR) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_ADAPTATION_LAYER", SCTP_ADAPTATION_LAYER) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_DISABLE_FRAGMENTS", SCTP_DISABLE_FRAGMENTS) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_I_WANT_MAPPED_V4_ADDR", SCTP_I_WANT_MAPPED_V4_ADDR) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_HMAC_IDENT", SCTP_HMAC_IDENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_HMAC_ID_SHA1", SCTP_AUTH_HMAC_ID_SHA1) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_HMAC_ID_SHA256", SCTP_AUTH_HMAC_ID_SHA256) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_ACTIVE_KEY", SCTP_AUTH_ACTIVE_KEY) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_MAXSEG", SCTP_MAXSEG) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_DELAYED_SACK", SCTP_DELAYED_SACK) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_FRAGMENT_INTERLEAVE", SCTP_FRAGMENT_INTERLEAVE) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_PARTIAL_DELIVERY_POINT", SCTP_PARTIAL_DELIVERY_POINT) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_AUTO_ASCONF", SCTP_AUTO_ASCONF) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_MAX_BURST",  SCTP_MAX_BURST) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_CONTEXT",  SCTP_CONTEXT) < 0)
	return -1;
#ifdef HAVE_FREEBSD
    if (PyModule_AddIntConstant(
	    m, "SCTP_EXPLICIT_EOR",  SCTP_EXPLICIT_EOR) < 0)
	return -1; /* (constant defined in RFC-6458, but not in Linux) */
#endif /* HAVE_FREEBSD */
    if (PyModule_AddIntConstant(m, "SCTP_REUSE_PORT",  SCTP_REUSE_PORT) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_EVENT",  SCTP_EVENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_DEFAULT_SNDINFO", SCTP_DEFAULT_SNDINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_DEFAULT_PRINFO", SCTP_DEFAULT_PRINFO) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_STATUS",  SCTP_STATUS) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_CLOSED",  SCTP_CLOSED) < 0)
	return -1;
#ifdef HAVE_FREEBSD
    if (PyModule_AddIntConstant(m, "SCTP_LISTEN",  SCTP_LISTEN) < 0)
	return -1; /* (constant defined in RFC-6458, but not in Linux) */
#endif /* HAVE_FREEBSD */
    if (PyModule_AddIntConstant(m, "SCTP_COOKIE_WAIT",  SCTP_COOKIE_WAIT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_COOKIE_ECHOED",  SCTP_COOKIE_ECHOED) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_ESTABLISHED",  SCTP_ESTABLISHED) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SHUTDOWN_PENDING",  SCTP_SHUTDOWN_PENDING) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SHUTDOWN_SENT",  SCTP_SHUTDOWN_SENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SHUTDOWN_RECEIVED",  SCTP_SHUTDOWN_RECEIVED) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SHUTDOWN_ACK_SENT",  SCTP_SHUTDOWN_ACK_SENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_GET_ASSOC_NUMBER",  SCTP_GET_ASSOC_NUMBER) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_GET_ASSOC_ID_LIST",  SCTP_GET_ASSOC_ID_LIST) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SET_PEER_PRIMARY_ADDR",  SCTP_SET_PEER_PRIMARY_ADDR) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_CHUNK",  SCTP_AUTH_CHUNK) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_KEY",  SCTP_AUTH_KEY) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_DEACTIVATE_KEY",  SCTP_AUTH_DEACTIVATE_KEY) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_DELETE_KEY",  SCTP_AUTH_DELETE_KEY) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_PEER_AUTH_CHUNKS",  SCTP_PEER_AUTH_CHUNKS) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_LOCAL_AUTH_CHUNKS",  SCTP_LOCAL_AUTH_CHUNKS) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_INITMSG_CSIZE", sizeof(struct sctp_initmsg)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_PADDRPARAMS_CSIZE", sizeof(struct sctp_paddrparams)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_PADDRINFO_CSIZE", sizeof(struct sctp_paddrinfo)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_RTOINFO_CSIZE", sizeof(struct sctp_rtoinfo)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_ASSOCPARAMS_CSIZE", sizeof(struct sctp_assocparams)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SETPRIM_CSIZE", sizeof(struct sctp_setprim)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SETADAPTATION_CSIZE",
	    sizeof(struct sctp_setadaptation)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_MAXSEG_CSIZE", sizeof(struct sctp_assoc_value)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_ACTIVE_KEY_CSIZE", sizeof(struct sctp_authkeyid)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_DELAYED_SACK_CSIZE", sizeof(struct sctp_sack_info)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SNDINFO_CSIZE", sizeof(struct sctp_sndinfo)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_DEFAULT_PRINFO_CSIZE",
	    sizeof(struct sctp_default_prinfo)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_STATUS_CSIZE", sizeof(struct sctp_status)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SET_PEER_PRIMARY_ADDR_CSIZE",
	    sizeof(struct sctp_setpeerprim)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_CHUNK_CSIZE", sizeof(struct sctp_authchunk)) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SOCKADDR_STORAGE_CSIZE", sizeof(struct sockaddr_storage)) < 0)
	return -1;
    return 0;
}

static int
obj_to_iovec(PyObject *obj, struct iovec **iov, int *iovcnt)
{
    int ret = 0;
    PyObject *item, *iter = PyObject_GetIter(obj);

    if (!iter) {
	PyErr_SetString(
	    PyExc_TypeError, "arg1 must be an iterable of bytes objects"
	    );
	return -1;
    }
    *iov = NULL;
    *iovcnt = 0;
    while ((item = PyIter_Next(iter))) {
	if (!PyBytes_Check(item)) {
	    Py_DECREF(item);
	    (void) PyErr_Format(
		PyExc_TypeError, "arg1: item#%d is not a bytes object",
		*iovcnt
		);
	    ret = -1;
	    goto err;
	} 
	*iovcnt += 1;
	Py_DECREF(item);
    }
    if (!*iovcnt) {
	PyErr_SetString(PyExc_ValueError, "arg1 has zero size");
	ret = -1;
	goto err;
    }
    *iov = PyMem_Malloc(*iovcnt * sizeof(**iov));
    if (!*iov) {
	(void) PyErr_NoMemory();
	ret = -1;
	goto err;
    }
    Py_DECREF(iter);
    iter = PyObject_GetIter(obj);
    (void) memset(*iov, 0, *iovcnt * sizeof(**iov));
    for (struct iovec *ptr = *iov; (item = PyIter_Next(iter)); ptr++) {
	 char *buf;
	 Py_ssize_t len;
	 
	 (void) PyBytes_AsStringAndSize(item, &buf, &len);
	 ptr->iov_base = PyMem_Malloc(len);
	 if (!ptr->iov_base) {
	     Py_DECREF(item);
	     (void) PyErr_NoMemory();
	     ret = -1;
	     goto err;
	 }
	 (void) memcpy(ptr->iov_base, buf, len);
	 ptr->iov_len = len;
	 Py_DECREF(item);
     }
err:
    if (ret < 0)
	iovec_free(*iov, *iovcnt);
    Py_DECREF(iter);
    return ret;
}

static void
iovec_free(struct iovec *iov, int iovcnt)
{
    if (!iov || !iovcnt)
	return;
    for (struct iovec *ptr = iov; ptr - iov < iovcnt; ptr++)
	PyMem_Free(ptr->iov_base);
    PyMem_Free(iov);
}

static int
obj_to_sockaddrs(
    PyObject *obj, int family, int socktype, int an, struct sockaddr **addrs,
    int *addrcnt)
{
    int ret = 0;
    socklen_t tlen;
    PyObject *item, *iter = PyObject_GetIter(obj);

    if (!iter) {
	(void) PyErr_Format(
	    PyExc_TypeError,
	    "arg%d must be an iterable of IPv4/v6 addresses or None", an
	    );
	return -1;
    }
    *addrs = NULL;
    *addrcnt = tlen = 0;
    while ((item = PyIter_Next(iter))) {
	socklen_t len;
	struct sockaddr *ptr;
	struct sockaddr_storage tmp;

	if (obj_to_sockaddr(
		item, family, socktype, (struct sockaddr *) &tmp, &len) < 0) {
	    PyObject *type, *value, *tb;

	    PyErr_Fetch(&type, &value, &tb);
	    (void) PyErr_Format(
		type, "arg%d: address#%d: %S", an, *addrcnt + 1, value
		);
	    PyMem_Free(*addrs);
	    Py_DECREF(item);
	    ret = -1;
	    goto err;
	}
	ptr = PyMem_Realloc(*addrs, tlen + len);
	if (!ptr) {
	    PyErr_SetNone(PyExc_MemoryError); 
	    PyMem_Free(*addrs);
	    Py_DECREF(item);
	    ret = -1;
	    goto err;
	}
	*addrs = ptr;
	(void) memcpy((char *) *addrs + tlen, &tmp, len);
	tlen += len;
	*addrcnt += 1;
	Py_DECREF(item);
    }
err:
    Py_DECREF(iter);
    return ret;
}

static int
obj_to_sockaddr(
    PyObject *obj, int family, int socktype, struct sockaddr *addr,
    socklen_t *addrlen)
{
    int ecode;
    char serv[NI_MAXSERV];
    const char *node, *service;
    struct addrinfo *res, hints = {
	.ai_socktype = socktype,
	.ai_protocol = IPPROTO_SCTP
    };
    
    if (!PyTuple_Check(obj) ||
	(PyTuple_GET_SIZE(obj) != 2 && PyTuple_GET_SIZE(obj) != 4)) {
	PyErr_SetString(
	    PyExc_TypeError,
	    "IP address must be a 2-tuple (IPv4) or a 4-tuple (IPv6)"
	    );
	return -1;
    }
    if (!PyUnicode_Check(PyTuple_GET_ITEM(obj, 0))) {
	PyErr_SetString(
	    PyExc_TypeError, "invalid IP address : item#1 must be a `str'"
	    );
	return -1;
    }
    node = PyUnicode_AsUTF8(PyTuple_GET_ITEM(obj, 0));
    if (PyLong_Check(PyTuple_GET_ITEM(obj, 1))) {
	snprintf(
	    serv, sizeof(serv), "%ld", PyLong_AsLong(PyTuple_GET_ITEM(obj, 1))
	    );
	service = serv;
    }
    else if (PyUnicode_Check(PyTuple_GET_ITEM(obj, 1)))
	service = PyUnicode_AsUTF8(PyTuple_GET_ITEM(obj, 1));
    else {
	PyErr_SetString(
	    PyExc_TypeError,
	    "invalid IP address : item#2 must be a `str' or an `int'"
	    );
	return -1;
    }
    hints.ai_family = PyTuple_GET_SIZE(obj) == 2 ? AF_INET : AF_INET6;
    if (hints.ai_family == AF_INET6 && family == AF_INET) {
	PyErr_SetString(
	    PyExc_TypeError,
	    "address is an IPv6 address but socket is an IPv4 socket"
	    );
	return -1;
    }
    if (hints.ai_family == AF_INET6) {
	if (!PyLong_Check(PyTuple_GET_ITEM(obj, 2))) {
	    PyErr_SetString(
		PyExc_TypeError, "invalid IP address : item#3 must be an `int'"
	    );
	    return -1;
	}
	if (!PyLong_Check(PyTuple_GET_ITEM(obj, 3))) {
	    PyErr_SetString(
		PyExc_TypeError, "invalid IP address : item#4 must be an `int'"
	    );
	    return -1;
	}
    }
    ecode = getaddrinfo(node, service, &hints, &res);
    if (ecode) {
	(void) PyErr_Format(
	    SCTPErr, "getaddrinfo(): [%d, %s]", ecode, gai_strerror(ecode)
	    );
	return -1;
    }
    (void) memcpy(addr, res->ai_addr, res->ai_addrlen);
    if (hints.ai_family == AF_INET6) {
	((struct sockaddr_in6 *) addr)->sin6_flowinfo =
	    (uint32_t) PyLong_AsLong(PyTuple_GET_ITEM(obj, 2));
	((struct sockaddr_in6 *) addr)->sin6_scope_id =
	    (uint32_t) PyLong_AsLong(PyTuple_GET_ITEM(obj, 3));
    }
    *addrlen = res->ai_addrlen;
    freeaddrinfo(res);
    return 0;
}

static PyObject *
sockaddr_to_obj(struct sockaddr *sa, socklen_t salen)
{
    char host[NI_MAXHOST] = "???", serv[NI_MAXSERV] = "???";
    uint16_t port;

    (void) getnameinfo(
	sa, salen, host, sizeof(host), serv,
	sizeof(serv), NI_NUMERICHOST | NI_NUMERICSERV
	);
    port = (uint16_t) strtoul(serv, NULL, 10);
    if (sa->sa_family == AF_INET)
	return Py_BuildValue("(sH)", host, port);
    return Py_BuildValue(
	"(sHII)", host, port, ((struct sockaddr_in6 *) sa)->sin6_flowinfo,
	((struct sockaddr_in6 *) sa)->sin6_scope_id
	);
}

static PyObject *
sctp_getlpaddrs(SCTPSocketObject *self, PyObject *args, getlpaddrs_t func)
{
    int rcode;
    const char *fname = func == sctp_getladdrs ? "sctp_getladdrs" :
	"sctp_getpaddrs";
    sctp_assoc_t assoc_id = 0;
    struct sockaddr *addrs, *ptr;
    PyObject *ret;
    
    if (!PyArg_ParseTuple(args, "|i", &assoc_id))
	return NULL;
    Py_BEGIN_ALLOW_THREADS
    rcode = func(self->fd, assoc_id, &addrs);
    Py_END_ALLOW_THREADS
    if (rcode < 0) {
	(void) PyErr_Format(
	    PyExc_OSError, "[%d, %s]", errno, strerror(errno)
	    );
	__SCTPErr(self, fname);
	return NULL;
    }
    if (!rcode)
	Py_RETURN_NONE;
    ret = PyTuple_New(rcode);
    if (!ret)
	goto err;
    ptr = addrs;
    for (int i = 0; i < rcode; i++) {
	socklen_t len = ptr->sa_family == AF_INET ?
	    sizeof(struct sockaddr_in) : sizeof(struct sockaddr_in6);
	PyObject *addr = sockaddr_to_obj(ptr, len);

	PyTuple_SET_ITEM(ret, i, addr);
	ptr = (struct sockaddr *) ((char *) ptr + len);
    }
err:
    sctp_freepaddrs(addrs);
    return ret;
}

static PyObject *
sockfd_to_sctpsock(int sd)
{
    int type, family;
    socklen_t optlen;
    PyObject *ret;
    
    ret = SCTPSocketType.tp_new(&SCTPSocketType, NULL, NULL);
    if (!ret) {
	(void) close(sd);
	return NULL;
    }
    optlen = sizeof(type);
    (void) getsockopt(sd, SOL_SOCKET, SO_TYPE, &type, &optlen);
    optlen = sizeof(family);
    (void) getsockopt(sd, SOL_SOCKET, SO_DOMAIN, &family, &optlen);
    if (SCTPSocketType.tp_init(
	    ret,
	    Py_BuildValue("(iiii)", family, type, IPPROTO_SCTP, sd),
	    NULL) < 0) {
	(void) close(sd);
	Py_DECREF(ret);
	return NULL;
    }
    return ret;
}

/*****************************************************************************
 * EXPORTED FUNCTIONS DEFINITIONS
 *****************************************************************************/
