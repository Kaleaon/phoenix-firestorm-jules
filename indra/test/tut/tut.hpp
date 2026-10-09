#ifndef TUT_HPP
#define TUT_HPP

#include <string>
#include <exception>
#include <iostream>
#include <sstream>

namespace tut
{
    class failure : public std::exception
    {
        std::string mMsg;
    public:
        failure(const std::string& msg) : mMsg(msg) {}
        const char* what() const noexcept override { return mMsg.c_str(); }
    };

    inline void ensure(const std::string& msg, bool cond)
    {
        if (!cond) throw failure(msg);
    }

    inline void ensure(bool cond)
    {
        if (!cond) throw failure("ensure failed");
    }

    template<typename T1, typename T2>
    inline void ensure_equals(const std::string& msg, const T1& actual, const T2& expected)
    {
        if (!(actual == expected))
        {
            std::stringstream ss;
            ss << msg << " [expected: " << expected << ", actual: " << actual << "]";
            throw failure(ss.str());
        }
    }

    template<typename T1, typename T2>
    inline void ensure_equals(const T1& actual, const T2& expected)
    {
        ensure_equals("ensure_equals failed", actual, expected);
    }

    template<typename Data>
    struct test_group
    {
        std::string name;
        test_group(const std::string& n) : name(n) {}
        struct object
        {
            Data data;
            std::string test_name;
            void set_test_name(const std::string& tn) { test_name = tn; }
            template<int N> void test() {}
        };
    };
}

#endif
