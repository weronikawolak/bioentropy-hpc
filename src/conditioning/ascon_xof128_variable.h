#pragma once

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

int bioentropy_ascon_xof128(
    unsigned char* out,
    size_t out_len,
    const unsigned char* in,
    size_t in_len
);

#ifdef __cplusplus
}
#endif
