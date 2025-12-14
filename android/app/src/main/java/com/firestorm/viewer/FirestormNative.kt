package com.firestorm.viewer

object FirestormNative {
    init {
        System.loadLibrary("firestorm_native")
    }

    external fun version(): String
}
