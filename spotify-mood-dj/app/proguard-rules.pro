# Spotify App Remote SDK
-keep class com.spotify.android.appremote.** { *; }
-keep class com.spotify.protocol.** { *; }

# Retrofit + Gson
-keepattributes Signature
-keepattributes *Annotation*
-keep class retrofit2.** { *; }
-keep class com.google.gson.** { *; }
-keep class com.djnews.data.** { *; }
-keep class com.djnews.domain.model.** { *; }

# Media3
-keep class androidx.media3.** { *; }
