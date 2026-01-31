from . import fetch_info
import iterfzf
import json
from colorama import init, Fore, Back, Style
import re
from functools import reduce
import subprocess

init(autoreset=True)

def strip_ansi(text):
    """Strips all of the ansi code from a string"""
    return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)

def get_lookup_search_results(search_results:list) -> dict:
    """
    Formats the search results into a key that can be chosen, and all the info stored in the value.

    Args:
        search_results: a list of search results

    Return:
        A dictionary with keys that work well with `iterfzf`
    """

    # this will be displayed in the fzf interface
    get_display_info = lambda result: f"{Fore.CYAN} {result['title']} {Style.RESET_ALL} {Fore.YELLOW} ({result['id']})"

    ret_dict = dict()
    for result in search_results:
        to_display = get_display_info(result)
        # strip it because iterfzf will strip all the ansi code
        ret_dict[strip_ansi(to_display)] = result | {"display":to_display}
    return ret_dict

INPUT_PROMPT = f"""{Fore.CYAN}Watch anime from the terminal {Fore.RED}(no ads, no bullshit){Fore.CYAN}
┃
┗━❯ {Fore.YELLOW}Enter an anime: {Style.RESET_ALL}"""

def pretty_print_dict(input_dict:dict) -> None:
    """return a string represention of a depth 1 dictionary in a presentable way"""
    for k, v in input_dict.items():
        print(f"{Fore.YELLOW} {k}{Style.RESET_ALL}: {v}")

def get_lookup_episodes(episode_list:list) -> dict:
    """
    Formats the lists of episodes such that the key can be displayed in iterfzf

    Args:
        episode_list: the list in the "episodes" parameter in the response from the API
    Return:
        A dictionary of episodes with keys that can be looked up after using `iterfzf`
    """

    is_filler = lambda episode: bool(episode["is_filler"])
    ret_dict = dict()
    get_display_info = lambda episode: f"{Fore.CYAN + episode['title']} {Fore.YELLOW}(#{episode['number']}) {Back.RED + Fore.RESET+ Style.BRIGHT + 'filler' if is_filler(episode) else ''}{Style.RESET_ALL}"
    for episode in episode_list:
        to_display = get_display_info(episode)
        ret_dict[strip_ansi(to_display)] = episode|{"display":to_display}
    return ret_dict

def get_lookup_servers(server_list:list) -> dict:
    """
    Formats the list of servers such that it can be accessed nicely through `iterfzf`.

    Args:
        server_list: the list of servers

    Return:
        A dictionary of with a nice string representation of the dictionary as key
    """

    ret_dict = dict()
    get_display_info = lambda server: f"{Fore.CYAN + server['name']}{Fore.YELLOW} ({server['type']})"
    for server in server_list:
        to_display = get_display_info(server)
        ret_dict[strip_ansi(to_display)] = server | {'display':to_display}
    return ret_dict

def get_lookup_videos(video_list:list) -> dict:
    """
    Formats the list of videos such that it can be nicely accessed through `iterfzf`.

    Args:
        video_list: the list of videos 

    Return:
        A dictionary with keys as a string representation of videos (to display through `iterfzf`)
    """

    ret_dict = dict()
    get_display_info = lambda video: Fore.CYAN + video['quality']
    for video in video_list:
        to_display = get_display_info(video)
        ret_dict[strip_ansi(to_display)] = video | {"display":to_display}
    return ret_dict

def open_video(video:dict) -> None:
    """
    Opens the video using mpv while handling all the subtitles and referrer.
    
    Args:
        video: a video dictionary containing the stream, the referrer, and the subtitles

    Return:
        None
    """
    # preparing the subtitles list
    subtitles_list = [f"--sub-file={subtitle['url']}" for subtitle in video['subtitles']]
    subprocess.run(["mpv",
                    f"--referrer={video['referer']}", # referrer is misspelled, cuz of the api
                    video['url']
                    ] + subtitles_list)

def main():
    anime_name = input(INPUT_PROMPT)
    search_results = fetch_info.get_all_search_results(anime_name)
    lookup_search_results = get_lookup_search_results(search_results)
    choice = iterfzf.iterfzf(map(lambda result: result["display"],lookup_search_results.values()),
                            ansi=True,
                            prompt="Choose anime: ")

    chosen_anime = lookup_search_results[choice]


    print(f"{Fore.MAGENTA} You've chosen: ")
    pretty_print_dict(lookup_search_results[choice])

# now we have the anime, we need to get episodes now
    episodes_dict = fetch_info.get_episodes(chosen_anime["id"])
    episodes_list = episodes_dict["episodes"]
    lookup_episodes_list = get_lookup_episodes(episodes_list)
    choice = iterfzf.iterfzf(map(lambda episode: episode["display"],
                                lookup_episodes_list.values()),
                            ansi=True,
                            prompt="Choose episodes: "
                            )

    chosen_episode = lookup_episodes_list[choice]

    while True:
        servers = fetch_info.get_servers(chosen_episode["id"])
        server_list = servers["servers"]
        flattened_servers = reduce(lambda a, b: a + b,
                                server_list.values()
                                )

# this is a misnomer, it's not a list
        lookup_server_list = get_lookup_servers(flattened_servers)

        choice = iterfzf.iterfzf(map(lambda server: server["display"],
                                    lookup_server_list.values()),
                                ansi=True,
                                prompt="Choose server: "
                                )

        server_chosen = lookup_server_list[choice]

        stream = fetch_info.get_stream(chosen_episode["id"],
                                    server_chosen["name"],
                                    server_chosen["type"]
                                    )

        video_list = stream["videos"]

        lookup_videos = get_lookup_videos(video_list)

        choice = iterfzf.iterfzf(map(lambda video: video["display"],
                                    lookup_videos.values()),
                                ansi=True,
                                prompt="Choose videos: "
                                )

        video = lookup_videos[choice]

        open_video(video)

        #after opening the video, go to new episode (if can)
        episode_number = int(chosen_episode["number"])
        if  episode_number >= len(episodes_list):
            break
        chosen_episode = episodes_list[episode_number]

        print(f"\n{Fore.MAGENTA} Continuing to episode {Fore.YELLOW}{episode_number + 1} ")
        pretty_print_dict(chosen_episode)

        confirm = None
        while confirm not in {'y', 'n'}:
            confirm = input(f"{Fore.CYAN} Do you want to continue? {Fore.YELLOW}(Y/n){Style.RESET_ALL} ").lower()

        if confirm == 'n':
            break



if __name__ == "__main__":
    main()
