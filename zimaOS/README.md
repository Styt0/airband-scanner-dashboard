# ZimaOS Homeserver — Management Hub

## Server Access Details
- **IP Address:** `192.168.0.237`
- **SSH Command:** `ssh zimaos` (Key-based authentication)
- **SSH Key Location:** `C:/Users/Tom/.ssh/zimaos`
- **Username:** `styto`
- **ZimaOS Login:** `styto / beelinkbee`
- **Sudo Command:** `echo beelinkbee | sudo -S <command>`

## Docker Management (Remote via SSH)
- **Check PS:** `ssh zimaos 'docker ps'`
- **Check Status:** `ssh zimaos 'docker ps --format "table {{.Names}}\t{{.Status}}"'`
- **Restart Container:** `ssh zimaos 'docker restart <naam>'`
- **Check Logs:** `ssh zimaos 'docker logs <naam> --tail 50'`

## Project Goal
Manage, document, and automate server tasks for the ZimaOS environment, providing a central location for configuration tracking and automation scripts.
