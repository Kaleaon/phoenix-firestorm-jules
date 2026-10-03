package com.firestorm.viewer.llcommon

import java.util.UUID

/**
 * Kotlin port of Firestorm/LL's LLUUID basics.
 *
 * This is an incremental migration target: Android code should depend on this Kotlin type,
 * and native/C++ can be bridged behind it as needed.
 */
class LLUUID private constructor(private val data: ByteArray) {

    init {
        require(data.size == 16) { "LLUUID must be 16 bytes" }
    }

    fun toByteArray(): ByteArray = data.copyOf()

    fun isNull(): Boolean = data.all { it.toInt() == 0 }

    fun notNull(): Boolean = !isNull()

    fun asString(): String {
        val hex = "0123456789abcdef"
        val out = CharArray(36)
        var o = 0
        for (i in 0 until 16) {
            if (i == 4 || i == 6 || i == 8 || i == 10) out[o++] = '-'
            val b = data[i].toInt() and 0xFF
            out[o++] = hex[b ushr 4]
            out[o++] = hex[b and 0x0F]
        }
        return String(out)
    }

    override fun toString(): String = asString()

    /** Equivalent to C++ LLUUID::operator^ */
    fun xor(rhs: LLUUID): LLUUID {
        val out = ByteArray(16)
        for (i in 0 until 16) {
            out[i] = (this.data[i].toInt() xor rhs.data[i].toInt()).toByte()
        }
        return LLUUID(out)
    }

    /**
     * WARNING: This algorithm MUST remain MD5(uuidA||uuidB) for compatibility.
     * Matches C++ LLUUID::combine().
     */
    fun combine(other: LLUUID): LLUUID {
        val md5 = LLMD5()
        md5.update(this.data)
        md5.update(other.data)
        md5.finalizeDigest()
        return LLUUID(md5.rawDigest())
    }

    /** Sum of 8 little-endian 16-bit words (matches typical viewer behavior). */
    fun getCRC16(): Int {
        var sum = 0
        for (i in 0 until 8) {
            val lo = data[i * 2].toInt() and 0xFF
            val hi = data[i * 2 + 1].toInt() and 0xFF
            sum = (sum + (lo or (hi shl 8))) and 0xFFFF
        }
        return sum
    }

    /** Sum of 4 little-endian 32-bit words. */
    fun getCRC32(): Long {
        var sum = 0L
        for (i in 0 until 4) {
            val b0 = data[i * 4].toLong() and 0xFF
            val b1 = data[i * 4 + 1].toLong() and 0xFF
            val b2 = data[i * 4 + 2].toLong() and 0xFF
            val b3 = data[i * 4 + 3].toLong() and 0xFF
            val word = b0 or (b1 shl 8) or (b2 shl 16) or (b3 shl 24)
            sum += word
        }
        return sum and 0xFFFFFFFFL
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is LLUUID) return false
        return data.contentEquals(other.data)
    }

    override fun hashCode(): Int = data.contentHashCode()

    companion object {
        val NULL: LLUUID = LLUUID(ByteArray(16))

        fun random(): LLUUID {
            val u = UUID.randomUUID()
            val out = ByteArray(16)
            var msb = u.mostSignificantBits
            var lsb = u.leastSignificantBits
            for (i in 0 until 8) {
                out[7 - i] = (msb and 0xFFL).toByte()
                msb = msb ushr 8
                out[15 - i] = (lsb and 0xFFL).toByte()
                lsb = lsb ushr 8
            }
            return LLUUID(out)
        }

        /** Accepts canonical (36 chars), legacy-broken (35 chars; missing last hyphen), or raw 32 hex chars. */
        fun validate(input: String): Boolean {
            val s = input.trim()
            if (s.isEmpty()) return true

            val allowedLengths = setOf(36, 35, 32)
            if (s.length !in allowedLengths) return false

            if (s.length == 36) {
                if (!(s[8] == '-' && s[13] == '-' && s[18] == '-' && s[23] == '-')) return false
            } else if (s.length == 35) {
                // legacy broken format: missing the final hyphen
                if (!(s[8] == '-' && s[13] == '-' && s[18] == '-')) return false
                if (s.count { it == '-' } != 3) return false
            }

            val hexOnly = buildString(32) {
                for (ch in s) if (ch != '-') append(ch)
            }
            if (hexOnly.length != 32) return false
            return hexOnly.all { it.isDigit() || (it.lowercaseChar() in 'a'..'f') }
        }

        /** Returns NULL for empty input; null for invalid. */
        fun fromString(input: String): LLUUID? {
            val s = input.trim()
            if (s.isEmpty()) return NULL
            if (!validate(s)) return null

            val hex = buildString(32) {
                for (ch in s) if (ch != '-') append(ch.lowercaseChar())
            }
            if (hex.length != 32) return null

            val out = ByteArray(16)
            for (i in 0 until 16) {
                val hi = hexDigit(hex[i * 2])
                val lo = hexDigit(hex[i * 2 + 1])
                if (hi < 0 || lo < 0) return null
                out[i] = ((hi shl 4) or lo).toByte()
            }
            return LLUUID(out)
        }

        private fun hexDigit(ch: Char): Int = when (ch) {
            in '0'..'9' -> ch.code - '0'.code
            in 'a'..'f' -> 10 + (ch.code - 'a'.code)
            in 'A'..'F' -> 10 + (ch.code - 'A'.code)
            else -> -1
        }
    }
}
