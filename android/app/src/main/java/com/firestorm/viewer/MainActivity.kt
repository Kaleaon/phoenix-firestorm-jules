package com.firestorm.viewer

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.firestorm.viewer.llcommon.LLUUID

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Proof-of-life call into native layer; we’ll gradually replace native pieces with Kotlin.
        val version = FirestormNative.version()
        // First file-by-file Kotlin port: LLUUID (see llcommon/LLUUID.kt).
        val id = LLUUID.random()
        check(LLUUID.fromString(id.asString()) == id)

        title = "Firestorm ($version) ${id.asString().take(8)}"
    }
}
