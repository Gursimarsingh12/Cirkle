plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    id("com.google.devtools.ksp")
    id("com.google.dagger.hilt.android")
    alias(libs.plugins.navigation.safe.args)
    id("kotlin-parcelize")
}

android {
    namespace = "com.app.cirkle"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.app.cirkle"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
    buildFeatures{
        viewBinding = true
    }
}

dependencies {

    implementation("androidx.paging:paging-runtime:3.3.6")

    implementation("com.google.dagger:hilt-android:2.56.1")
    implementation(libs.androidx.swiperefreshlayout)
    implementation(libs.androidx.lifecycle.process)
    ksp("com.google.dagger:hilt-android-compiler:2.56.1")

    implementation (libs.gson)
    implementation (libs.retrofit)
    implementation (libs.converter.gson)


    implementation("com.squareup.moshi:moshi:1.15.2")
    ksp("com.squareup.moshi:moshi-kotlin-codegen:1.15.2")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.2")
    implementation("com.squareup.retrofit2:converter-moshi:3.0.0")

    implementation("com.squareup.okhttp3:logging-interceptor:5.0.0-alpha.17")

    implementation (libs.androidx.camera.core)
    implementation (libs.androidx.camera.camera2)
    implementation (libs.androidx.camera.lifecycle)
    implementation (libs.androidx.camera.view)

    //noinspection GradleDependency
    implementation(libs.kotlinx.coroutines.android)


    implementation(libs.androidx.navigation.fragment.ktx)
    implementation(libs.androidx.navigation.ui.ktx)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.activity)
    implementation(libs.androidx.constraintlayout)
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)

    implementation("androidx.security:security-crypto:1.0.0")

    implementation("com.github.bumptech.glide:glide:4.16.0")

    implementation("com.facebook.shimmer:shimmer:0.5.0")


}