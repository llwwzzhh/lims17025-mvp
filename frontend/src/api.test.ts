import { describe, expect, it } from 'vitest';
import { label, statusLabel } from './api';

describe('status labels', () => {
  it('translates known workflow states to Chinese', () => {
    expect(label('pending')).toBe('待评审');
    expect(label('in_progress')).toBe('进行中');
    expect(label('approved')).toBe('已批准');
  });
  it('keeps unknown states visible rather than hiding them', () => {
    expect(label('custom_state')).toBe('custom_state');
  });
  it('has labels for common workflow state groups', () => {
    expect(statusLabel.open).toBe('开放');
    expect(statusLabel.out_of_service).toBe('停用');
  });
});
