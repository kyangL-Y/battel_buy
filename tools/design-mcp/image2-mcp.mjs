import { randomUUID } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import * as z from "zod/v4";

const DEFAULT_BASE_URL = "https://ai.emqo.top";
const DEFAULT_MODEL = "gpt-image-2";
const DEFAULT_OUTPUT_DIR = "E:/battel/.tmp/image2";

function getEnv(name, fallback = "") {
  return process.env[name] || fallback;
}

function getConfig() {
  const apiKey = getEnv("IMAGE2_API_KEY") || getEnv("OPENAI_API_KEY");
  if (!apiKey) {
    throw new Error("Missing IMAGE2_API_KEY. Set IMAGE2_API_KEY before starting the image2 MCP server.");
  }

  return {
    apiKey,
    baseUrl: getEnv("IMAGE2_BASE_URL", DEFAULT_BASE_URL).replace(/\/+$/, ""),
    model: getEnv("IMAGE2_MODEL", DEFAULT_MODEL),
  };
}

function sanitizeFilename(value) {
  const cleaned = String(value || "")
    .trim()
    .replace(/[<>:"/\\|?*\u0000-\u001f]/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");

  return cleaned || `image2-${randomUUID()}`;
}

async function saveImage(image, outputDir, filenameBase) {
  await mkdir(outputDir, { recursive: true });

  const filePath = path.join(outputDir, `${sanitizeFilename(filenameBase)}.png`);

  if (image.b64_json) {
    await writeFile(filePath, Buffer.from(image.b64_json, "base64"));
    return filePath;
  }

  if (image.url) {
    const response = await fetch(image.url);
    if (!response.ok) {
      throw new Error(`Failed to download generated image: HTTP ${response.status}`);
    }
    await writeFile(filePath, Buffer.from(await response.arrayBuffer()));
    return filePath;
  }

  throw new Error("Image response did not include b64_json or url.");
}

async function generateImage(args) {
  const config = getConfig();
  const response = await fetch(`${config.baseUrl}/v1/images/generations`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: args.model || config.model,
      prompt: args.prompt,
      size: args.size,
      quality: args.quality,
      n: 1,
    }),
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.message || payload?.error?.message || `HTTP ${response.status}`;
    throw new Error(`Image2 generation failed: ${message}`);
  }

  const image = payload?.data?.[0];
  if (!image) {
    throw new Error("Image2 generation response did not include data[0].");
  }

  const savedPath = await saveImage(
    image,
    args.output_dir || DEFAULT_OUTPUT_DIR,
    args.filename || `image2-${new Date().toISOString().replace(/[:.]/g, "-")}`,
  );

  return {
    saved_path: savedPath,
    model: args.model || config.model,
    size: args.size,
    quality: args.quality,
    revised_prompt: image.revised_prompt || "",
  };
}

const server = new McpServer({
  name: "battel-image2",
  version: "0.1.0",
});

server.registerTool(
  "generate_image",
  {
    description:
      "Generate an image through the image2 OpenAI-compatible gateway and save it as a local PNG. Reads credentials from IMAGE2_API_KEY.",
    inputSchema: {
      prompt: z.string().min(1).describe("Detailed image prompt."),
      size: z
        .enum(["auto", "1024x1024", "1536x1024", "1024x1536", "2048x1152", "2048x2048", "3840x2160", "2160x3840"])
        .default("1536x1024")
        .describe("Image size supported by gpt-image-2."),
      quality: z.enum(["low", "medium", "high", "auto"]).default("high"),
      model: z.string().optional().describe("Override model. Defaults to IMAGE2_MODEL or gpt-image-2."),
      output_dir: z.string().optional().describe("Output directory. Defaults to E:/battel/.tmp/image2."),
      filename: z.string().optional().describe("Filename without extension."),
    },
    outputSchema: {
      saved_path: z.string(),
      model: z.string(),
      size: z.string(),
      quality: z.string(),
      revised_prompt: z.string(),
    },
  },
  async (args) => {
    const structuredContent = await generateImage(args);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(structuredContent, null, 2),
        },
      ],
      structuredContent,
    };
  },
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[image2-mcp] running on stdio");
}

main().catch((error) => {
  console.error("[image2-mcp] Failed to start:", error.message);
  process.exit(1);
});
