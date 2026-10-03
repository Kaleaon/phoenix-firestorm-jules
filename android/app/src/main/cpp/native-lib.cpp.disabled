#include <jni.h>
#include <string>

extern "C" JNIEXPORT jstring JNICALL
Java_com_firestorm_viewer_FirestormNative_version(JNIEnv* env, jobject /*thiz*/) {
    std::string version = "android-bootstrap";
    return env->NewStringUTF(version.c_str());
}
