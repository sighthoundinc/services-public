#!/usr/bin/env python3
from MCP import MCPClient
import os

def get_args():
    mcp_conf = {}
    mcp_conf["host"] = os.environ.get("MCP_HOST", "mcp")
    mcp_conf["port"] = os.environ.get("MCP_PORT", 9097)
    mcp_conf["username"] = os.environ.get("MCP_USERNAME", None)
    mcp_conf["password"] = os.environ.get("MCP_PASSWORD", None)
    print ("MCP configuration:", mcp_conf)
    return mcp_conf

def print_image(image):
    path = image.get("path", "undefined")
    type = image.get("type", "undefined")
    endTs = image.get("endTs", "undefined")
    print("  -", type, ":", path, "at", endTs)

def main():
    # getting the required information from the user 
    mcp_conf = get_args()
    # Create MCP Client
    mcp_client = MCPClient(mcp_conf)
    sources = mcp_client.list_sources()
    for source in sources:
        print("MCP source:", source)
        stats = mcp_client.get_stats(source)
        print("Source stats:")
        for stat in stats:
            print("  -", stat, ":", stats[stat])
        images = mcp_client.list_images("my-video")
        if len(images) != 0:
            print("Last 3 images:")
            for image in images[-3:]:
                print_image(image)
            print("First 3 images:")
            for image in images[:3]:
                print_image(image)
        else:
            print("No images found")
                
        # Get live HLS
        live = mcp_client.get_live_m3u8(source)
        print("Live HLS:\n", live, "\n")

        # Get oldest HLS
        oldestTs = int(stats.get("oldestTs", 0)/1000)
        next = oldestTs + 10
        oldest = mcp_client.get_m3u8(source, oldestTs, next)
        print("Oldest HLS:\n", oldest, "\n")
    
    

if __name__ == "__main__":
    main()