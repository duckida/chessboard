# frontend

This folder contains the Next.js frontend for the chessboard, which is displayed on the 3.5" TFT.

## deployment
The Next.js site is deployed at Vercel, under https://chessboard-moa.vercel.app. It can be deployed locally with static exports, `npm run build`.

To display the page in fullscreen kiosk on the Pi, we use Surf browser: `DISPLAY=:0 surf -F https://chessboard-moa.vercel.app/`
