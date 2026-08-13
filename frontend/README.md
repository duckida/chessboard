# frontend

This folder contains the Next.js frontend for the chessboard, which is displayed on the 3.5" TFT.

## deployment
It is recommended to statically compile the website using `npm run build` (on another computer), and host it using `nginx` on the Pi.

1. Install nginx: `sudo apt install nginx -y`
2. Add this to /etc/nginx/nginx.conf inside `http {`: `sudo nano  /etc/nginx/nginx.conf`
```
server {
        listen 80;
        server_name localhost;
        root  /var/www/html;
        index index.html;

        location / {
            try_files $uri $uri.html $uri/ /404.html;
        }
    }
```
3. Make /var/www/html accessible: `chmod 777 /var/www/html`
4. Move your compiled static website files to `/var/www/html`

## browser
To display the page in a fullscreen kiosk on the Pi, we use the Surf browser: `DISPLAY=:0 surf -F http://localhost/`

### systemd service
You can setup a systemd service to start the browser on boot: 
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
ExecStart=/usr/bin/surf -F http://localhost/

[Install]
WantedBy=graphical.target
```
3. `sudo systemctl daemon-reload`
4. `sudo systemctl enable frontend.service`
5. Reboot the Pi: `sudo reboot`
