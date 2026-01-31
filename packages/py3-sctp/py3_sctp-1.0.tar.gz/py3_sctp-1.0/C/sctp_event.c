/*****************************************************************************
 * INCLUDED FILES & MACRO DEFINITIONS
 *****************************************************************************/

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/sctp.h>

#include <sctp_error.h>

typedef struct {
    char *name;
    PyObject *value;
} field_t;

/*****************************************************************************
 * OBJECT(s) DEFINITION(s)
 *****************************************************************************/

/*****************************************************************************
 * LOCAL VARIABLES DECLARATIONS
 *****************************************************************************/

/*****************************************************************************
 * LOCAL FUNCTIONS DECLARATIONS
 *****************************************************************************/

static int SCTPEventModule_add_constants(PyObject *);
static PyObject *parse_assoc_change(void *);
static PyObject *parse_peer_addr_change(void *);
static PyObject *parse_remote_error(void *);
static PyObject *parse_shutdown_event(void *);
static PyObject *parse_adaptation_event(void *);
static PyObject *parse_pdapi_event(void *);
static PyObject *parse_authkey_event(void *);
static PyObject *parse_sender_dry_event(void *);
#ifdef HAVE_FREEBSD
static PyObject *parse_notifs_stop_event(void *);
#endif /* HAVE_FREEBSD */
static PyObject *parse_send_failed_event(void *);
static PyObject *event_to_dict(field_t *);
static PyObject *sockaddr_to_ip(struct sockaddr_storage);
static PyObject *sndinfo_to_dict(struct sctp_sndinfo);

/*****************************************************************************
 * EXPORTED FUNCTIONS DECLARATIONS
 *****************************************************************************/

/*****************************************************************************
 * MODULE METHODS
 *****************************************************************************/

PyDoc_STRVAR(
    SCTPEvent_parse_notificationDoc,
    "parses an event as a bytes object and returns an appropriate dictionary"
    );

static PyObject *
SCTPEvent_parse_notification(PyObject *self, PyObject *args)
{
    char *buf;
    void *data;
    Py_ssize_t len;
    PyObject *py_event, *ret;
    union sctp_notification *snp;
    
    if (!PyArg_ParseTuple(args, "O!", &PyBytes_Type, &py_event)) {
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    if (PyBytes_AsStringAndSize(py_event, &buf, &len) < 0) {
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    data = PyMem_Malloc(len);
    if (!data)
	return PyErr_NoMemory();
    (void) memcpy(data, buf, len);
    snp = data;
    switch (snp->sn_header.sn_type) {
    case SCTP_ASSOC_CHANGE:
	ret = parse_assoc_change(data);
	break;
    case SCTP_PEER_ADDR_CHANGE:
	ret = parse_peer_addr_change(data);
	break;
    case SCTP_SENDER_DRY_EVENT:
	ret = parse_sender_dry_event(data);
	break;
    case SCTP_REMOTE_ERROR:
	ret = parse_remote_error(data);
	break;
    case SCTP_SHUTDOWN_EVENT:
	ret = parse_shutdown_event(data);
	break;
    case SCTP_ADAPTATION_INDICATION:
	ret = parse_adaptation_event(data);
	break;
    case SCTP_PARTIAL_DELIVERY_EVENT:
	ret = parse_pdapi_event(data);
	break;
    case SCTP_AUTHENTICATION_EVENT:
	ret = parse_authkey_event(data);
	break;
#ifdef HAVE_FREEBSD	
    case SCTP_NOTIFICATIONS_STOPPED_EVENT:
	ret = parse_notifs_stop_event(data);
	break;
#endif /* HAVE_FREEBSD */
    case SCTP_SEND_FAILED_EVENT:
	ret = parse_send_failed_event(data);
	break;
    default:
	PyMem_Free(data);
	PyErr_SetString(PyExc_OSError, "unexpected or unknown event type");
	ret = NULL;
    }
    if (!ret) {
	__SCTPErr(self, __FUNC__);
	return NULL;
    }
    return ret;
}

static PyMethodDef SCTPEventMethods[] = {
    {"parse_notification", (PyCFunction) SCTPEvent_parse_notification,
     METH_VARARGS, SCTPEvent_parse_notificationDoc},
    {NULL, NULL, 0, NULL}
};

/*****************************************************************************
 * MODULE INITIALIZATION
 *****************************************************************************/

PyDoc_STRVAR(
    SCTPEventDoc, "Extension for SCTP sockets - C module `" MODS_DIR "."
    "sctp_event'"
    );

static PyModuleDef SCTPEventModule = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = MODS_DIR "." "sctp_event",
    .m_doc = SCTPEventDoc,
    .m_size = -1,
    .m_methods = SCTPEventMethods
};

PyMODINIT_FUNC
PyInit_sctp_event(void)
{
    PyObject* m;

    m = PyModule_Create(&SCTPEventModule);
    if (!m)
        return NULL;
    if (SCTPEventModule_add_constants(m) < 0) {
	Py_DECREF(m);
	return NULL;
    }
    return m;
}

/*****************************************************************************
 * LOCAL FUNCTION DEFINITIONS
 *****************************************************************************/

static int
SCTPEventModule_add_constants(PyObject *m)
{
    if (PyModule_AddIntConstant(m, "MSG_NOTIFICATION", MSG_NOTIFICATION) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_EVENT", SCTP_EVENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_ASSOC_CHANGE", SCTP_ASSOC_CHANGE) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_COMM_UP", SCTP_COMM_UP) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_COMM_LOST", SCTP_COMM_LOST) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_RESTART", SCTP_RESTART) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SHUTDOWN_COMP", SCTP_SHUTDOWN_COMP) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_CANT_STR_ASSOC", SCTP_CANT_STR_ASSOC) < 0)
	return -1;
