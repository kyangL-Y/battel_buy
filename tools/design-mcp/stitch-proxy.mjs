import { StitchProxy } from "@google/stitch-sdk";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

function getAuthConfig() {
  const apiKey = process.env.STITCH_API_KEY;
  const accessToken = process.env.STITCH_ACCESS_TOKEN;
  const projectId = process.env.GOOGLE_CLOUD_PROJECT;

  if (apiKey) {
    return { apiKey };
  }

  if (accessToken) {
    return {
      accessToken,
      projectId,
    };
  }

  throw new Error(
    "Missing Stitch credentials. Set STITCH_API_KEY, or set STITCH_ACCESS_TOKEN and GOOGLE_CLOUD_PROJECT.",
  );
}

async function main() {
  const proxy = new StitchProxy(getAuthConfig());
  const transport = new StdioServerTransport();
  await proxy.start(transport);
}

main().catch((error) => {
  console.error("[stitch-proxy] Failed to start:", error.message);
  process.exit(1);
});
