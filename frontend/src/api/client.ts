export type KnowledgeBase = {
  product_line: string;
  product_version: string;
  created_at: string;
};

export type Source = {
  document_id: string;
  file_name: string;
  product_line: string;
  product_version: string;
  chunk_index: number;
  score: number;
  text: string;
};

export type QueryResponse = {
  answer: string;
  grounded_summary: string;
  sources: Source[];
  used_supplemental_knowledge: boolean;
  generated_by_ai: boolean;
  generation_notice: string;
  supplemental_note: string | null;
};

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof payload.detail === 'string' ? payload.detail : response.statusText);
  }
  return response.json() as Promise<T>;
}

export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  return parseJson(await fetch('/api/knowledge-bases'));
}

export async function loginAdmin(adminSecret: string): Promise<void> {
  await parseJson<{ status: string }>(
    await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ admin_secret: adminSecret }),
    }),
  );
}

export async function createKnowledgeBase(productLine: string, productVersion: string): Promise<KnowledgeBase> {
  return parseJson(
    await fetch('/api/knowledge-bases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ product_line: productLine, product_version: productVersion }),
    }),
  );
}

export async function uploadDocument(productLine: string, productVersion: string, file: File): Promise<void> {
  const form = new FormData();
  form.append('file', file);
  const params = new URLSearchParams({ product_line: productLine, product_version: productVersion });
  await parseJson(
    await fetch(`/api/admin/upload?${params.toString()}`, {
      method: 'POST',
      credentials: 'include',
      body: form,
    }),
  );
}

export async function queryAssistant(
  productLine: string,
  productVersion: string,
  question: string,
): Promise<QueryResponse> {
  return parseJson(
    await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_line: productLine,
        product_version: productVersion,
        question,
      }),
    }),
  );
}
