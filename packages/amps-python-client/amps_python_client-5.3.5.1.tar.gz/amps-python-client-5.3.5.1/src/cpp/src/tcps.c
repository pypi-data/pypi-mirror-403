/*//////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2010-2025 60East Technologies Inc., All Rights Reserved.
//
// This computer software is owned by 60East Technologies Inc. and is
// protected by U.S. copyright laws and other laws and by international
// treaties.  This computer software is furnished by 60East Technologies
// Inc. pursuant to a written license agreement and may be used, copied,
// transmitted, and stored only in accordance with the terms of such
// license agreement and with the inclusion of the above copyright notice.
// This computer software or any other copies thereof may not be provided
// or otherwise made available to any other person.
//
// U.S. Government Restricted Rights.  This computer software: (a) was
// developed at private expense and is in all respects the proprietary
// information of 60East Technologies Inc.; (b) was not developed with
// government funds; (c) is a trade secret of 60East Technologies Inc.
// for all purposes of the Freedom of Information Act; and (d) is a
// commercial item and thus, pursuant to Section 12.212 of the Federal
// Acquisition Regulations (FAR) and DFAR Supplement Section 227.7202,
// Government's use, duplication or disclosure of the computer software
// is subject to the restrictions set forth by 60East Technologies Inc..
//
///////////////////////////////////////////////////////////////////////// */
#if _MSC_VER < 1400
  /*support for visual c++ 2003 */
  #define _WIN32_WINNT 0x0400
#endif
#include <amps/amps_impl.h>
#include <amps/amps_ssl.h>
#include <amps/ampsuri.h>
#include <amps/amps_zlib.h>
#if __STDC_VERSION__ >= 201100
  #include <stdatomic.h>
  #include <stdbool.h>
  #define AMPS_IEX(ptr, value) atomic_exchange_explicit((ptr), (value), memory_order_acq_rel)
  #define AMPS_IEX_GET(ptr, value) atomic_exchange_explicit((ptr), (value), memory_order_acq_rel)
  #define AMPS_IEX_LONG(ptr, value) atomic_exchange_explicit((ptr), (value), memory_order_acq_rel)
  #define AMPS_FETCH_ADD(ptr, value) atomic_fetch_add_explicit((ptr), (value), memory_order_acq_rel)
  #define AMPS_FETCH_SUB(ptr, value) atomic_fetch_sub_explicit((ptr), (value), memory_order_acq_rel)
#elif defined(_WIN32)
  #ifdef _WIN64
    #define AMPS_IEX(ptr,value) _InterlockedExchange64((LONG64*)(ptr), (LONG64)(value))
    #define AMPS_IEX_GET(ptr,value) _InterlockedExchange64((LONG64*)(ptr), (LONG64)(value))
    #define AMPS_IEX_LONG(ptr,value) _InterlockedExchange((ptr), (value))
    #define AMPS_FETCH_ADD(ptr, value) InterlockedExchangeAdd64((LONGLONG volatile*)(ptr), (LONGLONG)(value))
    #define AMPS_FETCH_SUB(ptr, value) InterlockedExchangeAdd64((LONGLONG volatile*)(ptr), (LONGLONG)(-1 * (value)))
  #else
    #define AMPS_IEX(ptr,value) _InterlockedExchange((long*)(ptr), (LONG)(value))
    #define AMPS_IEX_GET(ptr,value) _InterlockedExchange((long*)(ptr), (LONG)(value))
    #define AMPS_IEX_LONG(ptr,value) _InterlockedExchange((ptr), (LONG)(value))
    #define AMPS_FETCH_ADD(ptr, value) InterlockedExchangeAdd((LONG volatile*)(ptr), (LONG)(value))
    #define AMPS_FETCH_SUB(ptr, value) InterlockedExchangeAdd((LONG volatile*)(ptr), (LONG)(-1 * (value)))
  #endif
#else
  #define AMPS_IEX(ptr, value) (void)__sync_lock_test_and_set((ptr), (value))
  #define AMPS_IEX_GET(ptr, value) __sync_lock_test_and_set((ptr), (value))
  #define AMPS_IEX_LONG(ptr, value) (void)__sync_lock_test_and_set((ptr), (value))
  #define AMPS_FETCH_ADD(ptr, value) __sync_fetch_and_add((ptr), (value))
  #define AMPS_FETCH_SUB(ptr, value) __sync_fetch_and_sub((ptr), (value))
#endif

#ifdef _WIN32

/* Causes linked programs to add ws2_32.lib which is required by
 * this module. If you'd like to turn this off, define the macro
 * AMPS_WINDOWS_NO_DEFAULT_LIBS.
 */
#ifndef AMPS_WINDOWS_NO_DEFAULT_LIBS
  #pragma comment(lib,"ws2_32.lib")
#endif

#include <Ws2tcpip.h>
#define GET_ERRNO (WSAGetLastError())
#define SOCK_ERRORCODE(x) WSA##x
#define AMPS_INITLOCK(x) InitializeCriticalSection(x)
#define AMPS_LOCK(x) EnterCriticalSection(x)
/* defined in tcp.c */
int amps_win_spin_lock(LPCRITICAL_SECTION x);
#define AMPS_SPIN_LOCK(x) amps_win_spin_lock(x)
#define AMPS_SPIN_LOCK_UNLIMITED(x) EnterCriticalSection(x)
#define AMPS_UNLOCK(x) LeaveCriticalSection(x)
#define AMPS_KILLLOCK(x) DeleteCriticalSection(x)
#else
#define GET_ERRNO (errno)
#define SOCK_ERRORCODE(x) x
#include <poll.h>
#include <pthread.h>

static pthread_mutexattr_t _mutexattr_recursive;
#define AMPS_INITLOCK(x) { \
    pthread_mutexattr_init(&_mutexattr_recursive); \
    pthread_mutexattr_settype(&_mutexattr_recursive, PTHREAD_MUTEX_RECURSIVE);\
    pthread_mutex_init(x, &_mutexattr_recursive); }
#define AMPS_LOCK(x) pthread_mutex_lock(x)
#define AMPS_SPIN_LOCK(x) amps_spin_lock_counted(x)
#define AMPS_SPIN_LOCK_UNLIMITED(x) amps_spin_lock_unlimited(x)
#define AMPS_UNLOCK(x) pthread_mutex_unlock(x)
#define AMPS_KILLLOCK(x) pthread_mutex_destroy(x)
#endif

#ifdef AMPS_CPP_COUNT_THREADS
#define AMPS_INC_THREAD_COUNT(x) AMPS_FETCH_ADD(x, 1)
#else
#define AMPS_INC_THREAD_COUNT(x)
#endif

#ifdef _WIN32
INIT_ONCE ampsTcpsThreadKeyOnce = INIT_ONCE_STATIC_INIT;
DWORD ampsTcpsThreadKey = TLS_OUT_OF_INDEXES;

void amps_tcps_delete_key(void)
{
  TlsFree(ampsTcpsThreadKey);
}

BOOL CALLBACK amps_tcps_init_key(PINIT_ONCE pKeyOnce, PVOID unused, PVOID* unused2)
{
  if ((ampsTcpsThreadKey = TlsAlloc()) == TLS_OUT_OF_INDEXES)
  {
    return FALSE;
  }
  atexit(amps_tcps_delete_key);
  return TRUE;
}

DWORD amps_tcps_get_thread_key(void)
{
  InitOnceExecuteOnce(&ampsTcpsThreadKeyOnce, amps_tcps_init_key, NULL, NULL);
  return ampsTcpsThreadKey;
}

void amps_tcps_set_thread_key(void* pVal)
{
  InitOnceExecuteOnce(&ampsTcpsThreadKeyOnce, amps_tcps_init_key, NULL, NULL);
  TlsSetValue(ampsTcpsThreadKey, pVal);
}

int tcpsThreadTimeoutMillis = 10000;

#define AMPS_JOIN_DECLARE() \
  DWORD tid = (DWORD)0; \
  HANDLE tidH = (HANDLE)0

#define AMPS_JOIN(x) \
  tid = (DWORD)AMPS_IEX(&x, 0); \
  tidH = (HANDLE)AMPS_IEX(&x##H, 0); \
  if (tid != 0) \
  { \
    if (tid != GetCurrentThreadId()) \
    { \
      AMPS_INC_THREAD_COUNT(&amps_thread_join_count); \
      WaitForSingleObject(tidH, tcpsThreadTimeoutMillis); \
      CloseHandle(tidH); \
    } \
    else \
    { \
      amps_tcps_set_thread_key((void*)tidH); \
    } \
  }
#define AMPS_SLEEP(x) \
  Sleep(x)
#define SHUT_RDWR SD_BOTH
#else
pthread_once_t ampsTcpsThreadKeyOnce = PTHREAD_ONCE_INIT;
pthread_key_t ampsTcpsThreadKey;

void amps_tcps_detach_thread(void* vpSelf)
{
  pthread_detach((pthread_t)vpSelf);
  AMPS_INC_THREAD_COUNT(&amps_thread_detach_count);
}

void amps_tcps_delete_thread_key(void)
{
  pthread_key_delete(ampsTcpsThreadKey);
}

void amps_tcps_init_thread_key()
{
  pthread_key_create(&ampsTcpsThreadKey, amps_tcps_detach_thread);
  atexit(amps_tcps_delete_thread_key);
}

void amps_tcps_set_thread_key(void* pVal)
{
  (void) pthread_once(&ampsTcpsThreadKeyOnce, amps_tcps_init_thread_key);
  pthread_setspecific(ampsTcpsThreadKey, pVal);
}

#define AMPS_JOIN_DECLARE() \
  pthread_t tid = (pthread_t)0;

#if __STDC_VERSION__ >= 201100
#define AMPS_JOIN(x) \
  tid = atomic_exchange((&x), (pthread_t)0); \
  if(tid != (pthread_t)0) \
  { \
    if(tid != pthread_self()) \
    { \
      AMPS_INC_THREAD_COUNT(&amps_thread_join_count); \
      pthread_join(tid, NULL); \
    } \
    else \
    { \
      amps_tcps_set_thread_key((void*)tid); \
    } \
  } \
  else \
  { \
    /* Give recv thread a chance to exit in case it hasn't yet */ \
    usleep(10); \
  }
#else
#define AMPS_JOIN(x) \
  tid = AMPS_FETCH_ADD(&x, (pthread_t)0); \
  if(tid != (pthread_t)0) \
  { \
    if(__sync_bool_compare_and_swap(&x, tid, 0)) \
    { \
      if(tid != pthread_self()) \
      { \
        AMPS_INC_THREAD_COUNT(&amps_thread_join_count); \
        pthread_join(tid, NULL); \
      } \
      else \
      { \
        amps_tcps_set_thread_key((void*)tid); \
      } \
    } \
  } \
  else \
  { \
    /* Give recv thread a chance to exit in case it hasn't yet */ \
    usleep(10); \
  }
#endif

#define AMPS_SLEEP(x) { \
    static struct timespec ts = { x/1000, (x%1000) * 1000000 }; \
    nanosleep(&ts, NULL); }
#endif

// Default start length of socket buffers
#define AMPS_TCPS_DEFAULT_BUF_LEN 16 * 1024

