/**
 * @file lluictrl_test.cpp
 * @brief Unit tests for LLUICtrl accessibility binding and label_for functionality
 */

#include "linden_common.h"
#include "lltut.h"

#include "../lluictrl.h"
#include "../llpanel.h"
#include "../lltextbox.h"
#include "../llcheckboxctrl.h"
#include "../llcombobox.h"
#include "../lllineeditor.h"
#include "../llspinctrl.h"
#include "../llsliderctrl.h"

namespace tut
{
    struct lluictrl_test_data
    {
    };

    typedef test_group<lluictrl_test_data> lluictrl_test_group;
    typedef lluictrl_test_group::object lluictrl_test_object;
    lluictrl_test_group lluictrl_instance("LLUICtrl");

    template<> template<>
    void lluictrl_test_object::test<1>()
    {
        // Test 1: LLUICtrl label_for and accessible_name getters and setters
        LLUICtrl::Params p;
        p.name("test_ctrl");
        p.label_for("target_input");
        p.accessible_name("Explicit Accessible Name");

        LLUICtrl ctrl(p);
        ctrl.initFromParams(p);

        ensure_equals("label_for parsed from params", ctrl.getLabelFor(), "target_input");
        ensure_equals("accessible_name parsed from params", ctrl.getAccessibleName(), "Explicit Accessible Name");

        ctrl.setLabelFor("new_target");
        ensure_equals("setLabelFor updates value", ctrl.getLabelFor(), "new_target");

        ctrl.setAccessibleName("Updated Accessible Name");
        ensure_equals("setAccessibleName updates value", ctrl.getAccessibleName(), "Updated Accessible Name");
    }

    template<> template<>
    void lluictrl_test_object::test<2>()
    {
        // Test 2: Composite controls forward setAccessibleName
        LLSpinCtrl::Params spin_p;
        spin_p.name("spin_test");
        LLSpinCtrl spin(spin_p);
        spin.setAccessibleName("Spin Label");
        ensure_equals("LLSpinCtrl accessible name set", spin.getAccessibleName(), "Spin Label");

        LLSliderCtrl::Params slider_p;
        slider_p.name("slider_test");
        LLSliderCtrl slider(slider_p);
        slider.setAccessibleName("Slider Label");
        ensure_equals("LLSliderCtrl accessible name set", slider.getAccessibleName(), "Slider Label");
    }

    template<> template<>
    void lluictrl_test_object::test<3>()
    {
        // Test 3: Explicit label_for binding pass in LLPanel
        LLPanel::Params panel_p;
        panel_p.name("test_panel");
        panel_p.rect(LLRect(0, 100, 200, 0));
        LLPanel panel;
        panel.initFromParams(panel_p);

        LLTextBox::Params text_p;
        text_p.name("label_text");
        text_p.initial_value("UI Mode Label:");
        text_p.label_for("ui_mode_combo");
        text_p.rect(LLRect(10, 50, 100, 30));
        LLTextBox* text_ctrl = new LLTextBox(text_p);
        text_ctrl->initFromParams(text_p);
        panel.addChild(text_ctrl);

        LLComboBox::Params combo_p;
        combo_p.name("ui_mode_combo");
        combo_p.rect(LLRect(110, 50, 200, 30));
        LLComboBox* combo_ctrl = new LLComboBox(combo_p);
        combo_ctrl->initFromParams(combo_p);
        panel.addChild(combo_ctrl);

        panel.bindAccessibleLabels();

        ensure_equals("Explicit label_for binds accessible name to target control",
                      combo_ctrl->getAccessibleName(), "UI Mode Label:");
    }

    template<> template<>
    void lluictrl_test_object::test<4>()
    {
        // Test 4: Proximity Fallback binding pass in LLPanel
        LLPanel::Params panel_p;
        panel_p.name("fallback_panel");
        panel_p.rect(LLRect(0, 100, 300, 0));
        LLPanel panel;
        panel.initFromParams(panel_p);

        LLTextBox::Params text_p;
        text_p.name("unlinked_label");
        text_p.initial_value("Camera Angle:");
        text_p.rect(LLRect(10, 50, 100, 30));
        LLTextBox* text_ctrl = new LLTextBox(text_p);
        text_ctrl->initFromParams(text_p);
        panel.addChild(text_ctrl);

        LLLineEditor::Params line_p;
        line_p.name("camera_angle_input");
        line_p.rect(LLRect(110, 50, 250, 30));
        LLLineEditor* line_ctrl = new LLLineEditor(line_p);
        line_ctrl->initFromParams(line_p);
        panel.addChild(line_ctrl);

        panel.bindAccessibleLabels();

        ensure_equals("Proximity fallback binds adjacent text to input control",
                      line_ctrl->getAccessibleName(), "Camera Angle:");
    }

    template<> template<>
    void lluictrl_test_object::test<5>()
    {
        // Test 5: Precedence rule (explicit label or label_for takes precedence over proximity)
        LLPanel::Params panel_p;
        panel_p.name("precedence_panel");
        panel_p.rect(LLRect(0, 100, 300, 0));
        LLPanel panel;
        panel.initFromParams(panel_p);

        LLTextBox::Params text_p;
        text_p.name("unlinked_label");
        text_p.initial_value("Nearby Text:");
        text_p.rect(LLRect(10, 50, 100, 30));
        LLTextBox* text_ctrl = new LLTextBox(text_p);
        text_ctrl->initFromParams(text_p);
        panel.addChild(text_ctrl);

        LLCheckBoxControl::Params check_p;
        check_p.name("explicit_check");
        check_p.label("Explicit Checkbox Label");
        check_p.rect(LLRect(110, 50, 250, 30));
        LLCheckBoxControl* check_ctrl = new LLCheckBoxControl(check_p);
        check_ctrl->initFromParams(check_p);
        panel.addChild(check_ctrl);

        panel.bindAccessibleLabels();

        ensure_equals("Explicit label takes precedence over proximity fallback",
                      check_ctrl->getAccessibleName(), "Explicit Checkbox Label");
    }

    template<> template<>
    void lluictrl_test_object::test<6>()
    {
        // Test 6: Container isolation rule (proximity does not cross panel boundaries)
        LLPanel::Params outer_p;
        outer_p.name("outer_panel");
        outer_p.rect(LLRect(0, 200, 300, 0));
        LLPanel outer_panel;
        outer_panel.initFromParams(outer_p);

        LLTextBox::Params text_p;
        text_p.name("outer_label");
        text_p.initial_value("Outer Panel Text:");
        text_p.rect(LLRect(10, 150, 100, 130));
        LLTextBox* text_ctrl = new LLTextBox(text_p);
        text_ctrl->initFromParams(text_p);
        outer_panel.addChild(text_ctrl);

        LLPanel::Params inner_p;
        inner_p.name("inner_panel");
        inner_p.rect(LLRect(0, 100, 300, 0));
        LLPanel* inner_panel = new LLPanel;
        inner_panel->initFromParams(inner_p);
        outer_panel.addChild(inner_panel);

        LLLineEditor::Params line_p;
        line_p.name("inner_input");
        line_p.rect(LLRect(110, 50, 250, 30));
        LLLineEditor* line_ctrl = new LLLineEditor(line_p);
        line_ctrl->initFromParams(line_p);
        inner_panel->addChild(line_ctrl);

        // Run binding on inner_panel only
        inner_panel->bindAccessibleLabels();

        ensure_equals("Proximity fallback does not inherit text from parent panel",
                      line_ctrl->getAccessibleName(), "");
    }
}
