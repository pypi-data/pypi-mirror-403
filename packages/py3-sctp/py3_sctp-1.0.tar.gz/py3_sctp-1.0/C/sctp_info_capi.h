#ifndef SCTP_INFO_H
#define SCTP_INFO_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyDictObject info;
} SCTPSndInfoObject;
#define SCTPSndInfoObject_Check(o) Py_IS_TYPE(o, &SCTPSndInfoType)

typedef struct {
    PyDictObject info;
} SCTPPrInfoObject;
#define SCTPPrInfoObject_Check(o) Py_IS_TYPE(o, &SCTPPrInfoType)

typedef struct {
    PyDictObject info;
} SCTPAuthInfoObject;
#define SCTPAuthInfoObject_Check(o) Py_IS_TYPE(o, &SCTPAuthInfoType)

typedef struct {
    PyObject_HEAD
    SCTPSndInfoObject *sndinfo;
    SCTPPrInfoObject *prinfo;
    SCTPAuthInfoObject *authinfo;
} SCTPSendvSpaObject;
#define SCTPSendvSpaObject_Check(o) Py_IS_TYPE(o, &SCTPSendvSpaType)

typedef struct {
    PyDictObject info;
} SCTPRcvInfoObject;
#define SCTPRcvInfoObject_Check(o) Py_IS_TYPE(o, &SCTPRcvInfoType)

typedef struct {
    PyDictObject info;
} SCTPNxtInfoObject;
#define SCTPNxtInfoObject_Check(o) Py_IS_TYPE(o, &SCTPNxtInfoType)

typedef struct {
    PyObject_HEAD
    SCTPRcvInfoObject *rcvinfo;
    SCTPNxtInfoObject *nxtinfo;
} SCTPRecvvRnObject;
#define SCTPRecvvRnbject_Check(o) Py_IS_TYPE(o, &SCTPRecvvRnType)

#define SCTP_INFO_CAPI_NAME "sctp_info_capi"
#define SCTP_INFO_CAPSULE_NAME \
    (MODS_DIR "." "sctp_info" "." SCTP_INFO_CAPI_NAME)

#ifndef SCTP_INFO_PYMODULE

static void **sctp_info_capi;

#define SCTPSndInfoType (*(PyTypeObject *) sctp_info_capi[0])
#define SCTPSndInfo2C \
    ((void (*)(SCTPSndInfoObject *, struct sctp_sndinfo *)) sctp_info_capi[1])

#define SCTPPrInfoType (*(PyTypeObject *) sctp_info_capi[2])
#define SCTPPrInfo2C \
    ((void (*)(SCTPPrInfoObject *, struct sctp_prinfo *)) sctp_info_capi[3])

#define SCTPAuthInfoType (*(PyTypeObject *) sctp_info_capi[4])
#define SCTPAuthInfo2C \
    ((void (*)(SCTPAuthInfoObject *, struct sctp_authinfo *)) sctp_info_capi[5])

#define SCTPSendvSpaType (*(PyTypeObject *) sctp_info_capi[6])
#define SCTPSendvSpa2C \
    ((void (*)(SCTPSendvSpaObject *, struct sctp_sendv_spa *)) \
     sctp_info_capi[7])

#define SCTPRcvInfoType (*(PyTypeObject *) sctp_info_capi[8])
#define SCTPC2RcvInfo \
    ((SCTPRcvInfoObject *(*)(struct sctp_rcvinfo *)) sctp_info_capi[9])

#define SCTPNxtInfoType (*(PyTypeObject *) sctp_info_capi[10])
#define SCTPC2NxtInfo \
    ((SCTPNxtInfoObject *(*)(struct sctp_nxtinfo *)) sctp_info_capi[11])

#define SCTPRecvvType (*(PyTypeObject *) sctp_info_capi[12])
#define SCTPC2RecvvRn \
    ((SCTPRecvvRnObject *(*)(struct sctp_recvv_rn *)) sctp_info_capi[13])

static int
sctp_info_import_capi(void)
{
    sctp_info_capi = (void **) PyCapsule_Import(SCTP_INFO_CAPSULE_NAME, 0);
    return sctp_info_capi ? 0 : -1;
}

#endif /* SCTP_INFO_PYMODULE */

#ifdef __cplusplus
}
#endif

#endif /* SCTP_INFO_H*/
