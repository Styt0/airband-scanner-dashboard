package com.djnews.service

import android.app.Notification
import android.app.PendingIntent
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleService
import androidx.lifecycle.lifecycleScope
import com.djnews.DjNewsApplication.Companion.CHANNEL_ID_PLAYBACK
import com.djnews.MainActivity
import com.djnews.R
import com.djnews.data.news.VrtNwsRepository
import com.djnews.data.spotify.SpotifyAppRemoteManager
import com.djnews.domain.model.Mood
import com.djnews.domain.model.PlaybackState
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class MusicPlayerService : LifecycleService() {

    @Inject lateinit var spotifyManager: SpotifyAppRemoteManager
    @Inject lateinit var vrtNwsRepository: VrtNwsRepository
    @Inject lateinit var newsScheduler: NewsScheduler

    private lateinit var newsPlayerController: NewsPlayerController
    private lateinit var newsTransitionManager: NewsTransitionManager

    override fun onCreate() {
        super.onCreate()
        newsPlayerController = NewsPlayerController(this, vrtNwsRepository) {
            // Called when news ends — resume Spotify
            onNewsEnded()
        }
        newsTransitionManager = NewsTransitionManager(
            spotifyManager = spotifyManager,
            newsPlayerController = newsPlayerController
        )
        startForeground(NOTIFICATION_ID, buildNotification("Ready"))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)
        when (intent?.action) {
            ACTION_PLAY_MOOD -> {
                val mood = intent.getStringExtra(EXTRA_MOOD)
                    ?.let { Mood.valueOf(it) } ?: return START_STICKY
                playMood(mood)
            }
            ACTION_PLAY_NEWS -> {
                lifecycleScope.launch { newsTransitionManager.transitionToNews() }
            }
            ACTION_STOP -> stopSelf()
        }
        return START_STICKY
    }

    private fun playMood(mood: Mood) {
        lifecycleScope.launch {
            val result = spotifyManager.connect()
            if (result.isSuccess) {
                spotifyManager.playMood(mood)
                newsScheduler.scheduleNextHourAlarm()
                updateNotification("Playing: ${mood.label}")
            } else {
                updateNotification("Spotify connection failed")
            }
        }
    }

    private fun onNewsEnded() {
        lifecycleScope.launch {
            newsTransitionManager.transitionToMusic()
            newsScheduler.scheduleNextHourAlarm()
            updateNotification("Resuming music")
        }
    }

    private fun updateNotification(text: String) {
        val nm = getSystemService(android.app.NotificationManager::class.java)
        nm.notify(NOTIFICATION_ID, buildNotification(text))
    }

    private fun buildNotification(text: String): Notification {
        val openApp = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )
        return NotificationCompat.Builder(this, CHANNEL_ID_PLAYBACK)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_media_play)
            .setContentIntent(openApp)
            .setOngoing(true)
            .build()
    }

    override fun onDestroy() {
        newsPlayerController.release()
        spotifyManager.disconnect()
        newsScheduler.cancel()
        super.onDestroy()
    }

    override fun onBind(intent: Intent): IBinder? {
        super.onBind(intent)
        return null
    }

    companion object {
        const val ACTION_PLAY_MOOD = "com.djnews.ACTION_PLAY_MOOD"
        const val ACTION_PLAY_NEWS = "com.djnews.ACTION_PLAY_NEWS"
        const val ACTION_STOP = "com.djnews.ACTION_STOP"
        const val EXTRA_MOOD = "extra_mood"
        private const val NOTIFICATION_ID = 1001
    }
}
