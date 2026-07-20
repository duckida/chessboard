# frontend

This folder contains the Next.js frontend for the chessboard, which is displayed on the 3.5" TFT.

## deployment
The Next.js site is deployed at Vercel, under https://chessboard-moa.vercel.app. It can be deployed locally with static exports, `npm run build`.

To display the page in fullscreen kiosk on the Pi, we use Surf browser: `DISPLAY=:0 surf -F https://chessboard-moa.vercel.app/`

## systemd service
You can also setup a systemd service to start the browser on boot: 
1. `sudo systemctl edit --full frontend.service --force`
2. Paste this in:
```
[Unit]
Description=Frontend Kiosk Service
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
WorkingDirectory=/home/pi
ExecStartPre=/bin/sh -c 'for i in $(seq 1 60); do xdpyinfo >/dev/null 2>&1 && exit 0; sleep 1; done; exit 1'
ExecStart=/usr/bin/surf -F https://chessboard-moa.vercel.app/

[Install]
WantedBy=graphical.target
```
3. `sudo systemctl daemon-reload`
4. `sudo systemctl enable frontend.service`
5. Reboot the Pi: `sudo reboot`
