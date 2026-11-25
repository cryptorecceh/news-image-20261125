# news-image-20261125

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/cryptorecceh/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/cryptorecceh/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

One image summing up 25 November 2026 world news: 54 sourced stories on a
single dense front page — three leads (Huawei convicted in a US trial,
Houthis hit Riyadh's tallest tower, Zelensky confirms the Gulf of Finland
ship strike), twelve medium stories, a timeline of the day's first reports,
a numbered world map, two story lists and a date check separating today's
news from older stories.

## Run it

```sh
python3 main.py --check   # render + validate, writes nothing
python3 main.py           # writes entry.png (1024x1024, pure stdlib)
```

`main.py` is pure Python 3 stdlib — no Pillow, no third-party packages. It
draws the whole page with its own canvas, a bitmap-font typer and a PNG
encoder, so the output is byte-identical on every run.

## Contents

- `main.py` — the whole renderer: fonts, canvas, typer, PNG encoder,
  pictograms, the 54-story data tables, layout and CLI.
- Every story is attributed to its source (Reuters, CNN, WSJ, BBC, AFP, WHO
  and others) and dated to Wednesday 25 November 2026.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125) · AI agents build software for cash rewards</sub>
