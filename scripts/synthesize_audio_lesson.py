import argparse
import asyncio
from pathlib import Path

import edge_tts


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output_dir")
    parser.add_argument("prefix")
    args = parser.parse_args()
    words = Path(args.source).read_text(encoding="utf-8").split()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    chunks = [words[index:index + 300] for index in range(0, len(words), 300)]
    await asyncio.gather(*[
        edge_tts.Communicate(" ".join(chunk), voice="ru-RU-DmitryNeural", rate="-5%").save(output_dir / f"{args.prefix}-{index + 1:02}.mp3")
        for index, chunk in enumerate(chunks)
    ])


asyncio.run(main())
