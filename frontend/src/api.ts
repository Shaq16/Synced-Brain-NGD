const BACKEND_URL = "http://localhost:8000";

export interface CitationItem {
  source: string;
  chunk_index: number;
  text: string;
  page: number | null;
  score?: number | null;
}

export interface QueryResponse {
  answer: string;
  citations: CitationItem[];
  retrieval?: { top_k: number; scores: number[] } | null;
}

export interface QueryFilters {
  source_prefix?: string;
  doc_type?: "md" | "pdf";
}

export async function queryBrain(
  question: string,
  topK = 5,
  filters?: QueryFilters,
  debug = false
): Promise<QueryResponse> {
  const res = await fetch(`${BACKEND_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK, filters, debug }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Query failed (${res.status}): ${errText}`);
  }
  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