typedef struct
{
  amps_thread_created_callback threadCreatedCallback;
  void* threadCreatedCallbackUserData;
  char* buf;
  amps_int64_t serializer;
  amps_handler messageHandler;
  void* messageHandlerUserData;
  amps_transport_filter_function filterFunction;
  void* filterUserData;

  amps_predisconnect_handler predisconnectHandler;
  void* predisconnectHandlerUserData;
  amps_handler disconnectHandler;
  void* disconnectHandlerUserData;
  amps_uint64_t readTimeoutMillis;
  amps_uint64_t idleTimeMillis;
#if __STDC_VERSION__ >= 201100
  atomic_int_fast64_t threadCreatedCallbackResult;
  _Atomic unsigned connectionVersion;
#else
#if defined(_WIN32) && !defined(_WIN64)
  volatile long threadCreatedCallbackResult;
#else
  volatile amps_int64_t threadCreatedCallbackResult;
#endif
  volatile unsigned connectionVersion;
#endif

  size_t capacity;
#if __STDC_VERSION__ >= 201100
  _Atomic AMPS_SOCKET fd;
  _Atomic(_amps_SSL*)  ssl;
  atomic_bool disconnecting;
  atomic_bool destroying;
#else
  volatile AMPS_SOCKET fd;
  _amps_SSL*  ssl;
  volatile long disconnecting;
  volatile long destroying;
#endif
#ifdef _WIN32
  CRITICAL_SECTION lock;
  CRITICAL_SECTION sendLock;
#if __STDC_VERSION__ >= 201100
  _Atomic DWORD thread;
  _Atomic HANDLE threadH;
#else
  volatile DWORD thread;
  volatile HANDLE threadH;
#endif
#else
  pthread_mutex_t lock;
  pthread_mutex_t sendLock;
#if __STDC_VERSION__ >= 201100
  _Atomic pthread_t thread;
#else
  volatile pthread_t thread;
#endif
#endif

  // Deflation (sending) support;
#if __STDC_VERSION__ >= 201100
  atomic_bool   useZlib;
#else
  volatile long useZlib;
#endif
  amps_zstream* pDeflater;
  char*         pDeflateBuffer;
  size_t        deflateBufferLength;
  amps_zstream* pInflater;
  char*         pInflateBuffer;
  size_t        inflateBufferLength;
  int           inflatePending;

  char lastErrorBuf[1024];
  amps_thread_exit_callback threadExitCallback;
  void* threadExitCallbackUserData;
  amps_http_preflight_callback httpPreflightCallback;
  void* httpPreflightCallbackUserData;
  amps_uint64_t sendBatchSizeBytes;
  amps_uint64_t sendBatchTimeoutMillis;
  char* sendCache;
  size_t sendCacheOffset;
  amps_uint64_t lastSendTime;
}
amps_tcps_t;

void amps_tcps_set_zlib_error(amps_tcps_t* transport, int rc)
{
  _AMPS_SNPRINTF(transport->lastErrorBuf, sizeof(transport->lastErrorBuf),
                 "zlib error code %d: %s", rc, transport->pDeflater->msg);
}

void amps_tcps_set_error(
  amps_tcps_t* transport,
  const amps_char* buffer)
{
  _AMPS_SNPRINTF(transport->lastErrorBuf, sizeof(transport->lastErrorBuf), "%s", buffer);
}

// Allow python client to set transport errors during connect/close
AMPSDLL void amps_tcps_set_external_error(void* transport,
                                          const amps_char* buffer)
{
  amps_tcps_set_error((amps_tcps_t*)transport, buffer);
}

void amps_tcps_set_socket_error(
  amps_tcps_t* transport,
  int errorCode)
{
#ifdef _WIN32
  char localBuf[256];
  FormatMessageA(FORMAT_MESSAGE_FROM_SYSTEM, NULL, errorCode, 0, localBuf, sizeof(localBuf), NULL);
  amps_tcps_set_error(transport, localBuf);
#else
  amps_tcps_set_error(transport, strerror(errorCode));
#endif
}

void amps_tcps_set_hostname_error(
  amps_tcps_t* transport,
  int rc,
  int errorCode)
{
#ifdef _WIN32
  amps_tcps_set_socket_error(transport, errorCode);
#else
  strncpy(transport->lastErrorBuf, gai_strerror(rc), sizeof(transport->lastErrorBuf));
  transport->lastErrorBuf[sizeof(transport->lastErrorBuf) - 1] = '\0';
#endif
}

void amps_tcps_set_error_stack_error(amps_tcps_t* transport)
{
  char buffer[256];
  _amps_ERR_error_string_n(_amps_ERR_get_error(), buffer, 256);
  amps_tcps_set_error(transport, buffer);
}

void amps_tcps_set_ssl_error(amps_tcps_t* transport,
                             int rc,
                             int sysError)
{
  char buffer[256];
  if (!transport->ssl)
  {
    _AMPS_SNPRINTF(buffer, 256, "SSL error, SSL is closing");
    amps_tcps_set_error(transport, buffer);
    return;
  }
  int sslError = _amps_SSL_get_error(transport->ssl, rc);
  unsigned long errorQueue = 0;
  switch (sslError)
  {
  case AMPS_SSL_ERROR_SSL:
    amps_tcps_set_error_stack_error(transport);
    break;
  case AMPS_SSL_ERROR_SYSCALL:
    errorQueue = _amps_ERR_get_error();
    if (errorQueue)
    {
      _amps_ERR_error_string_n(errorQueue, buffer, 256);
      amps_tcps_set_error(transport, buffer);
    }
    else if (rc == 0 || sysError == 0)
    {
      amps_tcps_set_error(transport, "An unexpected disconnect occurred.");
    }
    else
    {
      amps_tcps_set_socket_error(transport, sysError);
    }
    break;
  default:
    _AMPS_SNPRINTF(buffer, 256, "Unexpected SSL error %d", sslError);
    amps_tcps_set_error(transport, buffer);
    return;
  }
}

int amps_tcps_send_compressed(amps_tcps_t* me, amps_char* data, size_t length)
{
  amps_zstream* pDeflater = me->pDeflater;

  pDeflater->next_in = data;
  pDeflater->avail_in = (unsigned int)length;
  pDeflater->avail_out = (unsigned int)me->deflateBufferLength;

  // The ... || !pDeflater->avail_out is so we can send the flushed bytes
  // even if all the input data is consumed, when the output buffer fills up.
  while (pDeflater->avail_in || !pDeflater->avail_out)
  {
    // We send the whole deflate buffer after every deflate().
    pDeflater->avail_out = (unsigned int)me->deflateBufferLength;
    pDeflater->next_out = me->pDeflateBuffer;

    int rc = amps_deflate(pDeflater, 2);
    if (rc != 0)
    {
      amps_tcps_set_zlib_error(me, rc);
      return -1;
    }

    // Send the whole deflate buffer here.
    const char* p = me->pDeflateBuffer, *pe = pDeflater->next_out;
    while (p != pe)
    {
      int sentBytes = _amps_SSL_write(me->ssl, p, (int)(pe - p));
      if (sentBytes <= 0)
      {
        return -1;
      }
      p += sentBytes;
    }
  }
  return (int)length;
}

int amps_tcps_recv_compressed(amps_tcps_t* me, size_t capacity)
{
  amps_zstream* pInflater = me->pInflater;
  int bytes = 0;
  if (!pInflater->avail_in && !me->inflatePending)
  {
    // Retrieve data from the socket only if there's nothing to do.
    errno = 0;
    bytes = _amps_SSL_read(me->ssl, me->pInflateBuffer, (int)me->inflateBufferLength);
    if (bytes <= 0)
    {
      return bytes;
    }
    pInflater->avail_in = (unsigned int)bytes;
    pInflater->next_in = me->pInflateBuffer;
  }
  pInflater->avail_out = (unsigned int)capacity;

  if (pInflater->avail_out)
  {
    me->inflatePending = 0;
    int rc = amps_inflate(pInflater, 2);
    if (rc != 0)
    {
      amps_tcps_set_zlib_error(me, rc);
      if (rc > 0)
      {
        return -1;
      }
      return rc;
    }
    if (pInflater->avail_out == 0)
    {
      // Special case where, even though we consumed the input, we have more output to write next time someone calls here.
      me->inflatePending = 1;
      // Are we out of space to inflate?
      if (pInflater->avail_in
          && pInflater->next_in < (me->pInflateBuffer + bytes))
      {
        return AMPS_ZLIB_NEED_SPACE;
      }
    }
    // If we inflated nothing, read more input
    if (pInflater->avail_out == capacity)
    {
      return AMPS_ZLIB_WANT_READ;
    }
    return (int)(capacity - pInflater->avail_out);
  }

  return 0;
}

amps_result
amps_tcps_init_zlib(amps_tcps_t* me)
{
  const int windowBits = -15; /* no headers */
  if (me->pDeflater)
  {
    amps_deflateEnd(me->pDeflater);
    free(me->pDeflater);
    me->pDeflater = 0;

    amps_inflateEnd(me->pInflater);
    free(me->pInflater);
    me->pInflater = 0;
  }
  me->pDeflater = (amps_zstream*)malloc(sizeof(amps_zstream));
  memset(me->pDeflater, 0, sizeof(amps_zstream));
  int rc = amps_deflateInit2(me->pDeflater,
                  6,   /* level */
                  8,   /* Z_DEFLATED */
                  windowBits,
                  8,   /* default memory level */
                  0);  /* default strategy */
  if (rc != 0)
  {
    free(me->pDeflater);
    me->pDeflater = 0;
    amps_tcps_set_error(me, "Unable to initialize zlib.");
    return AMPS_E_URI;
  }
  me->pInflater = (amps_zstream*)malloc(sizeof(amps_zstream));
  memset(me->pInflater, 0, sizeof(amps_zstream));
  rc = amps_inflateInit2(me->pInflater, windowBits)
  if (rc != 0)
  {
    amps_inflateEnd(me->pInflater);
    free(me->pInflater);
    me->pInflater = 0;
    amps_tcps_set_error(me, "Unable to initialize zlib.");
    return AMPS_E_URI;
  }

  //  Initialize the work buffers for inflation and deflation;
  if (!me->pDeflateBuffer)
  {
    me->pDeflateBuffer = (char*)malloc(16384);
    me->deflateBufferLength = 16384;
  }

  if (!me->pInflateBuffer)
  {
    me->pInflateBuffer = (char*)malloc(16384);
    me->inflateBufferLength = 16384;
  }
  me->inflatePending = 0;
#if __STDC_VERSION__ >= 201100
  me->useZlib = true;
#else
  AMPS_IEX_LONG(&me->useZlib, 1);
#endif
  return AMPS_E_OK;
}

// Function to close SSL* and fd that can be replaced by Python client
int _amps_tcps_close_all(AMPS_SOCKET fd, _amps_SSL* ssl)
{
  int rc = 0;
  if (ssl)
  {
    rc = _amps_SSL_shutdown(ssl);
    if (rc == 0 && fd != AMPS_INVALID_SOCKET)
    {
      // attempt to wait for the server to send back the matching close notify.
#ifdef _WIN32
      struct timeval tv;
      fd_set readfds, exceptfds;
      tv.tv_sec = 0;
      tv.tv_usec = 10000;
      FD_ZERO(&readfds);
      FD_SET(fd, &readfds);
      FD_ZERO(&exceptfds);
      FD_SET(fd, &exceptfds);
      select(1, &readfds, 0, &exceptfds, &tv);
#else
    #ifdef __APPLE__
      struct pollfd pfd = { fd, POLLIN, 0 };
    #else
      struct pollfd pfd = { fd, POLLIN|POLLRDHUP, 0 };
    #endif
      poll(&pfd, 1, 10);
#endif
    }
  }
  if (fd != AMPS_INVALID_SOCKET)
  {
    shutdown(fd, SHUT_RDWR);
    AMPS_CLOSESOCKET(fd);
  }
  if (ssl)
  {
    _amps_SSL_free(ssl);
  }
  return rc;
}

// Pointer to function for closing SSL/fd that Python client redirects
AMPSDLL int (*amps_tcps_close_all)(AMPS_SOCKET, _amps_SSL*) = _amps_tcps_close_all;

const amps_char* amps_tcps_get_last_error(
  amps_handle transport)
{
  return ((amps_tcps_t*)transport)->lastErrorBuf;
}

void amps_tcps_clear_error(
  amps_handle transport)
{
  ((amps_tcps_t*)transport)->lastErrorBuf[0] = '\0';
}

void
amps_tcps_noop_filter_function(const unsigned char* data, size_t length, short direction, void* userdata)
{;}

void amps_tcps_atfork_handler(amps_tcps_t* transport_, int code_)
{
  switch (code_)
  {
  case 0:
    break;
  case 1:
    break;
  case 2:
    /* Reinitialize the transport lock in the forked child */
    AMPS_INITLOCK(&transport_->lock);
    break;
  }
}

amps_handle amps_tcps_create(void)
{
  amps_tcps_t* transport = (amps_tcps_t*)malloc(sizeof(amps_tcps_t));

  if (transport != NULL)
  {
    memset(transport, 0, sizeof(amps_tcps_t));
    transport->fd = AMPS_INVALID_SOCKET;
    transport->ssl = NULL;
    AMPS_INITLOCK(&transport->lock);
    AMPS_INITLOCK(&transport->sendLock);
#if __STDC_VERSION__ >= 201100
    transport->disconnecting = false;
    transport->destroying = false;
#else
    AMPS_IEX_LONG(&transport->disconnecting, 0);
    AMPS_IEX_LONG(&transport->destroying, 0);
#endif
    transport->filterFunction = &amps_tcps_noop_filter_function;
    amps_atfork_add(transport, (_amps_atfork_callback_function)amps_tcps_atfork_handler);
  }

  return transport;
}
#ifdef _WIN32
  DWORD amps_tcps_threaded_reader(void* userData);
