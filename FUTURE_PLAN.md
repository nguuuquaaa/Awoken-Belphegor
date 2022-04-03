So by the end of April, all bots will be required message intent or some sort to send normal messages for commands, *or* just go slash commands and YOLO. Since discord explicitly disapproves of using message intent for bot commands (iirc), slash commands is the only choice left.

So I'll do that.

Which means Belphegor bot will undergo complete overhaul.
No more `bel say some shitty stuff` -> Enter.
It's now `/say` -> select Belphegor from the list of 412412984565464 bots with the same `say` command -> `some shitty stuff` -> Enter.

Since these slash commands have different interface than message commands, which means I have a lot of rewriting to process, so I may as well remake Belphegor from scratch (holy shit) (actually I'll still copy old codes over so it's not exactly *from scratch*).

So here's the plan for now:
1. Since Otogi is already EoS, may as well not keep the commands anymore. The bot name/avatar and old repo is enough to remind everyone of the game.
2. Server management, tags/stickers (this sticker is different from discord sticker, as it exists long before), and random images will be removed due to low usage.
3. No more PSO2 EQ alert, as it's better to go to ARKS Fleet server and follow the EQ alert channel. Also no more item/price search since pso-hack had been down for a long while.
4. The weapons/units search (which is the only one left of PSO2) will proooobably be kept (need to stop procrastination ugh)
5. GFL and IS stuff will be kept, and with some enhancements (also same as above ugh).
6. Music stuff prob requires a lot of overhaul before going up, so it's will be unavailable for a while.
7. Misc commands will be ported over, and fast.
8. Experimental (presence tracking) commands will be kept I guess. No one actually uses it but it's there so image_processing.py doesn't collect dust.

That's all for now I guess.
If anyone has any question, suggestion, or request, pls send to my [deserted supported server](https://discord.gg/qnavjMy) since I mostly speak in gaming servers (yeeeeeeeah right that's kinda the reason for procrastination, games). I will try to answer most questions, but as I am bad at socializing I usually don't initiate conversations.