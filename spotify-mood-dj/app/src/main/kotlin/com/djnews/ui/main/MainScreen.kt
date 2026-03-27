package com.djnews.ui.main

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.djnews.ui.mood.MoodSelectorScreen
import com.djnews.ui.nowplaying.NowPlayingBar

@Composable
fun MainScreen(
    viewModel: MainViewModel = hiltViewModel()
) {
    val selectedMood by viewModel.selectedMood.collectAsStateWithLifecycle()
    val playbackState by viewModel.playbackState.collectAsStateWithLifecycle()
    val currentTrack by viewModel.currentTrack.collectAsStateWithLifecycle()

    Scaffold(
        bottomBar = {
            NowPlayingBar(
                playbackState = playbackState,
                currentTrack = currentTrack
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            MoodSelectorScreen(
                selectedMood = selectedMood,
                onMoodSelected = viewModel::selectMood,
                modifier = Modifier.weight(1f)
            )
        }
    }
}