#else
  void* amps_tcps_threaded_reader(void* userData);
#endif

int
amps_tcps_opt_parse(const char* val, size_t valLen, int* parsed)
{
  size_t i;
  if (valLen == 4 && memcmp(val, "true", 4) == 0)
  {
    *parsed = 1;
    return 1;
  }
  else if (valLen == 5 && memcmp(val, "false", 5) == 0)
  {
    *parsed = 0;
    return 1;
  }
  else
  {
    *parsed = 0;
    for (i = 0; i < valLen ; i++)
    {
      *parsed *= 10;
      if (val[i] >= '0' && val[i] <= '9')
      {
        *parsed += val[i] - '0';
      }
      else
      {
        return 0;
      }
    }
  }
  return 1;
}

typedef enum
{
  AMPS_PROPERTY_PARSE_ERROR = 0,
  AMPS_PROPERTY_OK = 1,
  AMPS_PROPERTY_PREFLIGHT_TRUE = 2,
  AMPS_PROPERTY_COMPRESSION_ZLIB = 4,
} amps_property_result;

amps_property_result
amps_tcps_apply_socket_property(AMPS_SOCKET fd, const char* key, size_t keyLen, const
                                char* val, size_t valLen)
{
  int value = 0, level = SOL_SOCKET, optname;
  unsigned int optValueSize = sizeof(int);
  char* optValuePtr = (char*)&value;
  struct linger lingerStruct;
  if (keyLen == 4 && memcmp(key, "bind", keyLen) == 0)
  {
    struct addrinfo* pAddrInfo = NULL, addrhints;
    char addr[256] = { 0 };
    char port[256] = { 0 };
    size_t addrLen = valLen, portLen = 0;
    char* portStr = (char*)(memchr((void*)val, ':', valLen));
    char* ipv6Str = (char*)(memchr((void*)val, '[', valLen));

#ifdef _WIN32
    int addrFamily = 0;
    WSAPROTOCOL_INFOW localProto;
    int localProtoLen = sizeof(WSAPROTOCOL_INFO);
    if (getsockopt(fd, SOL_SOCKET, SO_PROTOCOL_INFO, (char*)&localProto, &localProtoLen) == SOCKET_ERROR)
    {
      return AMPS_PROPERTY_PARSE_ERROR;
    }
    addrFamily = localProto.iAddressFamily;
#elif !defined(__APPLE__)
    int addrFamily = 0;
    socklen_t addrFamilyLen = sizeof(addrFamily);
    if (getsockopt(fd, SOL_SOCKET, AMPS_SO_DOMAIN, (void*)&addrFamily, &addrFamilyLen) < 0)
    {
      return AMPS_PROPERTY_PARSE_ERROR;
    }
#endif

    if (ipv6Str)
    {
      ++ipv6Str;
      char* ipv6StrEnd = (char*)(memchr((void*)ipv6Str, ']', (size_t)(val + valLen - ipv6Str)));
      if (!ipv6StrEnd)
      {
        return AMPS_PROPERTY_PARSE_ERROR;
      }
      addrLen = (size_t)(ipv6StrEnd - ipv6Str);
      memcpy(addr, ipv6Str, addrLen);
      addr[addrLen] = '\0';

      if ((size_t)(val + valLen - ++ipv6StrEnd) < valLen && *ipv6StrEnd == ':')
      {
        portLen = (size_t)(val + valLen - ++ipv6StrEnd);
        memcpy(port, ipv6StrEnd, portLen);
        port[portLen] = '\0';
      }
    }
    else if (portStr)
    {
      addrLen = (size_t)(portStr - val);
      portLen = (size_t)(val + valLen - ++portStr);
      memcpy(addr, val, addrLen);
      addr[addrLen] = '\0';
      memcpy(port, portStr, portLen);
      port[portLen] = '\0';
    }
    else
    {
      memcpy(addr, val, addrLen);
      addr[addrLen] = '\0';
    }

    /* use getaddrinfo() to find an appropriate address */
    memset(&addrhints, 0, sizeof(struct addrinfo));
    addrhints.ai_socktype = SOCK_STREAM;
    addrhints.ai_protocol = 0;
#ifndef __APPLE__
    addrhints.ai_family = addrFamily; // match the family of the socket
#else
    if (ipv6Str)
    {
      addrhints.ai_family = AF_INET6;
    }
    else
    {
      addrhints.ai_family = AF_INET;
    }
#endif
    addrhints.ai_flags = (AI_V4MAPPED | AI_ADDRCONFIG | AI_PASSIVE);

    int rc = getaddrinfo(addr, port, &addrhints, &pAddrInfo);
    if (rc != 0 || pAddrInfo == NULL)
    {
      if (pAddrInfo)
      {
        freeaddrinfo(pAddrInfo);
      }
      return AMPS_PROPERTY_PARSE_ERROR;
    }

    if (bind(fd, pAddrInfo->ai_addr, (socklen_t)pAddrInfo->ai_addrlen) != 0)
    {
      freeaddrinfo(pAddrInfo);
      return AMPS_PROPERTY_PARSE_ERROR;
    }
    freeaddrinfo(pAddrInfo);
    return AMPS_PROPERTY_OK;
  }
  else if (keyLen == 18 && memcmp(key, "ip_protocol_prefer", keyLen) == 0)
  {
    // no-op; handled in the connect function
    return AMPS_PROPERTY_OK;
  }
  else if (keyLen == 3 && memcmp(key, "sni", keyLen) == 0)
  {
    // no-op; handled in amps_tcps_apply_ssl_properties
    return AMPS_PROPERTY_OK;
  }
  else if (keyLen == 11 && memcmp(key, "compression", keyLen) == 0)
  {
    return (valLen == 4 && memcmp(val, "zlib", 4) == 0)
            ? AMPS_PROPERTY_COMPRESSION_ZLIB
            : AMPS_PROPERTY_PARSE_ERROR;
  }
  // properties after this point must only be boolean or numeric
  if (!amps_tcps_opt_parse(val, valLen, &value))
  {
    return AMPS_PROPERTY_PARSE_ERROR;
  }
  if (keyLen == 14 && memcmp(key, "http_preflight", keyLen) == 0)
  {
    return value ? AMPS_PROPERTY_PREFLIGHT_TRUE : AMPS_PROPERTY_OK;
  }
  if (keyLen == 10 && memcmp(key, "tcp_rcvbuf", keyLen) == 0)
  {
    optname = SO_RCVBUF;
  }
  else if (keyLen == 13 && memcmp(key, "tcp_keepalive", keyLen) == 0 )
  {
    optname = SO_KEEPALIVE;
  }
  else if (keyLen == 10 && memcmp(key, "tcp_sndbuf", keyLen) == 0)
  {
    optname = SO_SNDBUF;
  }
  else if (keyLen == 11 && memcmp(key, "tcp_nodelay", keyLen) == 0)
  {
    optname = TCP_NODELAY;
    level = IPPROTO_TCP;
  }
  else if (keyLen == 10 && memcmp(key, "tcp_linger", keyLen) == 0)
  {
    optname = SO_LINGER;
    lingerStruct.l_onoff = value != 0;
    lingerStruct.l_linger = (u_short)value;
    optValuePtr = (char*)&lingerStruct;
    optValueSize = sizeof(struct linger);
  }
  else if (keyLen == 6 && memcmp(key, "pretty", keyLen) == 0)
  {
    // no-op; handled in C++ layer
    return AMPS_PROPERTY_OK;
  }
  else
  {
    return AMPS_PROPERTY_PARSE_ERROR;
  }

  /* set it */
  if (setsockopt(fd, level, optname, optValuePtr, optValueSize))
  {
    return AMPS_PROPERTY_PARSE_ERROR;
  }
  return AMPS_PROPERTY_OK;
}

amps_property_result
amps_tcps_apply_socket_properties(AMPS_SOCKET fd, const char* uri,
                                  size_t uriLength, amps_uri_state* uriState)
{
  int retVal = AMPS_PROPERTY_OK;
  amps_property_result optRet = AMPS_PROPERTY_OK;
  const char* key = NULL;
  size_t keyLength = 0;
  /* First, enable tcp_keepalive by default */
  int value = 1;
  unsigned int optValueSize = sizeof(int);
  char* optValuePtr = (char*)&value;
  if (setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, optValuePtr, optValueSize))
  {
    return AMPS_PROPERTY_PARSE_ERROR;
  }
  /* Now, parse the rest of the URI */
  while (uriState->part_id < AMPS_URI_ERROR)
  {
    amps_uri_parse(uri, uriLength, uriState);
    if (uriState->part_id == AMPS_URI_OPTION_KEY)
    {
      key = uriState->part;
      keyLength = uriState->part_length;
    }
    else if (uriState->part_id == AMPS_URI_OPTION_VALUE)
    {
      optRet = amps_tcps_apply_socket_property(fd, key, keyLength,
                                          uriState->part, uriState->part_length);
      if (optRet != AMPS_PROPERTY_OK)
      {
        if (optRet == AMPS_PROPERTY_PARSE_ERROR)
        {
          return optRet;
        }
        retVal |= (int)optRet;
      }
    }
  }
  if (uriState->part_id == AMPS_URI_ERROR)
  {
    return AMPS_PROPERTY_PARSE_ERROR;
  }
  return (amps_property_result)retVal;
}

// Retrieve server name indicator for use by SSL when connecting
char* amps_tcps_get_sni_hostname(const char* uri, size_t uriLength,
                                 amps_uri_state* uriState)
{
  const char* key = NULL;
  size_t keyLength = 0;
  while (uriState->part_id < AMPS_URI_ERROR)
  {
    amps_uri_parse(uri, uriLength, uriState);
    if (uriState->part_id == AMPS_URI_OPTION_KEY)
    {
      key = uriState->part;
      keyLength = uriState->part_length;
    }
    else if (uriState->part_id == AMPS_URI_OPTION_VALUE)
    {
      if (keyLength == 3 && memcmp(key, "sni", keyLength) == 0)
      {
        char* hostname = (char*)malloc(uriState->part_length + 1);
        memcpy(hostname, uriState->part, uriState->part_length);
        hostname[uriState->part_length] = '\0';
        return hostname;
      }
    }
  }
  return NULL;
}

// Normal initialization and connection of SSL around socket
_amps_SSL* _amps_tcps_get_socket_and_ssl(AMPS_SOCKET fd_,
                                         const char* address_, int port_,
                                         struct addrinfo* pAddrInfo_,
                                         char* hostname_, void* me_)
{
  amps_tcps_t* transport = (amps_tcps_t*)me_;
  /* On first use, initialize an SSL context if one hasn't been created. */
  if (!_amps_ssl_ctx)
  {
    if (amps_ssl_init(NULL))
    {
      amps_tcps_set_error(transport, amps_ssl_get_error());
      AMPS_CLOSESOCKET(fd_);
      return NULL;
    }
  }
  // Create SSL wrapper for the socket
  _amps_ERR_clear_error();
  _amps_SSL* ssl = _amps_SSL_new(_amps_ssl_ctx);

  int rc = _amps_SSL_set_fd(ssl, (int)(fd_));
  int sysError = GET_ERRNO;
  if (rc != 1)
  {
    transport->ssl = ssl;
    amps_tcps_set_ssl_error(transport, rc, sysError);
    _amps_SSL_free(ssl);
    ssl = (_amps_SSL*)0;
    transport->ssl = (_amps_SSL*)0;
    AMPS_CLOSESOCKET(fd_);
    return NULL;
  }

  // Connect socket
  rc = connect(fd_, pAddrInfo_->ai_addr,
               (socklen_t)pAddrInfo_->ai_addrlen);
  sysError = GET_ERRNO;
  if (rc == -1)
  {
    amps_tcps_set_socket_error(transport, sysError);
    _amps_SSL_free(ssl);
    AMPS_CLOSESOCKET(fd_);
    return NULL;
  }

  // Set server name indicator if used
  if (hostname_)
  {
    rc = _amps_SSL_ctrl(ssl, AMPS_SSL_CTRL_SET_TLSEXT_HOSTNAME,
                        AMPS_TLSEXT_NAMETYPE_host_name, hostname_);
    sysError = GET_ERRNO;
    if (rc != 1)
    {
      amps_tcps_set_ssl_error(transport, rc, sysError);
      _amps_SSL_free(ssl);
      AMPS_CLOSESOCKET(fd_);
      return NULL;
    }
  }

  _amps_SSL_ctrl(ssl, AMPS_SSL_CTRL_MODE, AMPS_SSL_AUTO_RETRY, NULL);

  // Complete SSL connect/handshake
  rc = _amps_SSL_connect(ssl);
  sysError = GET_ERRNO;
  if (rc != 1)
  {
    amps_tcps_set_ssl_error(transport, rc, sysError);
    _amps_SSL_free(ssl);
    AMPS_CLOSESOCKET(fd_);
    return NULL;
  }
  return ssl;
}

