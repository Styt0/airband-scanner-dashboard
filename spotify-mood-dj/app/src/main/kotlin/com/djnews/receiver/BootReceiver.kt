package com.djnews.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.djnews.service.NewsScheduler
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

private const val TAG = "BootReceiver"

@AndroidEntryPoint
class BootReceiver : BroadcastReceiver() {

    @Inject lateinit var newsScheduler: NewsScheduler

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED ||
            intent.action == Intent.ACTION_MY_PACKAGE_REPLACED
        ) {
            Log.d(TAG, "Device booted — re-scheduling news alarm")
            newsScheduler.scheduleNextHourAlarm()
        }
    }
}
