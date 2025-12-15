package com.firestorm.viewer

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.firestorm.viewer.llcommon.LLBase64
import com.firestorm.viewer.llcommon.LLMD5
import com.firestorm.viewer.llcommon.LLCRC
import com.firestorm.viewer.llcommon.LLTimer
import com.firestorm.viewer.llcommon.LLStringUtil
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

        val md5 = LLMD5()
        md5.update(id.asString())
        md5.finalizeDigest()

        // Kotlin port: LLTimer (see llcommon/LLTimer.kt)
        LLTimer.initClass()
        val uptime = LLTimer.getElapsedSeconds()

        // Kotlin port: LLStringUtil (subset of llstring.*)
        val tokens = LLStringUtil.getTokens("""~/\"sub dir\"/myfile.txt""", dropDelims = "/", keepDelims = "/", quotes = "\"", escapes = "\\")
        check(tokens.isNotEmpty())

        // Kotlin ports: LLBase64 + LLCRC
        val payload = "hello &#$)$&Nd0".encodeToByteArray()
        val b64 = LLBase64.encode(payload)
        check(LLBase64.decode(b64).contentEquals(payload))
        check(LLCRC.testHarness())

        title = "Firestorm ($version) ${id.asString().take(8)} ${md5.hexDigest().take(6)} t=${"%.2f".format(uptime)} tok=${tokens.size} crc=${LLCRC.crcOf(payload).toString(16)}"
    }
}