// Pointer to init/connect function for Python client to override
AMPSDLL _amps_SSL* (*amps_tcps_get_socket_and_ssl)(AMPS_SOCKET fd_,
                                                   const char* address_, int port_,
                                                   struct addrinfo* pAddrInfo_,
                                                   char* hostname_, void* me_) =
                                                   _amps_tcps_get_socket_and_ssl;

amps_result amps_tcps_set_idle_time(amps_handle, int);
int amps_tcps_locked_read(amps_tcps_t*, char*, int, int*);

amps_result
amps_tcps_update_read_timeout(amps_tcps_t* me)
{
  amps_uint64_t timeout = (me->readTimeoutMillis && me->idleTimeMillis)
                          ? AMPS_MIN(me->readTimeoutMillis, me->idleTimeMillis)
                          : AMPS_MAX(me->readTimeoutMillis, me->idleTimeMillis);
  timeout = (timeout && me->sendBatchTimeoutMillis)
            ? AMPS_MIN(timeout, me->sendBatchTimeoutMillis)
            : AMPS_MAX(timeout, me->sendBatchTimeoutMillis);
  int rc = 0;
#ifdef _WIN32
  DWORD timeoutMillis = (DWORD)timeout;
  rc = setsockopt(me->fd, SOL_SOCKET, SO_RCVTIMEO,
                  (const char*)&timeoutMillis, sizeof(DWORD));
#else
  struct timeval tv;
  tv.tv_sec = (int)timeout / 1000;
  tv.tv_usec = ((int)timeout % 1000) * 1000;
  rc = setsockopt(me->fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(struct timeval));
#endif
  int sysError = GET_ERRNO;
  if (rc == -1)
  {
    amps_tcps_set_socket_error(me, sysError);
    return AMPS_E_USAGE;
  }
  return AMPS_E_OK;
}

amps_result _amps_tcps_handle_http_preflight(amps_tcps_t* me)
{
  const char* httpPreflight = NULL;
  int socketBytes = 0;
  int bytesWritten = 0;
  char* readPoint;
  char* end;
  int errorcode = 0;
  amps_uint64_t lastReadTime = 0;

  /* Get the message and size */
  httpPreflight = me->httpPreflightCallback(me->httpPreflightCallbackUserData);
  if (!httpPreflight)
  {
    return AMPS_E_OK;
  }
  bytesWritten = (int)(strlen(httpPreflight));
  /*now, send */
  while (socketBytes < bytesWritten)
  {
    errno = 0;
    int bytesWrittenThisTime;
    bytesWrittenThisTime = _amps_SSL_write(me->ssl, httpPreflight + socketBytes, bytesWritten - socketBytes);
    if (bytesWrittenThisTime <= 0)
    {
      /* record the error */
      amps_tcps_set_error(me, "The http connection failed.");
      return AMPS_E_CONNECTION_REFUSED;
    }
    socketBytes += bytesWrittenThisTime;
  }
  me->filterFunction((const unsigned char*)httpPreflight, (size_t)bytesWritten, 0, me->filterUserData);
  // Set up a buffer and get response
  free(me->buf);
  me->buf = (char*)malloc(sizeof(char) * AMPS_TCPS_DEFAULT_BUF_LEN);
  readPoint = me->buf;
  end = me->buf + AMPS_TCPS_DEFAULT_BUF_LEN;
  socketBytes = 0;
  lastReadTime = amps_now();
  while ((readPoint - me->buf) < 15)
  {
    // Use select to wait for data if none already exists on the ssl.
    if (!_amps_SSL_pending(me->ssl))
    {
      errno = 0;
  #ifdef _WIN32
      struct timeval tv;
      fd_set readfds, exceptfds;
      tv.tv_sec = 0;
      tv.tv_usec = 1000;
      FD_ZERO(&readfds);
      FD_SET(me->fd, &readfds);
      FD_ZERO(&exceptfds);
      FD_SET(me->fd, &exceptfds);
      socketBytes  = select(1, &readfds, 0, &exceptfds, &tv);
  #else
    #ifdef __APPLE__
      struct pollfd pfd = { me->fd, POLLIN, 0 };
    #else
      struct pollfd pfd = { me->fd, POLLIN|POLLRDHUP, 0 };
    #endif
      socketBytes = poll(&pfd, 1, 100);
      if (socketBytes > 0)
      {
        // If there are no bytes ready to read, we lost connection
        if ((pfd.revents & POLLIN) == 0)
        {
          // We don't want errorcode modified below
          socketBytes = 0;
          // Not important what we pick here, just not timeout/interrupt
          errorcode = EBADF;
        }
      }
      else if (socketBytes == 0)
      {
        errorcode = ETIMEDOUT;
      }
  #endif
      if (socketBytes > 0)
      {
          errno = 0;
          socketBytes = _amps_SSL_read(me->ssl, readPoint, (int)(end - readPoint));
          errorcode = socketBytes <= 0 ? _amps_SSL_get_error(me->ssl, socketBytes) : 0;
      }
    }
    if (socketBytes > 0)
    {
      readPoint += socketBytes;
    }
    else
    {
      if (errorcode == AMPS_SSL_ERROR_WANT_READ)
      {
        errorcode = 0;
      }
      // errorcode could be an ssl error code, so check for errno
      int sysError = socketBytes ? GET_ERRNO : 0;
      if (sysError)
      {
        errorcode = sysError;
      }
      if (errorcode == SOCK_ERRORCODE(EINTR))
      {
        continue;
      }
      /* disconnect if not a timeout error, or the user only set a read timeout, or the
       * read timeout has been exceeded. */
      if ((errorcode != 0
           && (errorcode != SOCK_ERRORCODE(ETIMEDOUT)
               && errorcode != SOCK_ERRORCODE(EWOULDBLOCK)))
          || (amps_now() - lastReadTime > 2000))
      {
        /* record the error */
        amps_tcps_set_error(me, "The http connection failed.");
        return AMPS_E_CONNECTION_REFUSED;
      }
      continue;
    }
  }
  me->filterFunction((const unsigned char*)me->buf, (size_t)(readPoint - me->buf), 1, me->filterUserData);
  if (memcmp(me->buf + 9, (void*)"101", 3) != 0)
  {
    amps_tcps_set_error(me, "Failed to upgrade connection");
    return AMPS_E_CONNECTION_REFUSED;
  }
  readPoint = me->buf;
  while (socketBytes > 0)
  {
    // Use select to wait for data if none already exists on the ssl.
    if (!_amps_SSL_pending(me->ssl))
    {
      errno = 0;
  #ifdef _WIN32
      struct timeval tv;
      fd_set readfds, exceptfds;
      tv.tv_sec = 0;
      tv.tv_usec = 1000;
      FD_ZERO(&readfds);
      FD_SET(me->fd, &readfds);
      FD_ZERO(&exceptfds);
      FD_SET(me->fd, &exceptfds);
      socketBytes  = select(1, &readfds, 0, &exceptfds, &tv);
  #else
    #ifdef __APPLE__
      struct pollfd pfd = { me->fd, POLLIN, 0 };
    #else
      struct pollfd pfd = { me->fd, POLLIN|POLLRDHUP, 0 };
    #endif
      socketBytes = poll(&pfd, 1, 100);
      if (socketBytes > 0)
      {
        // If there are no bytes ready to read, we lost connection
        if ((pfd.revents & POLLIN) == 0)
        {
          // We don't want errorcode modified below
          socketBytes = 0;
          // Not important what we pick here, just not timeout/interrupt
          errorcode = EBADF;
        }
      }
      else if (socketBytes == 0)
      {
        errorcode = ETIMEDOUT;
      }
  #endif
      if (socketBytes > 0)
      {
          errno = 0;
          socketBytes = _amps_SSL_read(me->ssl, readPoint, (int)(end - readPoint));
          errorcode = socketBytes <= 0 ? _amps_SSL_get_error(me->ssl, socketBytes) : 0;
      }
    }
    if (socketBytes > 0)
    {
      readPoint += socketBytes;
    }
    else
    {
      // errorcode could be an ssl error code, so check for errno
      int sysError = socketBytes ? GET_ERRNO : 0;
      if (sysError)
      {
        errorcode = sysError;
      }
      if (errorcode == SOCK_ERRORCODE(EINTR))
      {
        continue;
      }
      /* disconnect if not a timeout error, or the user only set a read timeout, or the
       * read timeout has been exceeded. */
      if (errorcode != 0
          && (errorcode != SOCK_ERRORCODE(ETIMEDOUT)
              && errorcode != SOCK_ERRORCODE(EWOULDBLOCK)))
      {
        /* record the error */
        amps_tcps_set_error(me, "The http connection failed.");
        return AMPS_E_CONNECTION_REFUSED;
      }
      break;
    }
  }
  me->filterFunction((const unsigned char*)me->buf, (size_t)(readPoint - me->buf), 1, me->filterUserData);
  return AMPS_E_OK;
}

amps_result amps_tcps_handle_disconnect(
  amps_tcps_t* me, unsigned failedConnectionVersion);

