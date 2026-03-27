# DJ News — Spotify Mood DJ + VRT NWS

Android app dat een Spotify mood-gebaseerde DJ-set combineert met automatisch uurlijks VRT NWS nieuws.

## Features

- **4 mood-knoppen**: Chill 🌙 / Energy ⚡ / Focus 🎯 / Party 🎉
- **Spotify playlist per mood**: elke mood speelt een gecureerde shuffle-playlist
- **Automatisch VRT NWS nieuws**: elke dag op het uur, zonder interactie
- **Automatisch terug naar muziek**: na het nieuws hervat Spotify automatisch

## Vereisten

- Android 8.0+ (API 26+)
- **Spotify Premium** account
- **Spotify app** geïnstalleerd op het toestel

## Setup

### 1. Spotify Developer App registreren

1. Ga naar [developer.spotify.com](https://developer.spotify.com/dashboard)
2. Maak een nieuwe app aan
3. Voeg toe als Redirect URI: `spotify-djnews://callback`
4. Voeg de SHA-1 fingerprint van je keystore toe onder Android settings
5. Kopieer de Client ID

### 2. Spotify App Remote SDK

1. Download de Spotify App Remote SDK (AAR) via de Spotify Developer portal
2. Plaats het bestand als `app/libs/spotify-app-remote-release-0.8.0.aar`

### 3. Client ID instellen

Maak een `local.properties` bestand aan (of stel in als CI secret):

```
SPOTIFY_CLIENT_ID=jouw_client_id_hier
```

### 4. Builden

```bash
./gradlew assembleDebug
```

## Architectuur

```
MainActivity
    └── MainScreen (Compose)
        ├── MoodSelectorScreen (2×2 grid)
        └── NowPlayingBar (onderaan)

MusicPlayerService (Foreground Service)
    ├── SpotifyAppRemoteManager  ← Spotify App Remote SDK
    ├── NewsPlayerController     ← ExoPlayer voor VRT NWS
    ├── NewsTransitionManager    ← State machine: pause → news → resume
    └── NewsScheduler            ← AlarmManager exact uurlijks

NewsAlarmReceiver  ← Wordt getriggerd door AlarmManager op :00
BootReceiver       ← Herstelt alarm na herstart
```

## Audio Transitie Flow

```
Alarm op het uur
    ↓
Spotify pauseren
    ↓ (500ms)
ExoPlayer start VRT NWS podcast/stream
    ↓ (nieuws afgelopen)
ExoPlayer stopt, geeft audio focus vrij
    ↓ (300ms)
Spotify hervat
    ↓
Volgend alarm inplannen
```

## VRT NWS Bronnen

- **Primair**: Podcast RSS feed (max 3 min per aflevering, elk uur geüpload)
- **Fallback**: Live radiostream (als aflevering ouder is dan 65 min)
