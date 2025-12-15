package com.firestorm.viewer.llcommon

import kotlin.math.max

/**
 * Kotlin port of `indra/llcommon/lltimer.{h,cpp}` (Android-safe).
 *
 * Semantics match the C++ implementation:
 * - `getElapsedTimeF64/F32()` do NOT modify internal state (time since last reset/lastClockCount).
 * - `getElapsedTimeAndResetF64/F32()` update the internal start point.
 * - `reset()` also clears expiration ticks.
 * - `hasExpired()` is true when now >= expiration; with default expiration=0 it is effectively "expired".
 */
class LLTimer {

    private var lastClockCountNanos: Long = nowNanos()
    private var expirationNanos: Long = 0L
    private var started: Boolean = false

    fun start() {
        reset()
        started = true
    }

    fun stop() {
        started = false
    }

    fun reset() {
        lastClockCountNanos = nowNanos()
        expirationNanos = 0L
    }

    fun setLastClockCount(currentCountNanos: Long) {
        lastClockCountNanos = currentCountNanos
    }

    fun setTimerExpirySec(expirationSeconds: Float) {
        expirationNanos = nowNanos() + (expirationSeconds * 1_000_000_000f).toLong()
    }

    fun checkExpirationAndReset(expirationSeconds: Float): Boolean {
        val now = nowNanos()
        if (now < expirationNanos) return false
        expirationNanos = now + (expirationSeconds * 1_000_000_000f).toLong()
        return true
    }

    fun hasExpired(): Boolean = nowNanos() >= expirationNanos

    fun getElapsedTimeF64(): Double {
        val elapsedNanos = safeElapsed(nowNanos(), lastClockCountNanos)
        return elapsedNanos / 1_000_000_000.0
    }

    fun getElapsedTimeF32(): Float = getElapsedTimeF64().toFloat()

    fun getElapsedTimeAndResetF64(): Double {
        val now = nowNanos()
        val elapsedNanos = safeElapsed(now, lastClockCountNanos)
        lastClockCountNanos = now
        return elapsedNanos / 1_000_000_000.0
    }

    fun getElapsedTimeAndResetF32(): Float = getElapsedTimeAndResetF64().toFloat()

    fun getRemainingTimeF32(): Float {
        val now = nowNanos()
        if (now > expirationNanos) return 0f
        return ((expirationNanos - now) / 1_000_000_000.0).toFloat()
    }

    fun getStarted(): Boolean = started

    companion object {
        @Volatile
        var sTimer: LLTimer? = null
            private set

        fun initClass() {
            if (sTimer == null) sTimer = LLTimer()
        }

        fun cleanupClass() {
            sTimer = null
        }

        /** Equivalent to C++ LLTimer::getElapsedSeconds(). */
        fun getElapsedSeconds(): Double = sTimer?.getElapsedTimeF64() ?: 0.0

        /** Equivalent to C++ LLTimer::getCurrentClockCount(). */
        fun getCurrentClockCount(): Long = nowNanos()

        /** Equivalent to C++ LLTimer::getTotalTime() (microseconds since epoch). */
        fun getTotalTimeMicros(): Long = System.currentTimeMillis() * 1_000L

        /** Equivalent to C++ LLTimer::getTotalSeconds(). */
        fun getTotalSeconds(): Double = getTotalTimeMicros() / 1_000_000.0

        /** Simple millisecond sleep (best-effort). */
        fun msSleep(ms: Long) {
            if (ms <= 0) return
            Thread.sleep(ms)
        }

        private fun nowNanos(): Long = System.nanoTime()

        private fun safeElapsed(now: Long, last: Long): Long = max(0L, now - last)
    }
}