amps_result amps_tcps_connect(amps_handle transport, const amps_char* address)
{
  AMPS_JOIN_DECLARE();
  amps_property_result propResult = AMPS_PROPERTY_OK;
  amps_tcps_t* me = (amps_tcps_t*)transport;
  char* host = NULL, *port = NULL, *protocol = NULL;
  amps_uri_state uri_state_socket_props, uri_state_addr_props, uri_state_ssl_props;
  amps_ip_protocol_preference ip_proto_prefer = AMPS_DEFAULT_IP_PROTOCOL_PREFERENCE;
  int ip_proto_pref_override = 0;
  int rc, sysError, i;
  amps_result result = AMPS_E_OK;
  struct addrinfo* pAddrInfo = NULL, addrhints;
  size_t address_length = 0;
  AMPS_SOCKET fd = AMPS_INVALID_SOCKET;
  _amps_SSL* ssl = 0;

#ifdef _WIN32
  WSADATA wsaData;
  rc = WSAStartup(MAKEWORD(2, 2), &wsaData);
  if (rc != 0)
  {
    amps_tcps_set_error(me, "Windows Sockets could not be started.");
    return AMPS_E_MEMORY;
  }
#endif

  AMPS_LOCK(&me->lock);
#ifndef _WIN32
  pthread_cleanup_push(amps_cleanup_unlock_mutex, (void*)&me->lock);
#endif
  me->lastErrorBuf[0] = '\0';
  /* if we were previously marked as disconnecting, forget that. */
#if __STDC_VERSION__ >= 201100
    me->disconnecting = false;
#else
  AMPS_IEX_LONG(&me->disconnecting, 0);
#endif
  AMPS_LOCK(&me->sendLock);
#ifndef _WIN32
  pthread_cleanup_push(amps_cleanup_unlock_mutex, (void*)&me->sendLock);
#endif
  fd = AMPS_IEX_GET(&me->fd, AMPS_INVALID_SOCKET);
  ssl = (_amps_SSL*)AMPS_IEX_GET(&me->ssl, 0);

  /* were we previously connected?  go ahead and close that. */
  // Use our close function to shutdown socket and SSL
  rc = amps_tcps_close_all(fd, ssl);
  sysError = GET_ERRNO;
  AMPS_JOIN(me->thread);
  fd = AMPS_INVALID_SOCKET;
  ssl = NULL;
  if (rc < 0)
  {
    amps_tcps_set_ssl_error(me, rc, sysError);
  }

  /* parse out the address */
  memset(&uri_state_socket_props, 0, sizeof(amps_uri_state));
  memset(&uri_state_addr_props, 0, sizeof(amps_uri_state));
  memset(&uri_state_ssl_props, 0, sizeof(amps_uri_state));
  address_length = strlen(address);
  while (uri_state_addr_props.part_id < AMPS_URI_ERROR)
  {
    amps_uri_parse(address, address_length, &uri_state_addr_props);
    switch (uri_state_addr_props.part_id)
    {
    case AMPS_URI_PROTOCOL:
      protocol = _AMPS_STRNDUP(uri_state_addr_props.part, uri_state_addr_props.part_length);
      me->serializer = amps_message_get_protocol(protocol);
      if (me->serializer == -1)
      {
        amps_tcps_set_error(me,
                            "The URI specified an unavailable protocol.");
        result = AMPS_E_URI;
        goto error;
      }
      memcpy(&uri_state_socket_props, &uri_state_addr_props, sizeof(amps_uri_state));
      memcpy(&uri_state_ssl_props, &uri_state_addr_props, sizeof(amps_uri_state));
      break;
    case AMPS_URI_HOST:
      host = _AMPS_STRNDUP(uri_state_addr_props.part, uri_state_addr_props.part_length);
      break;
    case AMPS_URI_PORT:
      port = _AMPS_STRNDUP(uri_state_addr_props.part, uri_state_addr_props.part_length);
      break;
    case AMPS_URI_OPTION_KEY:
      if (uri_state_addr_props.part_length == 18 && memcmp(uri_state_addr_props.part, "ip_protocol_prefer", uri_state_addr_props.part_length) == 0)
      {
        ip_proto_pref_override = 1;
      }
      break;
    case AMPS_URI_OPTION_VALUE:
      if (ip_proto_pref_override)
      {
        if (uri_state_addr_props.part_length == 4 && memcmp(uri_state_addr_props.part, "ipv4", uri_state_addr_props.part_length) == 0)
        {
          ip_proto_prefer = AMPS_PREFER_IPV4;
        }
        else if (uri_state_addr_props.part_length == 4 && memcmp(uri_state_addr_props.part, "ipv6", uri_state_addr_props.part_length) == 0)
        {
          ip_proto_prefer = AMPS_PREFER_IPV6;
        }
        else
        {
          amps_tcps_set_error(me,
                              "The URI specified an invalid ip protocol preference.");
          result = AMPS_E_URI;
          goto error;
        }
      }
      break;
    default:
      break;
    }
  }
  if (uri_state_addr_props.part_id == AMPS_URI_ERROR)
  {
    amps_tcps_set_error(me, "URI format invalid.");
    result = AMPS_E_URI;
    goto error;
  }

  /* use getaddrinfo() to find an appropriate address */
  memset(&addrhints, 0, sizeof(struct addrinfo));
  addrhints.ai_socktype = SOCK_STREAM;
  addrhints.ai_protocol = 0;
  addrhints.ai_flags = (AI_V4MAPPED | AI_ADDRCONFIG);
  addrhints.ai_family = ip_proto_prefer == AMPS_PREFER_IPV6 ? AF_INET6 : AF_INET; /* Try the preferred protocol first */

  rc = getaddrinfo(host, port, &addrhints, &pAddrInfo);
  sysError = GET_ERRNO;
#ifdef _WIN32
  if (rc == EAI_FAMILY || rc == EAI_NONAME || rc == EAI_AGAIN || rc == EAI_SERVICE)
#else
  if (rc == EAI_ADDRFAMILY || rc == EAI_NONAME || rc == EAI_AGAIN || rc == EAI_SERVICE)
#endif
  {
    // didn't find any addresses of the preferred protocol, try the other one.
    addrhints.ai_family = ip_proto_prefer == AMPS_PREFER_IPV6 ? AF_INET : AF_INET6;
    rc = getaddrinfo(host, port, &addrhints, &pAddrInfo);
    sysError = GET_ERRNO;
    if (rc != 0)
    {
      /* Try preferred protocol again without AI_ADDRCONFIG */
      addrhints.ai_flags = AI_V4MAPPED;
      addrhints.ai_family = ip_proto_prefer == AMPS_PREFER_IPV6 ? AF_INET6 : AF_INET;
      rc = getaddrinfo(host, port, &addrhints, &pAddrInfo);
      sysError = GET_ERRNO;
    }
  }
  if (rc != 0)
  {
    result = AMPS_E_CONNECTION_REFUSED;
    amps_tcps_set_hostname_error(me, rc, sysError);
    freeaddrinfo(pAddrInfo);
    goto error;
  }

  // Get the socket we'll use
  fd = socket(pAddrInfo->ai_family, pAddrInfo->ai_socktype, pAddrInfo->ai_protocol);
  sysError = GET_ERRNO;
  if (fd == AMPS_INVALID_SOCKET)
  {
    freeaddrinfo(pAddrInfo);
    amps_tcps_set_socket_error(me, sysError);
    result = AMPS_E_CONNECTION_REFUSED;
    goto error;
  }

  /* apply socket properties */
  propResult = amps_tcps_apply_socket_properties(fd, address, address_length, &uri_state_socket_props);
  if (me->destroying || propResult == AMPS_PROPERTY_PARSE_ERROR)
  {
    freeaddrinfo(pAddrInfo);
    if (me->lastErrorBuf[0] == '\0' && propResult == AMPS_PROPERTY_PARSE_ERROR)
    {
      char errBuf[128];
      _AMPS_SNPRINTF(errBuf, 128, "The URI specified invalid properties: %.*s.", (int)uri_state_socket_props.part_length, uri_state_socket_props.part);
      amps_tcps_set_error(me, errBuf);
    }
    AMPS_CLOSESOCKET(fd);
    fd = AMPS_INVALID_SOCKET;
    result = AMPS_E_URI;
    goto error;
  }
  if (propResult & AMPS_PROPERTY_COMPRESSION_ZLIB)
  {
    if (amps_zlib_init(NULL) == -1)
    {
      amps_tcps_set_error(me, amps_zlib_last_error);
      freeaddrinfo(pAddrInfo);
      result = AMPS_E_URI;
#if __STDC_VERSION__ >= 201100
      me->useZlib = false;
#else
      AMPS_IEX_LONG(&me->useZlib, 0);
#endif
      AMPS_CLOSESOCKET(fd);
      fd = AMPS_INVALID_SOCKET;
      result = AMPS_E_URI;
      goto error;
    }
    if (amps_tcps_init_zlib(me) != AMPS_E_OK)
    {
      freeaddrinfo(pAddrInfo);
      result = AMPS_E_URI;
#if __STDC_VERSION__ >= 201100
      me->useZlib = false;
#else
      AMPS_IEX_LONG(&me->useZlib, 0);
#endif
      AMPS_CLOSESOCKET(fd);
      fd = AMPS_INVALID_SOCKET;
      result = AMPS_E_URI;
      goto error;
    }
#if __STDC_VERSION__ >= 201100
    me->useZlib = true;
#else
    AMPS_IEX_LONG(&me->useZlib, 1);
#endif
  }
  else
  {
#if __STDC_VERSION__ >= 201100
    me->useZlib = false;
#else
    AMPS_IEX_LONG(&me->useZlib, 0);
#endif
  }
#ifdef __APPLE__
  rc = 1; /* Set NOSIGPIPE to ON */
  if (me->destroying
      || setsockopt(fd, SOL_SOCKET, SO_NOSIGPIPE, &rc, sizeof(rc)) < 0)
  {
    freeaddrinfo(pAddrInfo);
    amps_tcps_set_error(me, "Failed to set no SIGPIPE.");
    AMPS_CLOSESOCKET(fd);
    fd = AMPS_INVALID_SOCKET;
    result = AMPS_E_CONNECTION;
    goto error;
  }
#endif

  // Call function to do SSL init and connect
  char* hostname = amps_tcps_get_sni_hostname(address, address_length, &uri_state_ssl_props);
  int portNum = atoi(port);
  amps_tcps_clear_error(me);
  me->ssl = amps_tcps_get_socket_and_ssl(fd, host, portNum, pAddrInfo, hostname, (void*)me);
  freeaddrinfo(pAddrInfo);
  if (me->destroying || me->ssl == 0)
  {
    if (!amps_tcps_get_last_error(me))
    {
      amps_tcps_set_error_stack_error(me);
      // The error string should already be set, but just in case
      if (!amps_tcps_get_last_error(me))
      {
        amps_tcps_set_error(me, "Could not initialize an SSL context or SSL.");
      }
    }
    fd = AMPS_INVALID_SOCKET;
    result = AMPS_E_SSL;
    goto error;
  }
  AMPS_IEX(&me->fd, fd);
  fd = AMPS_INVALID_SOCKET;

  // tcps transport must use read with a timeout.
  amps_tcps_set_idle_time(transport, 100);

  /* Increase the connection version now, so that anyone else attempting a reconnect knows
   * that they may not need to. */
  me->connectionVersion++;
  result = AMPS_E_OK;

  // Handle http_preflight upgrade from HTTP
  if (propResult & AMPS_PROPERTY_PREFLIGHT_TRUE && me->httpPreflightCallback)
  {
    result = _amps_tcps_handle_http_preflight(me);
    if (result != AMPS_E_OK)
    {
      if (!me->disconnecting)
      {
        fd = AMPS_IEX_GET(&me->fd, AMPS_INVALID_SOCKET);
        amps_tcps_handle_disconnect(me, me->connectionVersion);
      }
      goto error;
    }
  }

  /*  and, start up a new reader thread */
  if (me->threadCreatedCallback)
  {
    AMPS_IEX(&me->threadCreatedCallbackResult, -1);
  }
#ifdef _WIN32
  me->threadH = CreateThread(NULL, 0,
                             (LPTHREAD_START_ROUTINE)amps_tcps_threaded_reader,
                             me, CREATE_SUSPENDED, (LPDWORD)&me->thread);
  /* Now that me->thread is populated, we can start the thread.
   * important to do it in two steps, since we use me->thread as a poor-man's cancellation mechanism */
  if (me->threadH)
  {
    AMPS_INC_THREAD_COUNT(&amps_thread_create_count);
    ResumeThread(me->threadH);
  }
  else
  {
    fd = AMPS_IEX_GET(&me->fd, AMPS_INVALID_SOCKET);
    ssl = (_amps_SSL*)AMPS_IEX_GET(&me->ssl, 0);
    amps_tcps_set_error(me, "Failed to create thread for receive");
    result = AMPS_E_MEMORY;
    goto error;
  }

#else
  rc = pthread_create((pthread_t*)(&me->thread), NULL,
                      &amps_tcps_threaded_reader, me);
  if (rc != 0)
  {
    fd = AMPS_IEX_GET(&me->fd, AMPS_INVALID_SOCKET);
    ssl = AMPS_IEX_GET(&me->ssl, 0);
    amps_tcps_set_error(me, "Failed to create thread for receive");
    result = AMPS_E_MEMORY;
    goto error;
  }
  AMPS_INC_THREAD_COUNT(&amps_thread_create_count);
#endif
  for (i = 0; i < AMPS_THREAD_START_TIMEOUT && me->threadCreatedCallbackResult == -1; ++i)
  {
    AMPS_SLEEP(4);
  }
  result = (amps_result)me->threadCreatedCallbackResult;
  if (me->threadCreatedCallbackResult == -1)
  {
    amps_tcps_set_error(me, "Thread created callback failed to return in a timely manner or returned -1.");
    result = AMPS_E_MEMORY;
  }
  if (result != AMPS_E_OK)
  {
    fd = AMPS_IEX_GET(&me->fd, AMPS_INVALID_SOCKET);
    ssl = (_amps_SSL*)AMPS_IEX_GET(&me->ssl, 0);
    AMPS_JOIN(me->thread);
    amps_tcps_set_error(me, "Thread creation callback failed");
  }

error:
  if (result != AMPS_E_OK)
  {
    // Use our close function to shutdown socket and SSL
    // But don't worry about return value as error state is already set
    amps_tcps_close_all(fd, ssl);
#ifdef _WIN32
    me->thread = 0;
#else
    me->thread = (pthread_t)0;
#endif
  }
  free(protocol);
  free(host);
  free(port);
  AMPS_UNLOCK(&me->sendLock);
  AMPS_UNLOCK(&me->lock);
#ifndef _WIN32
  pthread_cleanup_pop(0);
  pthread_cleanup_pop(0);
#endif
  return result;

}

