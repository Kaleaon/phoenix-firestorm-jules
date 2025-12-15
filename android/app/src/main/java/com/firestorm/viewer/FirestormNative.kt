package com.firestorm.viewer

object FirestormNative {
    /**
     * Kotlin-first bootstrap.
     *
     * We are intentionally removing the JNI dependency for now so the Android app can
     * build/run without requiring the NDK. Native/JNI can be reintroduced later behind
     * Kotlin interfaces once we have a stable Kotlin core.
     */
    fun version(): String = "kotlin-bootstrap"
}
