/**
 * Mock Data Generator
 * 
 * Generates sample data based on field types for the Sandbox preview.
 * Uses simple random generators (no external dependencies).
 */

import type { FieldData } from "../components/FieldEditor";

// Sample data pools for realistic mock data
const SAMPLE_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"];
const SAMPLE_WORDS = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit"];
const SAMPLE_EMAILS = ["alice@example.com", "bob@test.org", "charlie@demo.io", "diana@sample.net"];
const SAMPLE_URLS = ["https://example.com", "https://test.org", "https://demo.io", "https://sample.net"];

/**
 * Random integer between min and max (inclusive)
 */
function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Random float between min and max with decimals
 */
function randomFloat(min: number, max: number, decimals = 2): number {
  const value = Math.random() * (max - min) + min;
  return parseFloat(value.toFixed(decimals));
}

/**
 * Random item from an array
 */
function randomItem<T>(arr: T[]): T {
  return arr[randomInt(0, arr.length - 1)];
}

/**
 * Generate random words
 */
function randomWords(count: number): string {
  return Array.from({ length: count }, () => randomItem(SAMPLE_WORDS)).join(" ");
}

/**
 * Generate a random date within the last year
 */
function randomDate(): string {
  const now = new Date();
  const daysAgo = randomInt(0, 365);
  const date = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);
  return date.toISOString().split("T")[0]; // YYYY-MM-DD
}

/**
 * Generate a random datetime within the last year
 */
function randomDateTime(): string {
  const now = new Date();
  const daysAgo = randomInt(0, 365);
  const date = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);
  return date.toISOString().slice(0, 16); // YYYY-MM-DDTHH:MM
}

/**
 * Generate a random UUID
 */
function randomUUID(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Generate a mock value for a specific field type
 */
export function generateMockValue(fieldType: string, fieldName: string): unknown {
  const lowerName = fieldName.toLowerCase();

  switch (fieldType) {
    case "str":
    case "text":
      // Context-aware generation based on field name
      if (lowerName.includes("name")) return randomItem(SAMPLE_NAMES);
      if (lowerName.includes("title")) return randomWords(3).charAt(0).toUpperCase() + randomWords(3).slice(1);
      if (lowerName.includes("description")) return randomWords(8);
      return randomWords(2);

    case "int":
      if (lowerName.includes("age")) return randomInt(18, 80);
      if (lowerName.includes("quantity") || lowerName.includes("count")) return randomInt(1, 100);
      if (lowerName.includes("year")) return randomInt(2000, 2030);
      return randomInt(1, 1000);

    case "float":
    case "Decimal":
      if (lowerName.includes("price") || lowerName.includes("amount") || lowerName.includes("cost")) {
        return randomFloat(10, 1000, 2);
      }
      if (lowerName.includes("rate") || lowerName.includes("percentage")) {
        return randomFloat(0, 100, 2);
      }
      return randomFloat(0, 100, 2);

    case "bool":
      return Math.random() > 0.5;

    case "date":
      return randomDate();

    case "datetime":
      return randomDateTime();

    case "UUID":
      return randomUUID();

    case "email":
      return randomItem(SAMPLE_EMAILS);

    case "url":
      return randomItem(SAMPLE_URLS);

    case "dict":
    case "json":
      return { key: randomWords(1), value: randomInt(1, 100) };

    case "list":
      return [randomWords(1), randomWords(1), randomWords(1)];

    case "Table":
      return []; // Empty child table

    case "Link":
      return randomUUID(); // Foreign key as ID reference

    default:
      return randomWords(2);
  }
}

/**
 * Generate a complete mock document based on field definitions
 */
export function generateMockDocument(fields: FieldData[]): Record<string, unknown> {
  const doc: Record<string, unknown> = {
    id: randomUUID(),
    created_at: randomDateTime(),
    updated_at: randomDateTime(),
  };

  for (const field of fields) {
    // Skip if field is not required and randomly skip 30% of optional fields
    if (!field.required && Math.random() < 0.3) {
      doc[field.name] = null;
      continue;
    }

    doc[field.name] = generateMockValue(field.type, field.name);
  }

  return doc;
}

/**
 * Generate multiple mock documents
 */
export function generateMockRows(fields: FieldData[], count: number): Record<string, unknown>[] {
  return Array.from({ length: count }, () => generateMockDocument(fields));
}

/**
 * Generate mock data for pagination testing
 */
export function generatePaginatedMockData(
  fields: FieldData[],
  totalCount: number,
  page: number,
  pageSize: number
): { data: Record<string, unknown>[]; total: number; page: number; pageSize: number } {
  // Generate deterministic data based on page
  const allData = generateMockRows(fields, totalCount);
  const startIndex = (page - 1) * pageSize;
  const data = allData.slice(startIndex, startIndex + pageSize);

  return {
    data,
    total: totalCount,
    page,
    pageSize,
  };
}