#ifdef HAVE_FREEBSD
    if (PyModule_AddIntConstant(
	    m, "SCTP_ASSOC_SUPPORTS_PR", SCTP_ASSOC_SUPPORTS_PR) < 0)
	return -1; /* (constant defined in RFC-6458, but not in Linux) */
    if (PyModule_AddIntConstant(
	    m, "SCTP_ASSOC_SUPPORTS_AUTH", SCTP_ASSOC_SUPPORTS_AUTH) < 0)
	return -1; /* (constant defined in RFC-6458, but not in Linux) */
    if (PyModule_AddIntConstant(
	    m, "SCTP_ASSOC_SUPPORTS_ASCONF", SCTP_ASSOC_SUPPORTS_ASCONF) < 0)
	return -1; /* (constant defined in RFC-6458, but not in Linux) */
    if (PyModule_AddIntConstant(
	    m, "SCTP_ASSOC_SUPPORTS_MULTIBUF",
	    SCTP_ASSOC_SUPPORTS_MULTIBUF) < 0)
	return -1; /* (constant defined in RFC-6458, but not in Linux) */
#endif /* HAVE_FREEBSD */    
    if (PyModule_AddIntConstant(
	    m, "SCTP_PEER_ADDR_CHANGE", SCTP_PEER_ADDR_CHANGE) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_ADDR_AVAILABLE", SCTP_ADDR_AVAILABLE) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_ADDR_UNREACHABLE", SCTP_ADDR_UNREACHABLE) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_ADDR_REMOVED", SCTP_ADDR_REMOVED) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_ADDR_ADDED", SCTP_ADDR_ADDED) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_ADDR_MADE_PRIM", SCTP_ADDR_MADE_PRIM) < 0)
	return -1;
    if (PyModule_AddIntConstant(m, "SCTP_REMOTE_ERROR", SCTP_REMOTE_ERROR) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SHUTDOWN_EVENT", SCTP_SHUTDOWN_EVENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_ADAPTATION_INDICATION", SCTP_ADAPTATION_INDICATION) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_PARTIAL_DELIVERY_EVENT", SCTP_PARTIAL_DELIVERY_EVENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_PARTIAL_DELIVERY_ABORTED",
	    SCTP_PARTIAL_DELIVERY_ABORTED) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTHENTICATION_EVENT", SCTP_AUTHENTICATION_EVENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_NEW_KEY", SCTP_AUTH_NEW_KEY) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_NO_AUTH", SCTP_AUTH_NO_AUTH) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_AUTH_FREE_KEY", SCTP_AUTH_FREE_KEY) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_SENDER_DRY_EVENT", SCTP_SENDER_DRY_EVENT) < 0)
	return -1;
