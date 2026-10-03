package com.firestorm.viewer.llcommon

import java.util.Base64

/**
 * Kotlin port of `indra/llcommon/llbase64.*`.
 */
object LLBase64 {

    fun encode(input: ByteArray): String {
        if (input.isEmpty()) return ""
        return Base64.getEncoder().encodeToString(input)
    }

    /**
     * Equivalent to C++ `LLBase64::decodeAsString()`.
     *
     * C++ behavior uses `std::string::assign(char*)` which stops at the first NUL byte.
     * We mirror that by truncating decoded bytes at the first 0 byte and interpreting
     * the remainder as UTF-8.
     */
    fun decodeAsString(input: String): String {
        val decoded = decode(input)
        val n = decoded.indexOfFirst { it == 0.toByte() }.let { if (it < 0) decoded.size else it }
        return decoded.copyOfRange(0, n).toString(Charsets.UTF_8)
    }

    /** Safer decode for binary payloads. */
    fun decode(input: String): ByteArray {
        if (input.isEmpty()) return ByteArray(0)
        return Base64.getDecoder().decode(input)
    }
}
