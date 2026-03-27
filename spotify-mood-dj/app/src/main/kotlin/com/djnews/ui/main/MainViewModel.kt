package com.djnews.ui.main

import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.djnews.data.spotify.SpotifyAppRemoteManager
import com.djnews.domain.model.Mood
import com.djnews.domain.model.PlaybackState
import com.djnews.domain.model.TrackInfo
import com.djnews.service.MusicPlayerService
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import javax.inject.Inject

private val KEY_LAST_MOOD = stringPreferencesKey("last_mood")

@HiltViewModel
class MainViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val spotifyManager: SpotifyAppRemoteManager,
    private val dataStore: DataStore<Preferences>
) : ViewModel() {

    private val _selectedMood = MutableStateFlow<Mood?>(null)
    val selectedMood: StateFlow<Mood?> = _selectedMood.asStateFlow()

    private val _playbackState = MutableStateFlow<PlaybackState>(PlaybackState.Idle)
    val playbackState: StateFlow<PlaybackState> = _playbackState.asStateFlow()

    val currentTrack: StateFlow<TrackInfo?> = spotifyManager.currentTrack

    init {
        // Restore last selected mood from DataStore
        viewModelScope.launch {
            dataStore.data
                .map { prefs -> prefs[KEY_LAST_MOOD]?.let { Mood.valueOf(it) } }
                .collect { mood -> _selectedMood.value = mood }
        }
    }

    fun selectMood(mood: Mood) {
        _selectedMood.value = mood
        _playbackState.value = PlaybackState.PlayingMusic(mood, null)

        viewModelScope.launch {
            dataStore.edit { it[KEY_LAST_MOOD] = mood.name }
        }

        startServiceWithMood(mood)
    }

    fun triggerNewsManually() {
        val intent = Intent(context, MusicPlayerService::class.java).apply {
            action = MusicPlayerService.ACTION_PLAY_NEWS
        }
        startService(intent)
    }

    private fun startServiceWithMood(mood: Mood) {
        val intent = Intent(context, MusicPlayerService::class.java).apply {
            action = MusicPlayerService.ACTION_PLAY_MOOD
            putExtra(MusicPlayerService.EXTRA_MOOD, mood.name)
        }
        startService(intent)
    }

    private fun startService(intent: Intent) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(intent)
        } else {
            context.startService(intent)
        }
    }
}
