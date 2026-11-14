import sys
import threading

import config
import panel
from bot import Bot


def main():
    cfg = config.load()
    if not cfg["bot_token"] or cfg["bot_token"].startswith("PUT_"):
        print("আগে config.json ফাইলে bot_token বসান।")
        sys.exit(1)

    threading.Thread(target=panel.run, daemon=True).start()
    print("এডমিন প্যানেল খুলতে টেলিগ্রামে বটকে /panel লিখুন")
    Bot().run()


if __name__ == "__main__":
    main()
