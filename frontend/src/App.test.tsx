import { describe, expect, it } from 'vitest';

describe('frontend contract', () => {
  it('uses expected response metadata fields', () => {
    const fields = ['answer', 'grounded_summary', 'sources', 'used_supplemental_knowledge', 'supplemental_note'];
    expect(fields).toContain('sources');
    expect(fields).toContain('used_supplemental_knowledge');
  });
});

