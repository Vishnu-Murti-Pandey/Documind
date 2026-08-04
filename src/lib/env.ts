import { z } from "zod";

const publicEnvironmentSchema = z.object({
  NEXT_PUBLIC_API_URL: z
    .string()
    .url("NEXT_PUBLIC_API_URL must be a valid URL"),
});

const parsedEnvironment = publicEnvironmentSchema.safeParse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
});

if (!parsedEnvironment.success) {
  console.error(
    "Invalid frontend environment variables:",
    parsedEnvironment.error.flatten().fieldErrors,
  );

  throw new Error("Frontend environment configuration is invalid.");
}

export const env = parsedEnvironment.data;
