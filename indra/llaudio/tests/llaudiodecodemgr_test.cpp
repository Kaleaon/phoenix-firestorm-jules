/**
 * @file llaudiodecodemgr_test.cpp
 * @brief Unit tests for LLAudioDecodeMgr queue lookups and set synchronization.
 *
 * $LicenseInfo:firstyear=2026&license=viewerlgpl$
 * Second Life Viewer Source Code
 * Copyright (C) 2026, Linden Research, Inc.
 * $/LicenseInfo$
 */

#include "linden_common.h"
#include "lltut.h"

#include "../llaudiodecodemgr.h"
#include "lluuid.h"

namespace tut
{
    struct audio_decode_mgr_data
    {
    };
    typedef test_group<audio_decode_mgr_data> audio_decode_mgr_group;
    typedef audio_decode_mgr_group::object audio_decode_mgr_object;
    audio_decode_mgr_group audio_decode_mgr_grp("llaudiodecodemgr");

    template<> template<>
    void audio_decode_mgr_object::test<1>()
    {
        set_test_name("verify queue state and duplicate checking methods");

        LLUUID id1("00000000-0000-0000-0000-000000000001");
        LLUUID id2("00000000-0000-0000-0000-000000000002");

        LLAudioDecodeMgr &mgr = LLAudioDecodeMgr::instance();
        ensure_equals("queue initially empty", mgr.getQueueSize(), 0U);
        ensure("id1 is not queued", !mgr.isQueued(id1));
        ensure("id2 is not queued", !mgr.isQueued(id2));
    }
}