amps_result amps_tcps_set_receiver(amps_handle transport, amps_handler receiver, void* userData)
{
  amps_tcps_t* me = (amps_tcps_t*)transport;
  me->messageHandlerUserData = userData;
  me->messageHandler = receiver;
  return AMPS_E_OK;
}

amps_result amps_tcps_set_predisconnect(amps_handle transport,
                                        amps_predisconnect_handler receiver,
                                        void* userData)
{
  amps_tcps_t* me = (amps_tcps_t*)transport;
  me->predisconnectHandlerUserData = userData;
  me->predisconnectHandler = receiver;
  return AMPS_E_OK;
}

amps_result amps_tcps_set_disconnect(amps_handle transport, amps_handler receiver, void* userData)
{
  amps_tcps_t* me = (amps_tcps_t*)transport;
  me->disconnectHandlerUserData = userData;
  me->disconnectHandler = receiver;
  return AMPS_E_OK;
}

void amps_tcps_close(amps_handle transport)
{
  AMPS_JOIN_DECLARE();
  amps_tcps_t* me = (amps_tcps_t*)transport;
  AMPS_SOCKET fd = AMPS_INVALID_SOCKET;
  _amps_SSL* ssl = 0;
#if __STDC_VERSION__ >= 201100
  me->disconnecting = true;
#else
  AMPS_IEX_LONG(&me->disconnecting, 1);
#endif
  AMPS_LOCK(&me->sendLock);
#ifndef _WIN32
  pthread_cleanup_push(amps_cleanup_unlock_mutex, (void*)&me->sendLock);
#endif
  fd = AMPS_IEX_GET(&me->fd, AMPS_INVALID_SOCKET);
  ssl = (_amps_SSL*)AMPS_IEX_GET(&me->ssl, 0);
  AMPS_UNLOCK(&me->sendLock);
#ifndef _WIN32
  pthread_cleanup_pop(0);
#endif
  AMPS_SPIN_LOCK_UNLIMITED(&me->lock);
#ifndef _WIN32
  pthread_cleanup_push(amps_cleanup_unlock_mutex, (void*)&me->lock);
#endif
  // Use our close function to shutdown socket and SSL
  int rc = amps_tcps_close_all(fd, ssl);
  if (rc < 0)
  {
    int sysError = GET_ERRNO;
    amps_tcps_set_ssl_error(me, rc, sysError);
  }
  AMPS_UNLOCK(&me->lock);
#ifndef _WIN32
  pthread_cleanup_pop(0);
#endif
  AMPS_JOIN(me->thread);
}

void amps_tcps_destroy(amps_handle transport)
{
  AMPS_JOIN_DECLARE();
  amps_tcps_t* me = (amps_tcps_t*)transport;
  AMPS_SOCKET fd = AMPS_INVALID_SOCKET;
  _amps_SSL* ssl = 0;
  amps_atfork_remove(me, (_amps_atfork_callback_function)amps_tcps_atfork_handler);
  AMPS_LOCK(&me->sendLock);
#ifndef _WIN32
  pthread_cleanup_push(amps_cleanup_unlock_mutex, (void*)&me->sendLock);
#endif
  fd = AMPS_IEX_GET(&me->fd, AMPS_INVALID_SOCKET);
  ssl = (_amps_SSL*)AMPS_IEX_GET(&me->ssl, 0);
  AMPS_UNLOCK(&me->sendLock);
#ifndef _WIN32
  pthread_cleanup_pop(0);
#endif
  AMPS_LOCK(&me->lock);
#ifndef _WIN32
  pthread_cleanup_push(amps_cleanup_unlock_mutex, (void*)&me->lock);
#endif
#if __STDC_VERSION__ >= 201100
  me->destroying = true;
  me->disconnecting = true;
#else
  AMPS_IEX_LONG(&me->destroying, 1);
  AMPS_IEX_LONG(&me->disconnecting, 1);
#endif
  // Use our close function to shutdown socket and SSL
  int rc = amps_tcps_close_all(fd, ssl);
  if (rc < 0)
  {
    int sysError = GET_ERRNO;
    amps_tcps_set_ssl_error(me, rc, sysError);
  }

  AMPS_UNLOCK(&me->lock);
#ifndef _WIN32
  pthread_cleanup_pop(0);
#endif
  AMPS_JOIN(me->thread);
  AMPS_SLEEP(1);
  free(me->buf);
  if(me->pDeflater)
  {
    amps_deflateEnd(me->pDeflater);
    free(me->pDeflater);
    me->pDeflater = 0;
    free(me->pDeflateBuffer);
    me->pDeflateBuffer = 0;
  }
  if(me->pInflater)
  {
    amps_inflateEnd(me->pInflater);
    free(me->pInflater);
    me->pInflater = 0;

    free(me->pInflateBuffer);
    me->pInflateBuffer = 0;
  }
  free(me->sendCache);
  /* Hopefully, nobody else is using me right now. */
  AMPS_KILLLOCK(&me->lock);
  AMPS_KILLLOCK(&me->sendLock);

  free(me);
}

/* called with me->lock not already taken */
amps_result amps_tcps_handle_disconnect(
  amps_tcps_t* me, unsigned failedConnectionVersion)
{
  AMPS_SOCKET fd = AMPS_INVALID_SOCKET;
  _amps_SSL* ssl = 0;
#ifndef _WIN32
  int cancelState = 0;
  int unusedCancelState = 0;
#endif
  amps_result result = AMPS_E_OK;
  AMPS_LOCK(&me->sendLock);
#ifndef _WIN32
  pthread_cleanup_push(amps_cleanup_unlock_mutex, (void*)&me->sendLock);
#endif
  me->inflatePending = 0;
  fd = AMPS_IEX_GET(&me->fd, AMPS_INVALID_SOCKET);
  ssl = (_amps_SSL*)AMPS_IEX_GET(&me->ssl, 0);
  AMPS_UNLOCK(&me->sendLock);
#ifndef _WIN32
  pthread_cleanup_pop(0);
#endif
  // Use our close function to shutdown socket and SSL
  int rc = amps_tcps_close_all(fd, ssl);
  if (rc < 0)
  {
    int sysError = GET_ERRNO;
    amps_tcps_set_ssl_error(me, rc, sysError);
  }

  /* first let waiters know that we've failed. */
  me->predisconnectHandler(me, failedConnectionVersion, me->predisconnectHandlerUserData);

  /* Now take the lock on self.
   * Use a spin, the only case where it might fail should be if a recv
   * thread ends up here while a send thread is already handling disconnect
   * and it is trying to join this thread in disconnect. */
  if (AMPS_SPIN_LOCK(&me->lock) == 0)
  {
    return AMPS_E_RETRY;
  }
#ifndef _WIN32
  pthread_cleanup_push(amps_cleanup_unlock_mutex, (void*)&me->lock);
#endif

  /* if we're being destroyed, get out of here; don't worry about unlocking */
  if (me->destroying)
  {
    result = AMPS_E_DISCONNECTED; return result;
  }

  /* a new connection is available.  let someone else try. */
  if (failedConnectionVersion != me->connectionVersion)
  {
    result = AMPS_E_RETRY;
    goto error;
  }

  /* if we're disconnecting, get out of here; don't reconnect */
  if (me->disconnecting)
  {
    result = AMPS_E_DISCONNECTED;
    goto error;
  }

#ifdef _WIN32
  HANDLE tidH = (AMPS_CURRENT_THREAD() == me->thread) ? me->threadH : NULL;
#else
  pthread_setcancelstate(PTHREAD_CANCEL_DISABLE, &cancelState);
  void* vpTid = (void*)(pthread_self());
#endif
  /* Call the disconect handler. */
  result = me->disconnectHandler(me, me->disconnectHandlerUserData);
  if (result == AMPS_E_OK)
  {
#ifdef _WIN32
    if (tidH)
    {
      amps_tcps_set_thread_key(tidH);
    }
#else
    amps_tcps_set_thread_key(vpTid);
#endif
  }

error:
  AMPS_UNLOCK(&me->lock);
#ifndef _WIN32
  pthread_cleanup_pop(0);
  pthread_setcancelstate(cancelState, &unusedCancelState);
#endif

  return result;
}

void amps_tcps_handle_stream_corruption(
  amps_tcps_t* me, unsigned failedConnectionVersion)
{
  amps_tcps_set_error(me, "The connection appears corrupt.  Disconnecting.");
  amps_tcps_handle_disconnect(me, failedConnectionVersion);
}

int
amps_tcps_send_bytes(amps_tcps_t* me, char* buf, int bytesWritten)
{
  int bytesSent = 0;
  while (bytesSent < bytesWritten)
  {
    int bytesWrittenThisTime;
    if (me->useZlib)
    {
      bytesWrittenThisTime = amps_tcps_send_compressed(me, buf + bytesSent, (size_t)(bytesWritten - bytesSent));
    }
    else
    {
      bytesWrittenThisTime = _amps_SSL_write(me->ssl, buf + bytesSent, bytesWritten - bytesSent);
    }
    if (bytesWrittenThisTime <= 0)
    {
      // If error code is want read or want write, this is retryable
      int errorcode_ = _amps_SSL_get_error(me->ssl, bytesWrittenThisTime);
      if (errorcode_ == AMPS_SSL_ERROR_WANT_READ
          || errorcode_ == AMPS_SSL_ERROR_WANT_WRITE)
      {
        AMPS_UNLOCK(&me->sendLock);
        if (me->disconnecting)
        {
          amps_tcps_set_error(me, "Disconnecting.");
          return bytesWrittenThisTime;
        }
        if (me->fd == AMPS_INVALID_SOCKET)
        {
          amps_tcps_set_error(me, "Not connected.");
          return bytesWrittenThisTime;
        }
        AMPS_LOCK(&me->sendLock);
        if (me->ssl == 0)
        {
          AMPS_UNLOCK(&me->sendLock);
          amps_tcps_set_error(me, "Not connected.");
          return bytesWrittenThisTime;
        }
        continue;
      }
      return bytesWrittenThisTime;
    }
    bytesSent += bytesWrittenThisTime;
  }
  return bytesSent;
}

int
amps_tcps_send_cache(amps_tcps_t* me)
{
  me->lastSendTime = amps_now();
  int bytesSent = amps_tcps_send_bytes(me, me->sendCache, (int)(me->sendCacheOffset));
  if (bytesSent >= 0)
  {
      me->sendCacheOffset = 0;
  }
  return bytesSent;
}

