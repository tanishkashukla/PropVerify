export const DOCUMENT_TYPES = [
  { id: 'sale_deed', label: 'Sale Deed' },
  { id: 'property_card', label: 'Property Card' },
  { id: 'index_ii', label: 'Index II' },
  { id: '7_12_extract', label: '7/12 Extract' },
  { id: 'id_document', label: 'ID Document' },
];

const LABELS_BY_ID = Object.fromEntries(DOCUMENT_TYPES.map(({ id, label }) => [id, label]));
const IDS_BY_NORMALIZED_LABEL = new Map(
  DOCUMENT_TYPES.flatMap(({ id, label }) => [
    [label.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, ''), id],
    [id, id],
  ]),
);

export function canonicalDocumentType(value) {
  if (!value) return '';
  const normalized = String(value).trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
  // Accept the historical extract_7_12 spelling at the UI boundary.
  return IDS_BY_NORMALIZED_LABEL.get(normalized) || (normalized === 'extract_7_12' ? '7_12_extract' : '');
}

export function documentTypeLabel(value) {
  return LABELS_BY_ID[canonicalDocumentType(value)] || value || '';
}
