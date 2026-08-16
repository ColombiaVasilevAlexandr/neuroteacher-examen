import argparse
import asyncio
from pathlib import Path

import edge_tts


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)
    args = parser.parse_args()
    words = Path(args.source).read_text(encoding="utf-8").split()
    text = " ".join(words[args.start:args.end or None])
    await edge_tts.Communicate(text, voice="ru-RU-DmitryNeural", rate="-5%").save(args.output)


asyncio.run(main())