amps_result
amps_tcps_send_batch(amps_handle transport,
                     amps_handle message,
                     unsigned* version_out,
                     int addToBatch)
{
  amps_result result = AMPS_E_DISCONNECTED;
  amps_tcps_t* me = (amps_tcps_t*)transport;
  size_t len = AMPS_TCPS_DEFAULT_BUF_LEN;
  int bytesWritten = -1;
  unsigned int bytesWrittenN = 0;
  int bytesSent = 0;

  *version_out = me->connectionVersion;

  if (me->disconnecting)
  {
    amps_tcps_set_error(me, "Disconnecting.");
    return AMPS_E_DISCONNECTED;
  }

  if (me->fd == AMPS_INVALID_SOCKET)
  {
    amps_tcps_set_error(me, "Not connected.");
    return AMPS_E_DISCONNECTED;
  }

  /* serialize */
  AMPS_LOCK(&me->sendLock);
#ifndef _WIN32
  pthread_cleanup_push(amps_cleanup_unlock_mutex, (void*)&me->sendLock);
#endif
  if (me->ssl == 0)
  {
    amps_tcps_set_error(me, "Not connected.");
    result = AMPS_E_DISCONNECTED;
    goto error;
  }
  while (bytesWritten < 0)
  {
    if (me->sendCache && addToBatch == 0)
    {
      // Send the cache
      bytesSent = amps_tcps_send_cache(me);
      if (bytesSent < 0)
      {
          AMPS_UNLOCK(&me->sendLock);
          result = AMPS_E_DISCONNECTED;
          goto error;
      }
    }
    if (addToBatch && me->sendBatchSizeBytes)
    {
      // Serialize into cache
      if (me->sendCache == NULL)
      {
        me->sendCache = (char*)malloc(me->sendBatchSizeBytes);
        if (me->sendCache == NULL)
        {
          amps_tcps_set_error(me, "Unable to allocate memory to cache message.");
          AMPS_UNLOCK(&me->sendLock);
          result = AMPS_E_MEMORY;
          goto error;
        }
      }
      bytesWritten = amps_message_serialize(message, me->serializer,
                                            (me->sendCache) + me->sendCacheOffset + 4,
                                            me->sendBatchSizeBytes - me->sendCacheOffset - 4);
      /* amps_message_serialize could have written 0 bytes.
       * who are we to judge?  If it returns less than 0,
       * there wasn't enough room. */
      if (bytesWritten >= 0)
      {
        // record the message length all up in the first 4 bytes.
        bytesWrittenN = htonl((unsigned int)bytesWritten);
        me->filterFunction((const unsigned char*)(me->sendCache + me->sendCacheOffset + 4),
                           (size_t)bytesWritten, 0, me->filterUserData);
        *((unsigned int*)(me->sendCache + me->sendCacheOffset)) = bytesWrittenN;
        bytesWritten += 4;
        if (!me->sendCacheOffset)
        {
          // Start the send clock based on first cachec message
          me->lastSendTime = amps_now();
        }
        me->sendCacheOffset += (size_t)bytesWritten;
        if (me->sendCacheOffset < (me->sendBatchSizeBytes - 32)
            && me->lastSendTime > (amps_now() - me->sendBatchTimeoutMillis))
        {
          result = AMPS_E_OK;
          // Not an error, but that's where cleanup is
          goto error;
        }
        bytesSent = amps_tcps_send_cache(me);
        if (bytesSent < 0)
        {
          result = AMPS_E_DISCONNECTED;
          goto error;
        }
        result = AMPS_E_OK;
        // Not an error, but that's where cleanup is
        goto error;
      }
      // Need more space, bytesWritten < 0
      if (me->sendCacheOffset)
      {
        // Send cache and try again
        bytesSent = amps_tcps_send_cache(me);
        if (bytesSent < 0)
        {
          result = AMPS_E_DISCONNECTED;
          goto error;
        }
      }
      else
      {
        // Message is larger than batch max bytes, so just send it
        addToBatch = 0;
      }
    }
    else
    {
      if (me->buf == NULL)
      {
        me->buf = (char*)malloc(len);
        if (me->buf == NULL)
        {
          amps_tcps_set_error(me, "Unable to allocate memory to send message.");
          result = AMPS_E_MEMORY;
          goto error;
        }
        me->capacity = len;
      }
      else
      {
        len = me->capacity;
      }
      /* reserve 4 bytes for the length of the message */
      bytesWritten = amps_message_serialize(message, me->serializer, (me->buf) + 4, len - 4);
      /* amps_message_serialize could have written 0 bytes.
       * who are we to judge?  If it returns less than 0,
       * there wasn't enough room. */
      if (bytesWritten >= 0)
      {
        break;
      }
      /* free this buffer, allocate a larger buffer next time */
      free(me->buf);
      me->capacity = 0;
      me->buf = NULL;
      len = (size_t)((double)len * 1.5);
    }
  }
  /* once we're done, we don't free buf -- it hangs around until we need it next time.
   * record the message length all up in the first 4 bytes. */
  bytesWrittenN = htonl((unsigned int)bytesWritten);
  me->filterFunction((const unsigned char*)(me->buf + 4), (size_t)bytesWritten, 0, me->filterUserData);
  *((unsigned int*)(me->buf)) = bytesWrittenN;
  bytesWritten += 4;
  /*now, send */
  bytesSent = amps_tcps_send_bytes(me, me->buf, bytesWritten);
  if (bytesSent <= 0)
  {
    /* record the error */
    if (me->lastErrorBuf[0] == '\0')
    {
      amps_tcps_set_error(me, "The connection is closed.");
    }
    result = AMPS_E_DISCONNECTED;
    goto error;
  }
  result = AMPS_E_OK;
error:
  AMPS_UNLOCK(&me->sendLock);
#ifndef _WIN32
  pthread_cleanup_pop(0);
#endif

  return result;
}

amps_result
amps_tcps_send_with_version(amps_handle transport,
                            amps_handle message,
                            unsigned* version_out)
{
  return amps_tcps_send_batch(transport, message, version_out, 0);
}

amps_result
amps_tcps_send(amps_handle transport,
               amps_handle message)
{
  unsigned version_out;
  return amps_tcps_send_batch(transport, message, &version_out, 0);
}

/* Returns # bytes read, 0 if a timeout occurred without a read,
 * and <0 if an error occurred.
 */
int amps_tcps_locked_read(amps_tcps_t* me_,
                          char* readPoint_,
                          int bytes_,
                          int* pErrorcode_)
{
  int rc = 0;
  int fd = (int)me_->fd;
  int locked = 0;

  while (locked == 0)
  {
    if (me_->disconnecting || fd != me_->fd || !me_->ssl
        || me_->thread != AMPS_CURRENT_THREAD()  /* our cancellation mechanism on win32 */
        || me_->destroying || fd == AMPS_INVALID_SOCKET)
    {
      return 0;
    }
    locked = (int)AMPS_SPIN_LOCK(&me_->sendLock);
  }
  if (me_->disconnecting || fd != me_->fd || !me_->ssl
      || me_->thread != AMPS_CURRENT_THREAD()  /* our cancellation mechanism on win32 */
      || me_->destroying || fd == AMPS_INVALID_SOCKET)
  {
    AMPS_UNLOCK(&me_->sendLock);
    return 0;
  }
  // Use select to wait for data if none already exists on the ssl.
  if (!_amps_SSL_pending(me_->ssl))
  {
#ifdef _WIN32
    struct timeval tv;
    fd_set readfds, exceptfds;
    tv.tv_sec = 0;
    tv.tv_usec = 1000;
    FD_ZERO(&readfds);
    FD_SET(fd, &readfds);
    FD_ZERO(&exceptfds);
    FD_SET(fd, &exceptfds);
    AMPS_UNLOCK(&me_->sendLock);
    errno = 0;
    rc  = select(1, &readfds, 0, &exceptfds, &tv);
#else
  #ifdef __APPLE__
    struct pollfd pfd = { fd, POLLIN, 0 };
  #else
    struct pollfd pfd = { fd, POLLIN|POLLRDHUP, 0 };
  #endif
    AMPS_UNLOCK(&me_->sendLock);
    errno = 0;
    rc = poll(&pfd, 1, 100);
    if (rc > 0)
    {
      // If there are no bytes ready to read, we lost connection
      if ((pfd.revents & POLLIN) == 0)
      {
        rc = 0;
      }
    }
#endif
    if (rc < 0)
    {
      return rc;
    }
    AMPS_LOCK(&me_->sendLock);
    if (me_->disconnecting || fd != me_->fd || !me_->ssl
        || me_->thread != AMPS_CURRENT_THREAD()  /* our cancellation mechanism on win32 */
        || me_->destroying || fd == AMPS_INVALID_SOCKET)
    {
      AMPS_UNLOCK(&me_->sendLock);
      return 0;
    }
  }

#ifndef _WIN32
  pthread_cleanup_push(amps_cleanup_unlock_mutex, (void*)&me_->sendLock);
#endif
  if (me_->useZlib
      && (rc > 0
          || (rc == 0
              && me_->inflatePending)))
  {
    // Make sure next_out is set
    if (!me_->pInflater->next_out)
    {
      me_->pInflater->next_out = (const char*)readPoint_;
    }
    rc = amps_tcps_recv_compressed(me_, (size_t)((const char*)(readPoint_ + bytes_) - me_->pInflater->next_out));
    *pErrorcode_ = rc <= 0 ? _amps_SSL_get_error(me_->ssl, rc) : 0;
  }
  else if (rc > 0)
  {
    errno = 0;
    rc = _amps_SSL_read(me_->ssl, readPoint_, bytes_);
    *pErrorcode_ = rc <= 0 ? _amps_SSL_get_error(me_->ssl, rc) : 0;
  }

  AMPS_UNLOCK(&me_->sendLock);
#ifndef _WIN32
  pthread_cleanup_pop(0);
#endif

  if (rc <= 0)
  {
    if (*pErrorcode_ == AMPS_SSL_ERROR_WANT_READ)
    {
      *pErrorcode_ = 0;
      return 0;
    }
    if (rc == AMPS_ZLIB_WANT_READ
        || rc == AMPS_ZLIB_NEED_SPACE)
    {
      return rc;
    }
    // End of stream
    return -1;
  }
  return rc;
}

