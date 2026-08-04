export type ParsedSseEvent<T = unknown> = {
  event: string;
  data: T;
};

export function extractSseEvents(buffer: string): {
  events: ParsedSseEvent[];
  remainingBuffer: string;
} {
  const normalizedBuffer = buffer.replace(/\r\n/g, "\n");

  const blocks = normalizedBuffer.split("\n\n");

  const remainingBuffer = blocks.pop() ?? "";

  const events: ParsedSseEvent[] = [];

  for (const block of blocks) {
    if (!block.trim()) {
      continue;
    }

    let eventName = "message";
    const dataLines: string[] = [];

    for (const line of block.split("\n")) {
      if (line.startsWith(":")) {
        continue;
      }

      if (line.startsWith("event:")) {
        eventName = line.slice("event:".length).trim();

        continue;
      }

      if (line.startsWith("data:")) {
        dataLines.push(line.slice("data:".length).trimStart());
      }
    }

    if (dataLines.length === 0) {
      continue;
    }

    const rawData = dataLines.join("\n");

    let parsedData: unknown = rawData;

    try {
      parsedData = JSON.parse(rawData);
    } catch {
      // Keep non-JSON SSE payloads as strings.
    }

    events.push({
      event: eventName,
      data: parsedData,
    });
  }

  return {
    events,
    remainingBuffer,
  };
}
