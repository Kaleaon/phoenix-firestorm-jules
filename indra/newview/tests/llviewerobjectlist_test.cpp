/**
 * @file llviewerobjectlist_test.cpp
 * @brief Unit tests for hash map indexing in LLViewerObjectList orphan object handling.
 *
 * $LicenseInfo:firstyear=2026&license=viewerlgpl$
 * Second Life Viewer Source Code
 * Copyright (C) 2026, Linden Research, Inc.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation;
 * version 2.1 of the License only.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * Linden Research, Inc., 945 Battery Street, San Francisco, CA  94111  USA
 * $/LicenseInfo$
 */

#include "linden_common.h"
#include "../test/lltut.h"

#include "../llviewerobjectlist.h"

#include <chrono>
#include <iostream>

namespace tut
{
    struct orphan_test_data
    {
        LLViewerObjectList object_list;
        orphan_test_data() = default;
        ~orphan_test_data() = default;
    };

    typedef test_group<orphan_test_data> orphan_test_group;
    typedef orphan_test_group::object orphan_test_object;
    orphan_test_group orphan_grp("llviewerobjectlist_orphan");

    template<> template<>
    void orphan_test_object::test<1>()
    {
        set_test_name("Initial orphan state");
        ensure_equals("Initial orphan parent count should be 0", object_list.getOrphanParentCount(), 0);
        ensure_equals("Initial orphan count should be 0", object_list.getOrphanCount(), 0);
    }

    template<> template<>
    void orphan_test_object::test<2>()
    {
        set_test_name("Adding orphans and duplicate prevention");
        U64 parent_info_1 = 0x1111222233334444ULL;
        U64 parent_info_2 = 0x5555666677778888ULL;
        LLUUID child_1("00000000-0000-0000-0000-000000000001");
        LLUUID child_2("00000000-0000-0000-0000-000000000002");
        LLUUID child_3("00000000-0000-0000-0000-000000000003");

        object_list.addOrphan(parent_info_1, child_1);
        ensure_equals("Orphan parent count after child 1", object_list.getOrphanParentCount(), 1);
        ensure_equals("Orphan count after child 1", object_list.getOrphanCount(), 1);

        // Add duplicate child_1 for parent_info_1
        object_list.addOrphan(parent_info_1, child_1);
        ensure_equals("Orphan parent count after duplicate child 1", object_list.getOrphanParentCount(), 1);
        ensure_equals("Orphan count after duplicate child 1", object_list.getOrphanCount(), 1);

        // Add child_2 for parent_info_1
        object_list.addOrphan(parent_info_1, child_2);
        ensure_equals("Orphan parent count after child 2", object_list.getOrphanParentCount(), 1);
        ensure_equals("Orphan count after child 2", object_list.getOrphanCount(), 2);

        // Add child_3 for parent_info_2
        object_list.addOrphan(parent_info_2, child_3);
        ensure_equals("Orphan parent count after child 3", object_list.getOrphanParentCount(), 2);
        ensure_equals("Orphan count after child 3", object_list.getOrphanCount(), 3);
    }

    template<> template<>
    void orphan_test_object::test<3>()
    {
        set_test_name("Performance benchmark for 10,000 out-of-order orphans");
        const S32 NUM_PARENTS = 1000;
        const S32 CHILDREN_PER_PARENT = 10;
        const S32 TOTAL_ORPHANS = NUM_PARENTS * CHILDREN_PER_PARENT;

        auto start_add = std::chrono::high_resolution_clock::now();
        for (S32 p = 0; p < NUM_PARENTS; ++p)
        {
            U64 parent_info = 0x1000000000000000ULL + p;
            for (S32 c = 0; c < CHILDREN_PER_PARENT; ++c)
            {
                LLUUID child_id;
                child_id.generate();
                object_list.addOrphan(parent_info, child_id);
            }
        }
        auto end_add = std::chrono::high_resolution_clock::now();
        auto add_duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_add - start_add).count();

        ensure_equals("Orphan parent count should equal NUM_PARENTS", object_list.getOrphanParentCount(), NUM_PARENTS);
        ensure_equals("Orphan count should equal TOTAL_ORPHANS", object_list.getOrphanCount(), TOTAL_ORPHANS);

        std::cout << "[PERF] Time to add " << TOTAL_ORPHANS << " orphans: " << add_duration << " ms" << std::endl;
        ensure("Add duration should be under 1000ms", add_duration < 1000);
    }
}