#ifdef HAVE_FREEBSD
    if (PyModule_AddIntConstant(
	    m, "SCTP_NOTIFICATIONS_STOPPED_EVENT",
	    SCTP_NOTIFICATIONS_STOPPED_EVENT) < 0)
	return -1; /* (constant defined in RFC-6458, but not in Linux) */
#endif /* HAVE_FREEBSD */
    if (PyModule_AddIntConstant(
	    m, "SCTP_SEND_FAILED_EVENT", SCTP_SEND_FAILED_EVENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_DATA_UNSENT", SCTP_DATA_UNSENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_DATA_SENT", SCTP_DATA_SENT) < 0)
	return -1;
    if (PyModule_AddIntConstant(
	    m, "SCTP_EVENT_CSIZE", sizeof(struct sctp_event)) < 0)
	return -1;
    return 0;
}

static PyObject *
parse_assoc_change(void *data)
{
    Py_ssize_t length;
    field_t fields[] = {
	{.name = "sn_type"},
	{.name = "sac_flags"},
	{.name = "sac_state"},
	{.name = "sac_error"},
	{.name = "sac_outbound_streams"},
	{.name = "sac_inbound_streams"},
	{.name = "sac_assoc_id"},
	{.name = "sac_info"},
	{.name = NULL}
    };
    struct sctp_assoc_change *event = data;

    switch (event->sac_state) {
    case SCTP_COMM_UP:
    case SCTP_COMM_LOST:
    case SCTP_RESTART:
    case SCTP_SHUTDOWN_COMP:
    case SCTP_CANT_STR_ASSOC:
	break;
    default:
	PyErr_SetString(
	    PyExc_OSError, "SCTP_ASSOC_CHANGE: unexpected or unknown state"
	    );
	PyMem_Free(data);
	return NULL;
    }
    fields[0].value = Py_BuildValue("H", event->sac_type);
    fields[1].value = Py_BuildValue("H", event->sac_flags);
    fields[2].value = Py_BuildValue("H", event->sac_state);
    fields[3].value = Py_BuildValue("H", event->sac_error);
    fields[4].value = Py_BuildValue("H", event->sac_outbound_streams);
    fields[5].value = Py_BuildValue("H", event->sac_inbound_streams);
    fields[6].value = Py_BuildValue("i", event->sac_assoc_id);
    length = event->sac_length - sizeof(*event);
    if (length > 0) {
	if (event->sac_state == SCTP_COMM_UP ||
	    event->sac_state == SCTP_RESTART) {
	    uint8_t *ptr = event->sac_info;
	    PyObject *value = PyTuple_New(length);

	    if (!value)
		return NULL;
	    for (Py_ssize_t pos = 0; pos < length; pos++, ptr++)
		PyTuple_SET_ITEM(value, pos, Py_BuildValue("B", *ptr));
	    fields[7].value = value;
	}
	else
	    fields[7].value = PyBytes_FromStringAndSize(
		(char *) event->sac_info, length);
    }
    PyMem_Free(data);
    return event_to_dict(fields);
}

static PyObject *
parse_peer_addr_change(void *data)
{
    field_t fields[] = {
	{.name = "sn_type"},
	{.name = "spc_flags"},
	{.name = "spc_aaddr"},
	{.name = "spc_state"},
	{.name = "spc_error"},
	{.name = "spc_assoc_id"},
	{.name = NULL}
    };
    struct sctp_paddr_change *event = data;

    switch (event->spc_state) {
    case SCTP_ADDR_AVAILABLE:
    case SCTP_ADDR_UNREACHABLE:
    case SCTP_ADDR_REMOVED:
    case SCTP_ADDR_ADDED:
    case SCTP_ADDR_MADE_PRIM:
	break;
    default:
	PyErr_SetString(
	    PyExc_OSError, "SCTP_PEER_ADDR_CHANGE: unexpected or unknown state"
	    );
	PyMem_Free(data);
	return NULL;
    }
    fields[0].value = Py_BuildValue("H", event->spc_type);
    fields[1].value = Py_BuildValue("H", event->spc_flags);
    fields[2].value = sockaddr_to_ip(event->spc_aaddr);
    fields[3].value = Py_BuildValue("I", event->spc_state);
    fields[4].value = Py_BuildValue("I", event->spc_error);
    fields[5].value = Py_BuildValue("i", event->spc_assoc_id);
    PyMem_Free(data);
    return event_to_dict(fields);
}

