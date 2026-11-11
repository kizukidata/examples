# MCP setup

Three Kizuki bundles are listed in the official MCP Registry and served by the Apify MCP server at `https://mcp.apify.com`. Pick one bundle: fewer tools means a shorter tool list for the model and fewer accidental runs.

| Bundle | Registry name | Tools |
|---|---|---|
| Hiring Signals | `io.github.kizukidata/hiring-signals` | `linkedin-jobs-feed`, `linkedin-company-monitor` |
| News Monitoring | `io.github.kizukidata/news-monitoring` | `google-news-feed`, `youtube-channel-monitor`, `telegram-channel-feed` |
| RAG Ingest | `io.github.kizukidata/rag-ingest` | `youtube-transcripts`, `pdf-to-markdown`, `url-to-markdown` |

URLs are in `claude-desktop.json` and `cursor-mcp.json`. Any other client that accepts a remote MCP URL takes the same URL.

## Claude Desktop

Merge one entry from `claude-desktop.json` into `claude_desktop_config.json`:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

Restart Claude Desktop. On the first tool call your browser opens so you can sign in to Apify and approve access; usage is billed to that Apify account.

## Claude Code

```bash
claude mcp add --transport http kizuki-rag "https://mcp.apify.com?tools=kizukidata/youtube-transcripts,kizukidata/pdf-to-markdown,kizukidata/url-to-markdown"
```

Then run `/mcp` in Claude Code to check that the server is connected. Apify also ships a plugin that installs the server together with its Agent Skills:

```text
/plugin marketplace add apify/apify-claude-code-plugin
/plugin install apify@apify
/reload-plugins
```

Then open `/mcp`, enable `plugin:apify:apify` and authenticate. See [Apify plugins](https://docs.apify.com/agents/plugins).

## Cursor

Use the one-click link on [mcp.apify.com](https://mcp.apify.com), or let the Apify CLI write the config including your token:

```bash
apify mcp install cursor
```

By hand: copy an entry from `cursor-mcp.json` into `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (this project), then enable it in Cursor's MCP settings.

## Bearer token instead of sign-in

If the client cannot open a browser, pass an Apify API token in the header:

```json
{
  "mcpServers": {
    "kizuki-rag": {
      "url": "https://mcp.apify.com?tools=kizukidata/youtube-transcripts,kizukidata/pdf-to-markdown,kizukidata/url-to-markdown",
      "headers": { "Authorization": "Bearer <your Apify API token>" }
    }
  }
}
```

Keep the token in the client's own config or environment, not in a file you commit.

## Client without remote MCP support

Run the Apify MCP server locally through stdio (Node.js 22 or later). Every Actor call is then made with your token from the environment:

```json
{
  "mcpServers": {
    "kizuki": {
      "command": "npx",
      "args": ["-y", "@apify/actors-mcp-server", "--tools", "kizukidata/youtube-transcripts,kizukidata/pdf-to-markdown,kizukidata/url-to-markdown"],
      "env": { "APIFY_TOKEN": "<your Apify API token>" }
    }
  }
}
```

## What the agent sees

Each Actor becomes one tool. `call-actor` (or the Actor's own tool) starts a run, waits up to 45 seconds and returns the run status and the dataset ID; `get-dataset-items` reads the rows. A row that carries an `error`, `status: "scan"`/`"failed"`, or `detailsStatus: "blocked"` is returned with the reason and is not charged.

Cost: same per-row prices as the API: youtube-transcripts $0.0020, pdf-to-markdown $0.0022, url-to-markdown $0.0014, google-news-feed $0.0017, telegram-channel-feed $0.0020, youtube-channel-monitor $0.0011, linkedin-jobs-feed $0.0012, linkedin-company-monitor $0.0020. Free tier. No per-item charge when an input yields nothing; the run start fee still applies.
