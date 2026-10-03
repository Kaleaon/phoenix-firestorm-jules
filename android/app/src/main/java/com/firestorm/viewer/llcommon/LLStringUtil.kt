package com.firestorm.viewer.llcommon

/**
 * Kotlin-first subset port of `indra/llcommon/llstring.*`.
 *
 * This intentionally focuses on the small, frequently-used utilities we can safely
 * depend on early in an Android/Kotlin migration.
 */
object LLStringUtil {

    fun safeString(input: String?): String = input ?: ""

    fun safeString(input: String?, maxLen: Int): String {
        if (input == null) return ""
        if (maxLen <= 0) return ""
        return if (input.length <= maxLen) input else input.substring(0, maxLen)
    }

    fun trimHead(s: String): String = s.dropWhile { it.isWhitespace() }

    fun trimTail(s: String): String = s.dropLastWhile { it.isWhitespace() }

    fun trim(s: String): String = trimTail(trimHead(s))

    fun startsWith(string: String, substr: String): Boolean {
        if (string.isEmpty() || substr.isEmpty()) return false
        return string.startsWith(substr)
    }

    fun endsWith(string: String, substr: String): Boolean {
        if (string.isEmpty() || substr.isEmpty()) return false
        return string.endsWith(substr)
    }

    fun replaceChar(string: String, target: Char, replacement: Char): String {
        if (string.isEmpty()) return string
        return string.replace(target, replacement)
    }

    fun replaceString(string: String, target: String, replacement: String): String {
        if (string.isEmpty() || target.isEmpty()) return string
        return string.replace(target, replacement)
    }

    /**
     * Quote string if it contains any trigger char (default space or quote), unless already quoted.
     * Mirrors the behavior of `LLStringUtilBase<T>::quote()`.
     */
    fun quote(str: String, triggers: String = " \"", escape: String = "\\"): String {
        if (str.length >= 2 && str.first() == '"' && str.last() == '"') return str
        if (triggers.isNotEmpty() && str.none { it in triggers }) return str

        val out = StringBuilder(str.length + 2)
        out.append('"')
        for (ch in str) {
            if (ch == '"') out.append(escape)
            out.append(ch)
        }
        out.append('"')
        return out.toString()
    }

    /**
     * Tokenize with a single delimiter set: treats any run of delimiter characters as one separator.
     * Mirrors the simplest `getTokens(instr, tokens, delims)` behavior.
     */
    fun getTokens(instr: String, delims: String): List<String> {
        return getTokens(instr, dropDelims = delims, keepDelims = "", quotes = "", escapes = "")
    }

    /**
     * Tokenize with drop/keep delimiters and optional quoting.
     *
     * - **dropDelims**: skipped separators (runs are treated as one)
     * - **keepDelims**: delimiters emitted as standalone 1-char tokens
     * - **quotes**: quote chars that can wrap substrings within a token (bash-like)
     * - **escapes**: escape chars (if present, escape the next char)
     */
    fun getTokens(
        instr: String,
        dropDelims: String,
        keepDelims: String,
        quotes: String = "",
        escapes: String = "",
    ): List<String> {
        if (instr.isEmpty()) return emptyList()

        val tokens = ArrayList<String>()
        val allDelims = dropDelims + keepDelims

        var i = 0
        fun done(): Boolean = i >= instr.length

        fun isEscapedAt(pos: Int): Boolean {
            if (escapes.isEmpty()) return false
            if (pos >= instr.length) return false
            val ch = instr[pos]
            return (ch in escapes) && (pos + 1 < instr.length)
        }

        fun nextChar(): Char {
            val esc = isEscapedAt(i)
            if (esc) i++
            val ch = instr[i]
            i++
            return ch
        }

        fun currentChar(): Char = instr[i]

        fun oneOf(set: String): Boolean {
            if (done()) return false
            if (isEscapedAt(i)) return false
            return currentChar() in set
        }

        while (!done()) {
            // skip any drop delims
            while (oneOf(dropDelims)) {
                i++
                if (done()) return tokens
            }

            if (oneOf(keepDelims)) {
                tokens.add(currentChar().toString())
                i++
                continue
            }

            // start a new token
            val token = StringBuilder()
            while (!done() && !oneOf(allDelims)) {
                // quoted substring?
                if (quotes.isNotEmpty() && oneOf(quotes)) {
                    val quoteChar = currentChar()
                    val quotePos = i
                    i++ // consume open quote

                    val collected = StringBuilder()
                    var foundClose = false
                    while (!done()) {
                        if (!isEscapedAt(i) && currentChar() == quoteChar) {
                            i++ // consume close quote
                            foundClose = true
                            break
                        }
                        collected.append(nextChar())
                    }

                    if (foundClose) {
                        token.append(collected)
                        continue
                    } else {
                        // unmatched quote: treat it literally (like C++ behavior described in comments)
                        i = quotePos
                        token.append(nextChar())
                        continue
                    }
                }

                token.append(nextChar())
            }

            tokens.add(token.toString())
        }

        return tokens
    }

    fun isCharHex(ch: Char): Boolean =
        (ch in '0'..'9') || (ch in 'a'..'f') || (ch in 'A'..'F')

    fun hexAsNibble(ch: Char): Int = when (ch) {
        in '0'..'9' -> ch.code - '0'.code
        in 'a'..'f' -> 10 + (ch.code - 'a'.code)
        in 'A'..'F' -> 10 + (ch.code - 'A'.code)
        else -> 0
    }
}
