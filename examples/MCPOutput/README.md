# MCP Output Example

This example prints MCP data to console

## Quickstart

```bash
docker-compose up
```

## Example output

```bash
example-mcp-output  | MCP configuration: {'host': 'mcp', 'port': '9097', 'username': 'root', 'password': 'root'}
example-mcp-output  | Connecting to mcp://root:*****@mcp:9097
example-mcp-output  | MCP source: my-video
example-mcp-output  | Source stats:
example-mcp-output  |   - oldestTs : 1678199663763
example-mcp-output  |   - newestTs : 1678300020507
example-mcp-output  |   - numberOfVideos : 569
example-mcp-output  |   - numberOfImages : 6219
example-mcp-output  |   - fileSize : 1068389022
example-mcp-output  |   - sourceId : my-video
example-mcp-output  | Last 3 images:
example-mcp-output  |   - image : output/image/my-video/16783/1678300020207.jpg at 2023-03-08T18:27:00.207Z
example-mcp-output  |   - image : output/image/my-video/16783/1678300020357.jpg at 2023-03-08T18:27:00.357Z
example-mcp-output  |   - image : output/image/my-video/16783/1678300020507.jpg at 2023-03-08T18:27:00.507Z
example-mcp-output  | First 3 images:
example-mcp-output  |   - image : output/image/my-video/16782/1678291124428.jpg at 2023-03-08T15:58:44.428Z
example-mcp-output  |   - image : output/image/my-video/16782/1678291280134.jpg at 2023-03-08T16:01:20.134Z
example-mcp-output  |   - image : output/image/my-video/16782/1678291280284.jpg at 2023-03-08T16:01:20.284Z
example-mcp-output  | Live HLS:
example-mcp-output  |  #EXTM3U
example-mcp-output  | #EXT-X-VERSION:3
example-mcp-output  | #EXT-X-MEDIA-SEQUENCE:1678299996
example-mcp-output  | #EXT-X-TARGETDURATION:9.400000
example-mcp-output  | #EXTINF:9.400000,
example-mcp-output  | #EXT-X-PROGRAM-DATE-TIME:2023-03-08T18:26:36.771Z
example-mcp-output  | segment/output/video/my-video/16782/1678299996771.ts
example-mcp-output  | #EXT-X-ENDLIST
example-mcp-output  |  
example-mcp-output  | 
example-mcp-output  | Oldest HLS:
example-mcp-output  |  #EXTM3U
example-mcp-output  | #EXT-X-VERSION:3
example-mcp-output  | #EXT-X-MEDIA-SEQUENCE:0
example-mcp-output  | #EXT-X-TARGETDURATION:9.400000
example-mcp-output  | #EXTINF:9.400000,
example-mcp-output  | #EXT-X-PROGRAM-DATE-TIME:2023-03-07T14:34:23.763Z
example-mcp-output  | segment/output/video/my-video/16781/1678199663763.ts
example-mcp-output  | #EXT-X-ENDLIST
```