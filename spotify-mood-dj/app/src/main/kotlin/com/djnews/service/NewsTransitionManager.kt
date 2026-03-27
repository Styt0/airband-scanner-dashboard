package com.djnews.service

import android.util.Log
import com.djnews.data.spotify.SpotifyAppRemoteManager
import kotlinx.coroutines.delay
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

private const val TAG = "NewsTransition"

/**
 * State machine controlling the ordered Spotify pause → news → Spotify resume sequence.
 * A Mutex prevents re-entrant or concurrent transitions.
 */
class NewsTransitionManager(
    private val spotifyManager: SpotifyAppRemoteManager,
    private val newsPlayerController: NewsPlayerController
) {
    private val mutex = Mutex()

    private enum class State { IDLE, PAUSING_SPOTIFY, PLAYING_NEWS, RESUMING_SPOTIFY }
    private var state = State.IDLE

    suspend fun transitionToNews() = mutex.withLock {
        if (state != State.IDLE) {
            Log.w(TAG, "transitionToNews called in state $state — ignoring")
            return@withLock
        }
        Log.d(TAG, "→ PAUSING_SPOTIFY")
        state = State.PAUSING_SPOTIFY
        spotifyManager.pause()

        // Give Spotify time to release audio focus
        delay(500)

        Log.d(TAG, "→ PLAYING_NEWS")
        state = State.PLAYING_NEWS
        newsPlayerController.startNews()
    }

    suspend fun transitionToMusic() = mutex.withLock {
        if (state != State.PLAYING_NEWS) {
            Log.w(TAG, "transitionToMusic called in state $state — ignoring")
            return@withLock
        }
        Log.d(TAG, "→ RESUMING_SPOTIFY")
        state = State.RESUMING_SPOTIFY
        newsPlayerController.stop()

        // Short pause so ExoPlayer fully releases audio output
        delay(300)

        spotifyManager.resume()
        Log.d(TAG, "→ IDLE")
        state = State.IDLE
    }
}
