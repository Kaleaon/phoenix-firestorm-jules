/**
 * @file lluictrl_stub.cpp
 * @brief Stub implementations for LLUICtrl unit test dependencies
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
#include "../llpanel.h"
#include "../lltabcontainer.h"

// Stubs for LLPanel
LLPanel::~LLPanel() {}
bool LLPanel::isPanel() const { return true; }
void LLPanel::draw() {}
bool LLPanel::handleKeyHere(KEY key, MASK mask) { return false; }
void LLPanel::onVisibilityChange(bool new_visibility) {}
void LLPanel::setFocus(bool b) {}
void LLPanel::refresh() {}
void LLPanel::clearCtrls() {}
bool LLPanel::postBuild() { return true; }
void LLPanel::bindAccessibleLabels() {}

// Stubs for LLTabContainer
LLTabContainer::~LLTabContainer() {}
void LLTabContainer::setValue(const LLSD& value) {}
void LLTabContainer::reshape(S32 width, S32 height, bool called_from_parent) {}
void LLTabContainer::draw() {}
bool LLTabContainer::handleMouseDown(S32 x, S32 y, MASK mask) { return false; }
bool LLTabContainer::handleHover(S32 x, S32 y, MASK mask) { return false; }
bool LLTabContainer::handleMouseUp(S32 x, S32 y, MASK mask) { return false; }
bool LLTabContainer::handleScrollWheel(S32 x, S32 y, S32 clicks) { return false; }
bool LLTabContainer::handleToolTip(S32 x, S32 y, MASK mask) { return false; }
bool LLTabContainer::handleKeyHere(KEY key, MASK mask) { return false; }
bool LLTabContainer::handleDragAndDrop(S32 x, S32 y, MASK mask, bool drop, EDeflectUtils deflect_utils, LLUUID source_id, void* user_data) { return false; }
LLView* LLTabContainer::getChildView(std::string_view name, bool recurse) const { return NULL; }
LLView* LLTabContainer::findChildView(std::string_view name, bool recurse) const { return NULL; }
void LLTabContainer::initFromParams(const LLPanel::Params& p) {}
bool LLTabContainer::addChild(LLView* view, S32 tab_group) { return false; }
bool LLTabContainer::postBuild() { return true; }
LLPanel* LLTabContainer::getCurrentPanel() { return NULL; }
