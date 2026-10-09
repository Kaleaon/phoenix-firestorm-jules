/**
 * @file lluictrl_test.cpp
 * @brief Unit tests for LLUICtrl accessibility binding and label_for functionality
 */

#include "linden_common.h"
#include "lltut.h"

#include "../lluictrl.h"

namespace
{
    class TestControl : public LLUICtrl
    {
    public:
        TestControl(const LLUICtrl::Params& p) : LLUICtrl(p) {}
    };

    class TestCompositeControl : public LLUICtrl
    {
    public:
        TestCompositeControl(const LLUICtrl::Params& p)
            : LLUICtrl(p), mChildEditor(nullptr)
        {
            LLUICtrl::Params child_p;
            child_p.name("child_editor");
            mChildEditor = new TestControl(child_p);
            addChild(mChildEditor);
        }

        virtual void setAccessibleName(const std::string& name) override
        {
            LLUICtrl::setAccessibleName(name);
            if (mChildEditor)
            {
                mChildEditor->setAccessibleName(name);
            }
        }

        TestControl* getChildEditor() const { return mChildEditor; }

    private:
        TestControl* mChildEditor;
    };
}

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

        TestControl ctrl(p);
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
        // Test 2: Composite controls forward setAccessibleName to child controls
        LLUICtrl::Params comp_p;
        comp_p.name("composite_test");
        TestCompositeControl composite(comp_p);
        composite.setAccessibleName("Composite Label");

        ensure_equals("TestCompositeControl accessible name set", composite.getAccessibleName(), "Composite Label");
        ensure_equals("Child editor inherited accessible name", composite.getChildEditor()->getAccessibleName(), "Composite Label");
    }

    template<> template<>
    void lluictrl_test_object::test<3>()
    {
        // Test 3: LLUICtrl default accessible_name and label_for are empty
        LLUICtrl::Params default_p;
        default_p.name("default_ctrl");
        TestControl default_ctrl(default_p);
        default_ctrl.initFromParams(default_p);

        ensure_equals("Default label_for is empty", default_ctrl.getLabelFor(), "");
        ensure_equals("Default accessible_name is empty", default_ctrl.getAccessibleName(), "");
    }
}