static PyObject *
parse_remote_error(void *data)
{
    Py_ssize_t length;
    field_t fields[] = {
	{.name = "sn_type"},
	{.name = "sre_flags"},
	{.name = "sre_error"},
	{.name = "sre_assoc_id"},
	{.name = "sre_data"},
	{.name = NULL}
    };
    struct sctp_remote_error *event = data;

    fields[0].value = Py_BuildValue("H", event->sre_type);
    fields[1].value = Py_BuildValue("H", event->sre_flags);
    fields[2].value = Py_BuildValue("H", ntohs(event->sre_error));
    fields[3].value = Py_BuildValue("i", event->sre_assoc_id);
    length = event->sre_length - sizeof(*event);
    if (length > 0)
	fields[4].value = PyBytes_FromStringAndSize(
		(char *) event->sre_data, length);
    PyMem_Free(data);
    return event_to_dict(fields);
}

static PyObject *
parse_shutdown_event(void *data)
{
    field_t fields[] = {
	{.name = "sn_type"},
	{.name = "sse_flags"},
	{.name = "sse_assoc_id"},
	{.name = NULL}
    };
    struct sctp_shutdown_event *event = data;

    fields[0].value = Py_BuildValue("H", event->sse_type);
    fields[1].value = Py_BuildValue("H", event->sse_flags);
    fields[2].value = Py_BuildValue("i", event->sse_assoc_id);
    PyMem_Free(data);
    return event_to_dict(fields);
}

static PyObject *
parse_adaptation_event(void *data)
{
    field_t fields[] = {
	{.name = "sn_type"},
	{.name = "sai_flags"},
	{.name = "sai_adaptation_ind"},
	{.name = "sai_assoc_id"},
	{.name = NULL}
    };
    struct sctp_adaptation_event *event = data;

    fields[0].value = Py_BuildValue("H", event->sai_type);
    fields[1].value = Py_BuildValue("H", event->sai_flags);
    fields[2].value = Py_BuildValue("I", event->sai_adaptation_ind);
    fields[3].value = Py_BuildValue("i", event->sai_assoc_id);
    PyMem_Free(data);
    return event_to_dict(fields);
}

static PyObject *
parse_pdapi_event(void *data)
{
    field_t fields[] = {
	{.name = "sn_type"},
	{.name = "pdapi_flags"},
	{.name = "pdapi_indication"},
	{.name = "pdapi_stream"},
	{.name = "pdapi_seq"},
	{.name = "pdapi_assoc_id"},
	{.name = NULL}
    };
    struct sctp_pdapi_event *event = data;

    fields[0].value = Py_BuildValue("H", event->pdapi_type);
    fields[1].value = Py_BuildValue("H", event->pdapi_flags);
    fields[2].value = Py_BuildValue("I", event->pdapi_indication);
    fields[3].value = Py_BuildValue("I", event->pdapi_stream);
    fields[4].value = Py_BuildValue("I", event->pdapi_seq);
    fields[5].value = Py_BuildValue("i", event->pdapi_assoc_id);
    PyMem_Free(data);
    return event_to_dict(fields);
}

static PyObject *
parse_authkey_event(void *data)
{
    
    field_t fields[] = {
	{.name = "sn_type"},
	{.name = "auth_flags"},
	{.name = "auth_keynumber"},
	{.name = "auth_indication"},
	{.name = "auth_assoc_id"},
	{.name = NULL}
    };
    struct sctp_authkey_event *event = data;

    fields[0].value = Py_BuildValue("H", event->auth_type);
    fields[1].value = Py_BuildValue("H", event->auth_flags);
    fields[2].value = Py_BuildValue("H", event->auth_keynumber);
    fields[3].value = Py_BuildValue("I", event->auth_indication);
    fields[4].value = Py_BuildValue("i", event->auth_assoc_id);
    PyMem_Free(data);
    return event_to_dict(fields);
}

static PyObject *
parse_sender_dry_event(void *data)
{
    
    field_t fields[] = {
	{.name = "sn_type"},
	{.name = "sender_dry_flags"},
	{.name = "sender_dry_assoc_id"},
	{.name = NULL}
    };
    struct sctp_sender_dry_event *event = data;

    fields[0].value = Py_BuildValue("H", event->sender_dry_type);
    fields[1].value = Py_BuildValue("H", event->sender_dry_flags);
    fields[2].value = Py_BuildValue("i", event->sender_dry_assoc_id);
    PyMem_Free(data);
    return event_to_dict(fields);
}

