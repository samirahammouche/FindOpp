function firstMessage(value) {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return firstMessage(value[0]);
  if (value && typeof value === "object") {
    return firstMessage(Object.values(value)[0]);
  }
  return null;
}

export async function readApiResponse(response, fallbackMessage) {
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(firstMessage(data) || fallbackMessage);
  }

  if (!data) {
    throw new Error("The server returned an invalid response.");
  }

  return data;
}
