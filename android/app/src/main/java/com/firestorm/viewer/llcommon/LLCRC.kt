package com.firestorm.viewer.llcommon

/**
 * Kotlin port of `indra/llcommon/llcrc.*`.
 *
 * CRC polynomial: 0xEDB88320 (IEEE/ZIP CRC-32, reflected)
 * Init: 0xFFFFFFFF
 * Final XOR: 0xFFFFFFFF
 */
class LLCRC {

    // stored as unsigned 32-bit value in an Int
    private var current: Int = -1 // 0xFFFFFFFF

    fun update(nextByte: Byte) {
        val idx = (current xor (nextByte.toInt() and 0xFF)) and 0xFF
        current = TABLE[idx] xor (current ushr 8)
    }

    fun update(buffer: ByteArray, offset: Int = 0, length: Int = buffer.size - offset) {
        require(offset >= 0 && length >= 0 && offset + length <= buffer.size) { "Invalid input range" }
        for (i in 0 until length) {
            update(buffer[offset + i])
        }
    }

    /** Returns bitwise-not of the running CRC (matches C++ getCRC()). */
    fun getCRC(): Long = (current.inv().toLong() and 0xFFFF_FFFFL)

    companion object {
        private val TABLE: IntArray = buildTable()

        private fun buildTable(): IntArray {
            val table = IntArray(256)
            for (n in 0 until 256) {
                var c = n
                for (k in 0 until 8) {
                    c = if ((c and 1) != 0) {
                        0xEDB88320.toInt() xor (c ushr 1)
                    } else {
                        c ushr 1
                    }
                }
                table[n] = c
            }
            return table
        }

        fun testHarness(): Boolean {
            val test = "hello &#$)$&Nd0".encodeToByteArray() // matches C++ buffer content (without explicit NUL)
            val c1 = LLCRC().apply { update(test) }
            val c2 = LLCRC().apply {
                for (b in test) update(b)
            }
            return c1.getCRC() == c2.getCRC()
        }

        fun crcOf(bytes: ByteArray): Long = LLCRC().apply { update(bytes) }.getCRC()
    }
}
