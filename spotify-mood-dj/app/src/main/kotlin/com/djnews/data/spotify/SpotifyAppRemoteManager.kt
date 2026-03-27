package com.djnews.data.spotify

import android.content.Context
import android.util.Log
import com.djnews.BuildConfig
import com.djnews.domain.model.Mood
import com.djnews.domain.model.TrackInfo
import com.spotify.android.appremote.api.ConnectionParams
import com.spotify.android.appremote.api.Connector
import com.spotify.android.appremote.api.SpotifyAppRemote
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

private const val TAG = "SpotifyAppRemote"

@Singleton
class SpotifyAppRemoteManager @Inject constructor(
    private val context: Context
) {
    private var appRemote: SpotifyAppRemote? = null

    private val _currentTrack = MutableStateFlow<TrackInfo?>(null)
    val currentTrack: StateFlow<TrackInfo?> = _currentTrack.asStateFlow()

    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected.asStateFlow()

    suspend fun connect(): Result<Unit> = suspendCancellableCoroutine { cont ->
        if (appRemote?.isConnected == true) {
            cont.resume(Result.success(Unit))
            return@suspendCancellableCoroutine
        }

        val params = ConnectionParams.Builder(BuildConfig.SPOTIFY_CLIENT_ID)
            .setRedirectUri(BuildConfig.SPOTIFY_REDIRECT_URI)
            .showAuthView(true)
            .build()

        SpotifyAppRemote.connect(context, params, object : Connector.ConnectionListener {
            override fun onConnected(remote: SpotifyAppRemote) {
                appRemote = remote
                _isConnected.value = true
                subscribeToPlayerState()
                Log.d(TAG, "Connected to Spotify")
                if (cont.isActive) cont.resume(Result.success(Unit))
            }

            override fun onFailure(error: Throwable) {
                _isConnected.value = false
                Log.e(TAG, "Failed to connect: ${error.message}")
                if (cont.isActive) cont.resume(Result.failure(error))
            }
        })

        cont.invokeOnCancellation { disconnect() }
    }

    fun disconnect() {
        appRemote?.let {
            SpotifyAppRemote.disconnect(it)
            appRemote = null
            _isConnected.value = false
        }
    }

    fun playMood(mood: Mood) {
        val remote = appRemote ?: run {
            Log.w(TAG, "playMood called but not connected")
            return
        }
        remote.playerApi.setShuffle(true)
        remote.playerApi.play(mood.spotifyPlaylistUri)
        Log.d(TAG, "Playing mood ${mood.name}: ${mood.spotifyPlaylistUri}")
    }

    fun pause() {
        appRemote?.playerApi?.pause()
    }

    fun resume() {
        appRemote?.playerApi?.resume()
    }

    private fun subscribeToPlayerState() {
        appRemote?.playerApi?.subscribeToPlayerState()?.setEventCallback { state ->
            val track = state.track
            if (track != null) {
                _currentTrack.value = TrackInfo(
                    title = track.name,
                    artist = track.artist.name,
                    albumArtUrl = null // album art fetched separately via ImagesApi if needed
                )
            }
        }
    }
}
