plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.firestorm.viewer"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.firestorm.viewer"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.0.1"

        externalNativeBuild {
            cmake {
                cppFlags += listOf("-std=c++17")
            }
        }

        ndk {
            abiFilters += listOf("arm64-v8a")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
        debug {
            // keep defaults
        }
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
}
