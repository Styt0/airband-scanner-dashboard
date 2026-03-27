package com.djnews.service

import android.content.Context
import android.util.Log
import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import com.djnews.data.news.VrtNwsRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

private const val TAG = "NewsPlayerController"

/**
 * Manages news audio playback via ExoPlayer.
 * Handles audio focus automatically (handleAudioFocus = true).
 * Calls [onPlaybackEnded] when the episode finishes.
 */
class NewsPlayerController(
    context: Context,
    private val vrtNwsRepository: VrtNwsRepository,
    private val onPlaybackEnded: () -> Unit
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    private val player: ExoPlayer = ExoPlayer.Builder(context)
        .setAudioAttributes(
            AudioAttributes.Builder()
                .setUsage(C.USAGE_MEDIA)
                .setContentType(C.AUDIO_CONTENT_TYPE_SPEECH)
                .build(),
            /* handleAudioFocus = */ true
        )
        .setHandleAudioBecomingNoisy(true)
        .build()
        .also { exoPlayer ->
            exoPlayer.addListener(object : Player.Listener {
                override fun onPlaybackStateChanged(playbackState: Int) {
                    if (playbackState == Player.STATE_ENDED) {
                        Log.d(TAG, "News playback ended")
                        onPlaybackEnded()
                    }
                }
            })
        }

    fun startNews() {
        scope.launch {
            try {
                val audioUrl = vrtNwsRepository.getNewsAudioUrl()
                Log.d(TAG, "Starting news: $audioUrl")
                player.setMediaItem(MediaItem.fromUri(audioUrl))
                player.prepare()
                player.play()
            } catch (e: Exception) {
                Log.e(TAG, "Error starting news: ${e.message}")
                // Still call onPlaybackEnded so music resumes
                onPlaybackEnded()
            }
        }
    }

    fun stop() {
        player.stop()
        player.clearMediaItems()
    }

    fun release() {
        player.release()
    }
}
