#!/bin/bash

echo Marketing dashboard refreshing ...
while true
do
	# parallel data collection from advertising accounts and google analytics
	exec python3 ./scripts/AdsFacebook.py &
	exec python3 ./scripts/AdsSnapchat.py &
	exec python3 ./scripts/AdsTikTok.py &
	exec python3 ./scripts/GoogleAnalytics.py &
	# updating the dependent dashboard for marketing
	wait
	python3 ./scripts/Marketing.py
	break
done
echo Check /root/journal.log for more details.