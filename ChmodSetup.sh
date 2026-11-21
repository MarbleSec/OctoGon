#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
echo "starting"
sleep 1
echo "starting on chpkgs"
sleep 0.5
chmod +x "$DIR/chpkgs.sh"
sleep 2
echo "[+] DONE!"
sleep 0.5
echo "starting on files"
chmod +x "$DIR/files.sh"
echo "[+]done"
echo "starting on BackdoorMaker"
chmod +x "$DIR/src/Tools/BackdoorMaker.sh"
echo "[+]done"
sleep 0.5
echo "starting on Deauth"
chmod +x "$DIR/src/Tools/deauth.sh"
echo "[+]done"
sleep 0.5
echo "starting on Sql Injector"
chmod +x "$DIR/src/Tools/SqlInjector.sh"
echo "[+]done"
sleep 0.5
echo "starting on command Injector"
chmod +x "$DIR/src/Tools/commix.sh"
echo "[+]done"
sleep 0.5
echo "starting on xss scanner"
chmod +x "$DIR/src/Tools/xss.sh"
echo "[+]done"
sleep 0.5
echo "starting on wpscanner scanner"
chmod +x "$DIR/src/Tools/wpscan.sh"
echo "[+]done"
sleep 0.5
echo "starting on netdiscover scanner"
chmod +x "$DIR/src/Tools/netdiscover.sh"
echo "[+]done"
sleep 3
echo "[+]Complete"
# </list other dirs here/>
sleep 0.3

sleep 1
