////////////////////////////////////////////////////////////////////////////
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
////////////////////////////////////////////////////////////////////////////
#pragma once

/*********************************************************
 * amps_zlib
 *
 * This is a simple wrapper around a dynamically-loaded zlib implementation.
 *********************************************************/

#ifdef _cplusplus
extern "C"
{
#endif

typedef struct
{
    const char* next_in;
    unsigned int avail_in;
    unsigned long total_in;

    const char* next_out;
    unsigned int avail_out;
    unsigned long total_out;

    const char* msg;
    void* state;

    void* zalloc;
    void* zfree;
    void* opaque;

    int data_type;
    unsigned long adler;
    unsigned long reserved;
} amps_zstream;

// Loads zlib dynamic library; returns 0 on success, nonzero on error.
extern int amps_zlib_init(const char*);
extern char amps_zlib_last_error[];
extern int amps_zlib_is_loaded;

// Headers/loaders for just the functions we use.
typedef const char* (*amps_zlibVersion_t)(void);
typedef int (*amps_deflateInit2_t)(amps_zstream*, int, int, int, int, int, const char*, size_t);
typedef int (*amps_deflate_t)(amps_zstream*, int);
typedef int (*amps_deflate_end_t)(amps_zstream*);
typedef int (*amps_inflateInit2_t)(amps_zstream*, int, const char*, size_t);
typedef int (*amps_inflate_t)(amps_zstream*, int);
typedef int (*amps_inflate_end_t)(amps_zstream*);

extern amps_zlibVersion_t amps_zlibVersion;
extern amps_deflateInit2_t amps_deflateInit2_;
extern amps_deflate_t amps_deflate;
extern amps_deflate_end_t amps_deflateEnd;

extern amps_inflateInit2_t amps_inflateInit2_;
extern amps_inflate_t amps_inflate;
extern amps_inflate_end_t amps_inflateEnd;

#define amps_deflateInit2(stream, level, method, windowBits, memlevel, strategy) \
  amps_deflateInit2_(stream, level, method, windowBits, memlevel, strategy, "1.0.1", sizeof(amps_zstream))

#define amps_inflateInit2(stream, windowBits) \
  amps_inflateInit2_(stream, windowBits, "1.0.1", sizeof(amps_zstream));

#define AMPS_ZLIB_WANT_READ  (-254)
#define AMPS_ZLIB_NEED_SPACE (-253)

#ifdef _cplusplus
}
#endif
