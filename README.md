# EMA 13/50 Binance Futures Scanner (1H)

This bot scans all Binance USDT-M perpetual futures pairs and alerts a Discord webhook whenever the **13 EMA crosses bullishly above the 50 EMA** on the **1-hour timeframe**.

## Features
- Scans all USDT-M futures pairs
- Checks last 5 closed candles on startup
- Then checks every hour
- Sends Discord alerts
- Duplicate alert protection
- Railway-ready deployment

## Deployment (Railway)
1. Push this repo to GitHub  
2. Create a new Railway project  
3. Deploy from GitHub  
4. Railway will run the worker automatically

## Run locally
