plugins {
    id("com.android.application")
}

android {
    namespace = "org.hypernova.launcher"
    compileSdk = 35

    defaultConfig {
        applicationId = "org.hypernova.launcher"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            // Signed with the debug key so the APK installs directly for testing.
            // Replace with a real release key before publishing to a store.
            signingConfig = signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
