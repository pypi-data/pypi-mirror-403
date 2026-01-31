from . import fetch_info
import argparse
import iterfzf
from .main import get_lookup_search_results
import subprocess
import json
from colorama import init, Fore

init()

# tempfile for when we're converting stuff

TMP_FILE = ".tmp.mkv"
def main():
    parser = argparse.ArgumentParser(description="Download a whole season of anime given the anime ID")
    parser.add_argument("--search",
                        type = str,
                        help = "Find the anime ID you're trying to search"
                        )
    parser.add_argument("--anime-id", 
                        type = str, 
                        help = "The anime ID on hianime"
                        )
    parser.add_argument("--type",
                        choices = ['sub', 'dub', 'raw', 'mixed'], 
                        help = "Choose whether it's sub, dub, raw or mixed"
                        )

    args = parser.parse_args()

    anime_id = None
    if args.anime_id != None:
        anime_id = args.anime_id
    elif args.search != None:
        search_results = fetch_info.get_all_search_results(args.search)
        if len(search_results) == 0:
            exit(f"{Fore.RED}Error:{Fore.RESET} no search results found")
        elif len(search_results) == 1:
            anime_id = search_results[0]["id"]
        else:
            search_results = get_lookup_search_results(search_results)
            choice = iterfzf.iterfzf(map(lambda x: x["display"], search_results.values()),
                                     ansi=True)
            anime_id = search_results[choice]["id"]
    else:
        raise parser.error(message="Please enter an anime-id using --anime-id or search an anime using --search")

    if args.type == None:
        raise parser.error(message="Please enter an anime type (sub, dub, raw or mixed) using --type")

    episodes = fetch_info.get_episodes(anime_id)
    #print(episodes["episodes"])

    for episode in episodes["episodes"]:
        # first get the server info
        servers = fetch_info.get_servers(episode["id"])

        # choose the first server
        server = filtered_servers = servers["servers"][args.type][0]
        #print(server)

        stream = fetch_info.get_stream(episode_id=episode["id"],
                                       server_name=server["name"],
                                       server_type=server["type"]
                                       )

        video = stream["videos"][0]

        #choose the highest quality

        output_video = f"{episode["title"]}.mkv"

        yt_dlp_cmd = [
            "yt-dlp",
            video["url"],
            "--referer", video["referer"],
            "-o", TMP_FILE
        ]

        subprocess.run(yt_dlp_cmd)

        #print(json.dumps(episode, indent=2))

        subtitle_list = video["subtitles"]

        ffmpeg_cmd = ["ffmpeg", 
                      "-i", TMP_FILE
                      ]
        subtitle_url_list = []
        mapping = []
        metadata = []
        for i, subtitle in enumerate(subtitle_list):
            subtitle_url_list += ["-i", subtitle["url"]]
            mapping += ["-map", str(i+1)]
            metadata += [f"-metadata:s:s:{i}", 
                         f"language={subtitle['label']}"
                         ]

        ffmpeg_cmd += subtitle_url_list
        ffmpeg_cmd += ["-map", "0"] + mapping
        ffmpeg_cmd += metadata
        ffmpeg_cmd += ["-c", "copy",
                       "-c:s", "srt",
                       output_video
                       ]
        
        #print(ffmpeg_cmd)
        subprocess.run(ffmpeg_cmd)
        remove_tmp_cmd = [
            "rm", TMP_FILE
        ]
        subprocess.run(remove_tmp_cmd)

if __name__ == "__main__":
    main()

