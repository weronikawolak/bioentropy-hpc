#include "ascon_xof128_variable.h"

#include "api.h"
#include "ascon.h"
#include "permutations.h"
#include "word.h"

int bioentropy_ascon_xof128(
    unsigned char* out,
    size_t out_len,
    const unsigned char* in,
    size_t in_len
) {
    static const unsigned char empty_input = 0;

    if (out_len > 0 && out == NULL) {
        return -1;
    }

    if (in_len > 0 && in == NULL) {
        return -1;
    }

    if (in == NULL) {
        in = &empty_input;
    }

    /*
     * Initialization.
     *
     * This follows the reference Ascon-XOF128 implementation
     * from ascon-c, except that the requested output length is
     * supplied by the caller instead of CRYPTO_BYTES.
     */
    ascon_state_t state;

    state.x[0] = ASCON_XOF_IV;
    state.x[1] = 0;
    state.x[2] = 0;
    state.x[3] = 0;
    state.x[4] = 0;

    P12(&state);

    /*
     * Absorb complete 64-bit blocks.
     */
    while (in_len >= ASCON_HASH_RATE) {
        state.x[0] ^= LOADBYTES(
            in,
            ASCON_HASH_RATE
        );

        P12(&state);

        in += ASCON_HASH_RATE;
        in_len -= ASCON_HASH_RATE;
    }

    /*
     * Absorb and pad final partial block.
     */
    state.x[0] ^= LOADBYTES(
        in,
        in_len
    );

    state.x[0] ^= PAD(in_len);

    P12(&state);

    /*
     * Squeeze arbitrary-length output.
     */
    while (out_len > ASCON_HASH_RATE) {
        STOREBYTES(
            out,
            state.x[0],
            ASCON_HASH_RATE
        );

        P12(&state);

        out += ASCON_HASH_RATE;
        out_len -= ASCON_HASH_RATE;
    }

    if (out_len > 0) {
        STOREBYTES(
            out,
            state.x[0],
            out_len
        );
    }

    return 0;
}
