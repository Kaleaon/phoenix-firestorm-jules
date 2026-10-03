package com.firestorm.viewer.llcommon

import java.io.InputStream
import java.security.MessageDigest

/**
 * Kotlin port of `indra/llcommon/llmd5.{h,cpp}`.
 *
 * Notes:
 * - This is intentionally a thin wrapper around the JCA MD5 implementation.
 * - API shape follows the viewer's LLMD5 usage patterns: update(), finalize(), rawDigest(), hexDigest().
 */
class LLMD5 {

    private var md: MessageDigest = MessageDigest.getInstance("MD5")
    private var finalized: Boolean = false
    private var digest: ByteArray? = null

    fun update(input: ByteArray, offset: Int = 0, length: Int = input.size - offset) {
        require(!finalized) { "LLMD5.update: Can't update a finalized digest" }
        require(offset >= 0 && length >= 0 && offset + length <= input.size) { "Invalid input range" }
        md.update(input, offset, length)
    }

    fun update(input: String) {
        // LLMD5 in C++ digests raw bytes of std::string; in our Kotlin/Android world
        // we treat String as UTF-8.
        update(input.encodeToByteArray())
    }

    fun update(stream: InputStream, blockLen: Int = 4096) {
        require(!finalized) { "LLMD5.update: Can't update a finalized digest" }
        val buf = ByteArray(blockLen)
        while (true) {
            val read = stream.read(buf)
            if (read <= 0) break
            md.update(buf, 0, read)
        }
    }

    fun finalizeDigest() {
        if (finalized) return
        digest = md.digest()
        finalized = true
    }

    fun rawDigest(): ByteArray {
        require(finalized) { "LLMD5.rawDigest: finalizeDigest() must be called first" }
        return requireNotNull(digest).copyOf()
    }

    fun hexDigest(): String {
        val d = rawDigest()
        val hex = "0123456789abcdef"
        val out = CharArray(d.size * 2)
        var o = 0
        for (b in d) {
            val v = b.toInt() and 0xFF
            out[o++] = hex[v ushr 4]
            out[o++] = hex[v and 0x0F]
        }
        return String(out)
    }

    companion object {
        fun digestBytes(bytes: ByteArray): ByteArray {
            val md5 = LLMD5()
            md5.update(bytes)
            md5.finalizeDigest()
            return md5.rawDigest()
        }

        /** Matches the C++ helper ctor that digests "%s:%i". */
        fun digestStringColonNumber(prefix: ByteArray, number: Int): ByteArray {
            val md5 = LLMD5()
            md5.update(prefix)
            md5.update(":")
            md5.update(number.toString())
            md5.finalizeDigest()
            return md5.rawDigest()
        }
    }
}
