# Requirements

- `python` must be installed (if you're on windows, go to microsoft store or something to install it)

Check by running:

```bash
python --version
```

- [`mpv`](https://mpv.io/installation/) must be installed

Check by running:

```bash
mpv --version
```

On Linux, `mpv` can be installed using your package manager (or it might already be installed).

On Windows, it's gonna be a bit difficult.

You can try to download `mpv` just from the [offical site](https://mpv.io/installation/).

Here are the steps we used:

1. Went to [https://github.com/shinchiro/mpv-winbuild-cmake/releases](https://github.com/shinchiro/mpv-winbuild-cmake/releases)
2. Extract it to a folder somewhere
3. Add it as an environmental variable following [this tutorial](https://youtu.be/ow2jROvxyH4?si=78CbPF8AE2st7Vtd)
4. Check that it works by doing `mpv --version`, if not, find another tutorial (sorry, Windows kinda sucks for developing)

## (Optional) for downloading anime

- `ffmpeg` must be installed

```bash
ffmpeg -version
```

On linux, you know what to do. Idk how you'd install it on windows tho.

- `yt-dlp` must be installed

```bash
yt-dlp -version
```

I would honestly just install the [binaries (executable)](https://github.com/yt-dlp/yt-dlp/releases) and add it to path for both linux and windows. 

# Usage

## Watch anime

It's very easy to try it out using `uv`.

```bash
uvx --from anime-from-terminal anime
```

And there you go!

Otherwise, simply install it using `pip`

```bash
pip install anime-from-terminal
```

Now run:

```bash
anime
```

## Download anime

Download a whole anime season in one command (with subs too).

First, create a directory where you want all the episodes to be stored in and `cd` into it.

```bash
mkdir baan
cd baan
```

Now just run

```bash
uvx --from anime-from-terminal anime_dl --search "baan" --type "sub"
```

Enjoy.

A handy command to sort the episodes:

```bash
perl-rename 's/Ep\. (\d+): Episode \1/"Ep. ".sprintf("%04d",$1).": Episode ".sprintf("%04d",$1)/e' *.mkv
```

## Clanker Support!

Watch anime through MCP! Connect to an AI agent and let pull up the anime for you.

Start the mcp server:

```bash
uvx --from anime-from-terminal mcp --host 0.0.0.0 --port 6969
```

Connect to the mcp server through an mcp client. For example, in `opencode`, edit the `~/.config/opencode/opencode.json` and input:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "anime-from-terminal": {
      "command":["uvx", "--from", "anime-from-terminal", "mcp"]
      "type": "remote",
      "enabled": true,
      "url": "http://localhost:6767/mcp",
    }
  }
}
```

# About

This is simply a `cli` front end for the hi-anime scraping API by @f4rh4d-4hmed [this is their repo](https://github.com/f4rh4d-4hmed/HiAnime-Api).

# TODO

- [x] Write all the api interfaces
  - [x] searching (also continuously fetches until there's no more next page)
  - [x] getting episodes
  - [x] getting servers
  - [x] fetching the stream data
- [x] Figure out a way to query using `iterfzf` correctly
- [x] Figure out all the prompt and the flow of the program
- [x] Handle errors
- [x] Kinda wanna implement an mcp server for the api too (but that's for another time)