#ifdef _WIN32
DWORD amps_tcps_threaded_reader(void* userData)
{
  AMPS_THREAD_ID tid = AMPS_CURRENT_THREAD();
  HANDLE tidH = GetCurrentThread();
  amps_tcps_t* me = (amps_tcps_t*)userData;
  if (me->threadCreatedCallback)
  {
    amps_result result = me->threadCreatedCallback(tidH,
                                                   me->threadCreatedCallbackUserData);
    AMPS_IEX(&me->threadCreatedCallbackResult, (long)result);
    if (result != AMPS_E_OK)
    {
      return (DWORD)0;
    }
  }
  else
  {
    AMPS_IEX(&me->threadCreatedCallbackResult, (long)AMPS_E_OK);
  }
#else
void* amps_tcps_threaded_reader(void* userData)
{
  int unusedCancelState = 0;
  amps_tcps_t* me = (amps_tcps_t*)userData;
  AMPS_THREAD_ID tid = AMPS_CURRENT_THREAD();
  /* Wait for pthread_create to set me->thread */
  while (me->thread != tid
         && !me->disconnecting
         && !me->destroying)
  {
    AMPS_SLEEP(5);
  }
  if (me->threadCreatedCallback)
  {
    amps_result result = me->threadCreatedCallback(me->thread,
                                                   me->threadCreatedCallbackUserData);
    AMPS_IEX(&me->threadCreatedCallbackResult, (long)result);
    if (result != AMPS_E_OK)
    {
      return NULL;
    }
  }
  else
  {
    AMPS_IEX(&me->threadCreatedCallbackResult, (long)AMPS_E_OK);
  }
#endif
  unsigned char* buffer = 0, *newBuffer = 0, *end = 0, *readPoint = 0;
  unsigned char* parsePoint = 0;

  unsigned int msglenN = 0;
  unsigned long msglen = 0, currentPosition = 0, bytesRead = 0;
  int received = 0;
  int cancelState = 0;
  const size_t BUFFER_SIZE = AMPS_TCPS_DEFAULT_BUF_LEN;
  const unsigned MAX_MESSAGE_SIZE = 1024 * 1024 * 1024;
  amps_uint64_t now = 0;
  amps_uint64_t lastReadTime = 0;
  amps_uint64_t lastIdleTime = 0;
  amps_handle   message = 0;

  /* capture the connection version we are using now. */
  unsigned connectionVersion = me->connectionVersion;
  AMPS_SOCKET fd = me->fd;

  lastReadTime = amps_now();
  lastIdleTime = lastReadTime;

#ifndef _WIN32
  pthread_setcancelstate(PTHREAD_CANCEL_DISABLE, &cancelState);
#endif
  message = amps_message_create(NULL);
  buffer = (unsigned char*)malloc(BUFFER_SIZE);
#ifndef _WIN32
  pthread_cleanup_push(amps_message_destroy, (void*)message);
  pthread_cleanup_push(amps_cleanup_free_buffer, (void*)(&buffer));
  pthread_setcancelstate(cancelState, &unusedCancelState);
#endif
  if (!buffer)
  {
    amps_tcps_handle_disconnect(me, connectionVersion);
    goto cleanup;
  }

  end = buffer + BUFFER_SIZE;
  readPoint = buffer;
  parsePoint = buffer;

  /* while we're open and not disconnecting */
  while (connectionVersion == me->connectionVersion
         && !me->disconnecting
         && fd == me->fd
         && me->thread == AMPS_CURRENT_THREAD()  /* our cancellation mechanism on win32 */
        )
  {
    int errorcode = 0;
    if (me->destroying)
    {
      goto cleanup;
    }
    now = amps_now();
    if (me->idleTimeMillis > 0 &&
        (now - lastIdleTime) > me->idleTimeMillis)
    {
      lastIdleTime = now;
#ifndef _WIN32
      cancelState = 0;
      pthread_setcancelstate(PTHREAD_CANCEL_DISABLE, &cancelState);
#endif
      me->messageHandler(0L,
                         me->messageHandlerUserData);
#ifndef _WIN32
      pthread_setcancelstate(cancelState, &unusedCancelState);
#endif
    }
    if (me->sendBatchTimeoutMillis
        && (now - me->lastSendTime) > me->sendBatchTimeoutMillis
        && me->sendCacheOffset)
    {
      AMPS_LOCK(&me->sendLock);
      int bytesSent = amps_tcps_send_cache(me);
      AMPS_UNLOCK(&me->sendLock);
      if (bytesSent < 0)
      {
        if (fd != AMPS_INVALID_SOCKET && !me->disconnecting)
        {
          shutdown(fd, SHUT_RDWR);
          amps_tcps_handle_disconnect(me, connectionVersion);
        }
        goto cleanup;
      }
    }

    received = amps_tcps_locked_read(me, (char*) readPoint,
                                     (int)(end - readPoint), &errorcode);

    if (received == AMPS_ZLIB_WANT_READ)
    {
      continue;
    }
    else if (received == AMPS_ZLIB_NEED_SPACE)
    {
      // Increase the buffer size for inflate resuults
      size_t newLength = 2 * (size_t)(end - buffer);
      newBuffer = (unsigned char*)malloc( newLength );
      if (newBuffer == NULL)
      {
        /* stream broken */
        amps_tcps_handle_stream_corruption(me, connectionVersion);
        goto cleanup;
      }
      memcpy(newBuffer, buffer, (size_t)(end - buffer));
      readPoint = newBuffer + (size_t)((unsigned const char*)readPoint - buffer);
      if (me->useZlib
          &&!me->disconnecting
          && !me->destroying)
      {
        me->pInflater->next_out = (const char*)newBuffer
                                  + (size_t)((unsigned const char*)me->pInflater->next_out - buffer);
      }
      parsePoint = newBuffer + (size_t)(parsePoint - buffer);
#ifndef _WIN32
      cancelState = 0;
      pthread_setcancelstate(PTHREAD_CANCEL_DISABLE, &cancelState);
#endif
      free(buffer);
      buffer = newBuffer;
#ifndef _WIN32
      pthread_setcancelstate(cancelState, &unusedCancelState);
#endif
      end = newBuffer + newLength;
      assert(readPoint >= parsePoint);
      continue;
    }

    if (received > 0)
    {
      if (me->useZlib
          &&!me->disconnecting
          && !me->destroying)
      {
        // Because the total length received could have been returned by
        // multiple calls, get the full size.
        received = (int)(me->pInflater->next_out - (const char*)readPoint);
        me->pInflater->next_out = NULL;
      }
      /* Call filter function without the 4 byte size */
      me->filterFunction(readPoint, (size_t)received, 1, me->filterUserData);
      readPoint += received;
      lastReadTime = amps_now();
    }
    else
    {
      // errorcode could be an ssl error code, so check for errno
      int sysError = received ? GET_ERRNO : 0;
      if (sysError)
      {
        errorcode = sysError;
      }
      if (errorcode == SOCK_ERRORCODE(EINTR))
      {
        continue;
      }
      /* disconnect if not a timeout error, or the user only set a read timeout, or the
       * read timeout has been exceeded. */
      if ( (errorcode != 0
           && ((errorcode != SOCK_ERRORCODE(ETIMEDOUT)
                && errorcode != SOCK_ERRORCODE(EWOULDBLOCK))
              || me->idleTimeMillis == 0))
           || (me->readTimeoutMillis
              && amps_now() - lastReadTime > me->readTimeoutMillis))
      {
        if (!me->disconnecting)
        {
          amps_tcps_handle_disconnect(me, connectionVersion);
        }
        goto cleanup;
      }
      continue;
    }

    while (readPoint >= parsePoint + 4 &&
           fd == me->fd &&
           me->connectionVersion == connectionVersion)
    {
      msglenN = *(unsigned int*)parsePoint;
      msglen = ntohl(msglenN);
      if (msglen > MAX_MESSAGE_SIZE)
      {
        amps_tcps_handle_stream_corruption(me, connectionVersion);
        goto cleanup;
      }
      if (readPoint >= (parsePoint + msglen + 4))
      {
        /* there are enough bytes to parse this guy. */
        parsePoint += 4;
        if (amps_message_pre_deserialize(message, me->serializer,
                                         (amps_char*)parsePoint, msglen) == AMPS_E_OK)
        {
          currentPosition = 0;
          while (currentPosition < msglen &&
                 fd == me->fd &&
                 me->connectionVersion == connectionVersion)
          {
            if (amps_message_deserialize(message, me->serializer,
                                         currentPosition,
                                         &bytesRead) != AMPS_E_OK)
            {
              amps_tcps_handle_stream_corruption(me, connectionVersion);
              goto cleanup;
            }
            if (me->messageHandler)
            {
#ifndef _WIN32
              cancelState = 0;
              pthread_setcancelstate(PTHREAD_CANCEL_DISABLE, &cancelState);
#endif
              me->messageHandler(message,
                                 me->messageHandlerUserData);
#ifndef _WIN32
              pthread_setcancelstate(cancelState, &unusedCancelState);
#endif
            }
            currentPosition += bytesRead;
          }
        }
        else
        {
          amps_tcps_handle_stream_corruption(me, connectionVersion);
          goto cleanup;
        }
        parsePoint += msglen;
      }
      else if (end < buffer + msglen + 4)
      {
        /* this message is larger than the buffer
           * resize to 2* larger of this message or current buffer size */
        size_t newLength = end < buffer + (msglen * 2) ?
                           msglen * 2 : (size_t)(end - buffer);
        newBuffer = (unsigned char*)malloc( newLength );
        if (newBuffer == NULL)
        {
          assert(readPoint >= parsePoint);
          /* stream broken */
          amps_tcps_handle_disconnect(me, connectionVersion);
          goto cleanup;
        }
        memcpy(newBuffer, parsePoint, (size_t)(readPoint - parsePoint));
        readPoint = newBuffer + (readPoint - parsePoint);
        parsePoint = newBuffer;
        // Keep next_out valid as well
        if (!me->disconnecting
            && !me->destroying
            && me->pInflater
            && me->pInflater->next_out)
        {
          me->pInflater->next_out = (const char*)newBuffer + (size_t)((unsigned const char*)me->pInflater->next_out - buffer);
        }
#ifndef _WIN32
        cancelState = 0;
        pthread_setcancelstate(PTHREAD_CANCEL_DISABLE, &cancelState);
#endif
        free(buffer);
        buffer = newBuffer;
#ifndef _WIN32
        pthread_setcancelstate(cancelState, &unusedCancelState);
#endif
        end = newBuffer + newLength;
        assert(readPoint >= parsePoint);
        break;
      }
      else
      {
        /* Need to read more data to finish this message
         * Move what we have to the front of the buffer. */
        break;
      }
    } /*while(readPoint >= parsePoint + 4) */
    // If we used some bytes, but not all, and can make room, do so
    if (readPoint > parsePoint
        && parsePoint > buffer)
    {
      memmove(buffer, parsePoint, (size_t)(readPoint - parsePoint));
    }
    readPoint = buffer + (readPoint - parsePoint);
    parsePoint = buffer;
  } /* while(fd == me->fd) */
cleanup:
#ifndef _WIN32
  cancelState = 0;
  pthread_setcancelstate(PTHREAD_CANCEL_DISABLE, &cancelState);
  pthread_cleanup_pop(0);
  pthread_cleanup_pop(0);
#endif
  amps_message_destroy(message);
  free(buffer);
  // If exiting as the reader thread, clear me->thread
  // Unless me-thread is 0, we're not getting joined, so detach
  if (me->threadExitCallback)
  {
    me->threadExitCallback(tid, me->threadExitCallbackUserData);
  }
#if __STDC_VERSION__ >= 201100
  AMPS_THREAD_ID mytid = tid;
  bool swapped = atomic_compare_exchange_strong(&(me->thread), &tid, 0);
  if (swapped || me->thread != 0)
#elif defined(_WIN32)
  // This returns the initial value of me->thread
  if (InterlockedCompareExchange((volatile unsigned int*)(&(me->thread)),
                                 (unsigned int)tid, (unsigned int)0) != 0)
#else
  AMPS_THREAD_ID mytid = tid;
  int swapped = (int)__sync_bool_compare_and_swap(&(me->thread), tid, 0);
  if (swapped || me->thread != 0)
#endif
  {
    AMPS_INC_THREAD_COUNT(&amps_thread_detach_count);
#ifdef _WIN32
    CloseHandle((HANDLE)(AMPS_IEX(&(me->threadH), 0)));
#else
    pthread_detach(mytid);
#endif
    amps_tcps_set_thread_key(NULL);
  }
#ifdef _WIN32
  else
  {
    tidH = TlsGetValue(amps_tcps_get_thread_key());
    if (tidH != NULL)
    {
      CloseHandle(tidH);
    }
  }
#endif

  return 0;
}

amps_result
amps_tcps_attempt_reconnect(amps_handle transport, unsigned version)
{
  amps_result res;
  amps_tcps_t* me = (amps_tcps_t*)transport;
  if (version == 0)
  {
    version = me->connectionVersion;
  }
  res = amps_tcps_handle_disconnect(me, version);
  if (res == AMPS_E_OK)
  {
    // We don't want non-receive threads detaching
    amps_tcps_set_thread_key(NULL);
    res = AMPS_E_RETRY;
  }
  return res;
}

/* public-api -- get a socket */
AMPS_SOCKET
amps_tcps_get_socket(amps_handle transport)
{
  amps_tcps_t* me = (amps_tcps_t*)transport;
  return me->fd;
}

void* amps_tcps_get_SSL(amps_handle transport)
{
  amps_tcps_t* me = (amps_tcps_t*)transport;
  return me->ssl;
}

amps_result
amps_tcps_set_read_timeout(amps_handle transport, int readTimeout)
{
  amps_tcps_t* me = (amps_tcps_t*)transport;
  me->readTimeoutMillis = (amps_uint64_t)readTimeout * 1000;
  return amps_tcps_update_read_timeout(me);
}


void
amps_tcps_set_filter_function(amps_handle transport, amps_transport_filter_function filterFunction_, void* userdata_)
{
  amps_tcps_t* me = (amps_tcps_t*)transport;
  me->filterUserData = userdata_;
  me->filterFunction = filterFunction_ ? filterFunction_ : amps_tcps_noop_filter_function;
}

void
amps_tcps_set_thread_created_callback(amps_handle transport_, amps_thread_created_callback threadCreatedCallback_, void* userdata_)
{
  amps_tcps_t* me = (amps_tcps_t*)transport_;
  me->threadCreatedCallbackUserData = userdata_;
  me->threadCreatedCallback = threadCreatedCallback_;
}

void
amps_tcps_set_thread_exit_callback(amps_handle transport_, amps_thread_exit_callback threadExitCallback_, void* userdata_)
{
  amps_tcps_t* me = (amps_tcps_t*)transport_;
  me->threadExitCallbackUserData = userdata_;
  me->threadExitCallback = threadExitCallback_;
}

void
amps_tcps_set_http_preflight_callback(amps_handle transport_, amps_http_preflight_callback httpPreflightCallback_, void* userdata_)
{
  amps_tcps_t* me = (amps_tcps_t*)transport_;
  me->httpPreflightCallbackUserData = userdata_;
  me->httpPreflightCallback = httpPreflightCallback_;
}

amps_result
amps_tcps_set_idle_time(amps_handle transport, int millis)
{
  amps_tcps_t* me = (amps_tcps_t*)transport;
  if (!me->idleTimeMillis || (amps_uint64_t)millis < me->idleTimeMillis)
  {
    me->idleTimeMillis = (amps_uint64_t)millis;
  }
  return amps_tcps_update_read_timeout(me);
}

void
amps_tcps_set_batch_send(amps_handle transport, amps_uint64_t batchSizeBytes, amps_uint64_t timeout)
{
  amps_tcps_t* me = (amps_tcps_t*)transport;
  me->sendBatchSizeBytes = batchSizeBytes;
  me->sendBatchTimeoutMillis = timeout;
  amps_tcps_update_read_timeout(me);
}
