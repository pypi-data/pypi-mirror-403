from mcp.server.fastmcp import FastMCP
from . import fetch_info
from .main import open_video as main_open_video
import argparse

parser = argparse.ArgumentParser(description="Start an mcp server")

parser.add_argument("--host", 
                    type = str, 
                    help = "specify the host address"
                    )
parser.add_argument("--port",
                    type = int,
                    help = "specify the port"
                    )
args = parser.parse_args()

set_default = lambda x, default: default if x is None else x
mcp = FastMCP("Anime From Terminal", 
              json_response=True,
              host=set_default(args.host, "0.0.0.0"),
              port=set_default(args.port, "6767")
              )

@mcp.tool()
def get_search_results(search_query: str) -> list:
    """
    Searches for anime that matches the search_query. This may return a lot of results so please use your best judgement to filter out the results.
    """
    return fetch_info.get_all_search_results(search_query)

@mcp.tool()
def get_episodes(anime_id: str) -> dict:
    """
    Gets the list of episodes given an anime_id (can be found via search)
    """
    return fetch_info.get_episodes(anime_id)

@mcp.tool()
def get_servers(episode_id: str) -> dict:
    """
    Gets the server names given the episode id.
    """
    return fetch_info.get_servers(episode_id)

@mcp.tool()
def get_stream(episode_id: str, server_name: str, server_type: str):
    """
    Gets the stream given the episode id, server type (sub or dub) and server name (HD-1, HD-2, etc).
    """
    return fetch_info.get_stream(episode_id=episode_id,
                                 server_name=server_name,
                                 server_type=server_type
                                 )

@mcp.prompt(
    name="default",
    description = "How to use this MCP server"
)
def default_prompt():
    return """
This is an MCP server that has access to anime information, video stream information and the ability to open mpv to watch that stream.

If the user wants to watch anime, here's the general flow:
1. First get the anime that the user has specified, or prompt them if none was given
2. Now search that anime using get_all_search_results
3. Now use your best judgement to filter out all the search result such that the anime name or id is very close to the input of the user. Check whether the user approves of the anime you've chosen. If not, select the most likely choice
4. Now get the episodes and prompt the user if no episodes were chosen.
5. Now get and choose the servers automatically (the first server is usually the best) in order to get the server name and type (sub or dub or mixed or raw). If the user haven't specified the type, prompt them for it.
6. Now grab the important data to pass into get_stream
7. Once you have the information of get_stream, get the one with the highest quality and just pass the whole dictionary you've chosen into open_video.

Otherwise, if the user just wants to prompt for some general anime information, use your best judgement to find what ther user is looking for.
"""

@mcp.tool(
    name = "Open Video",
    description = "Open the video using mpv where the video is a dictionary is formatted the same as one of stream of get_stream"
)
def open_video(video:dict) -> None:
    """
    Opens the video using mpv while handling all the subtitles and referrer.
    
    Args:
        video: a video dictionary containing the stream, the referrer, and the subtitles

    Return:
        None
    """
    main_open_video(video)

def main():
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