#ifdef HAVE_FREEBSD
static PyObject *
parse_notifs_stop_event(void *data)
{
    field_t fields[] = {
	{.name = "sn_type"},
	{.name = "sn_flags"},
	{.name = NULL}
    };
    union sctp_notification *event = data;

    fields[0].value = Py_BuildValue("H", event->sn_header.sn_type);
    fields[1].value = Py_BuildValue("H", event->sn_header.sn_flags);
    PyMem_Free(data);
    return event_to_dict(fields);
}
#endif /* HAVE_FREEBSD */

#ifdef HAVE_LINUX
#define ssfe_type ssf_type
#define ssfe_flags ssf_flags
#define ssfe_length ssf_length
#define ssfe_error ssf_error
#define ssfe_assoc_id ssf_assoc_id
#define ssfe_data ssf_data
#endif /* HAVE_LINUX */

static PyObject *
parse_send_failed_event(void *data)
{
    Py_ssize_t length;
    field_t fields[] = {
	{.name = "sn_type"},
	{.name = "ssfe_flags"},
	{.name = "ssfe_error"},
	{.name = "ssfe_info"},
	{.name = "ssfe_assoc_id"},
	{.name = "ssfe_data"},
	{.name = NULL}
    };
    struct sctp_send_failed_event *event = data;

    fields[0].value = Py_BuildValue("H", event->ssfe_type);
    fields[1].value = Py_BuildValue("H", event->ssfe_flags);
    fields[2].value = Py_BuildValue("I", event->ssfe_error);
    fields[3].value = sndinfo_to_dict(event->ssfe_info);
    if (!fields[3].value)
	return NULL;
    fields[4].value = Py_BuildValue("i", event->ssfe_assoc_id);
    length = event->ssfe_length - sizeof(*event);
    if (length > 0)
	fields[5].value = PyBytes_FromStringAndSize(
		(char *) event->ssfe_data, length);
    PyMem_Free(data);
    return event_to_dict(fields);
}

static PyObject *
event_to_dict(field_t *fields)
{
    PyObject *ret;

    ret = PyDict_New();
    if (!ret)
	return NULL;
    for (field_t *ptr = fields; ptr->name; ptr++) {
	if (!ptr->value)
	    continue;
	if (PyDict_SetItemString(ret, ptr->name, ptr->value) < 0) {
	    Py_DECREF(ret);
	    return NULL;
	}
    }
    return ret;
}

static PyObject *
sockaddr_to_ip(struct sockaddr_storage ss)
{
    char host[NI_MAXHOST] = "???", serv[NI_MAXSERV] = "???";
    uint16_t port;
    socklen_t slen = ss.ss_family == AF_INET ? sizeof(struct sockaddr_in) :
	sizeof(struct sockaddr_in6);

    (void) getnameinfo(
	(struct sockaddr *) &ss, slen, host, sizeof(host), serv,
	sizeof(serv), NI_NUMERICHOST | NI_NUMERICSERV
	);
    port = (uint16_t) strtoul(serv, NULL, 10);
    if (ss.ss_family == AF_INET)
	return Py_BuildValue("(sH)", host, port);
    return Py_BuildValue(
	"(sHII)", host, port, ((struct sockaddr_in6 *) &ss)->sin6_flowinfo,
	((struct sockaddr_in6 *) &ss)->sin6_scope_id
	);
}

static PyObject *
sndinfo_to_dict(struct sctp_sndinfo info)
{
    PyObject *ret;

    ret = PyDict_New();
    if (!ret)
	return NULL;
    if (PyDict_SetItemString(
	    ret, "snd_sid", Py_BuildValue("H", info.snd_sid)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    ret, "snd_flags", Py_BuildValue("H", info.snd_flags)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    ret, "snd_ppid", Py_BuildValue("I", info.snd_ppid)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    ret, "snd_context", Py_BuildValue("I", info.snd_context)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    if (PyDict_SetItemString(
	    ret, "snd_assoc_id", Py_BuildValue("i", info.snd_assoc_id)) < 0) {
	Py_DECREF(ret);
	return NULL;
    }
    return ret;
}

/*****************************************************************************
 * EXPORTED FUNCTIONS DEFINITIONS
 *****************************************************************************/
