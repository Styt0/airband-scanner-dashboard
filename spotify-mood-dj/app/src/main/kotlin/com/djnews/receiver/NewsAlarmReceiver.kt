package com.djnews.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import com.djnews.service.MusicPlayerService

private const val TAG = "NewsAlarmReceiver"

class NewsAlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        Log.d(TAG, "News alarm fired — starting news playback")

        val serviceIntent = Intent(context, MusicPlayerService::class.java).apply {
            action = MusicPlayerService.ACTION_PLAY_NEWS
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(serviceIntent)
        } else {
            context.startService(serviceIntent)
        }
    }
}
