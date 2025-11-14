import { pool } from '../config/database';

export interface ICD10Code {
  id: number;
  code: string;
  name: string;
  source: string;
  validation_status: string;
  created_at: Date;
}

export interface ICD10Category {
  headCode: string;
  headName: string;
  count: number;
}

export interface ICD10Detail {
  code: string;
  name: string;
}

/**
 * Get ICD-10 HEAD categories based on search term with smart filtering
 * Example: "pneumonia" → J12, J13, J14, J15, J18 (general)
 *          "pneumonia cacar air" → J01.2 only (specific)
 */
export async function getICD10Categories(searchTerm: string): Promise<ICD10Category[]> {
  try {
    // Split search term into words for multi-word matching
    const words = searchTerm.toLowerCase().split(/\s+/).filter(w => w.length > 2);
    
    // Build dynamic query based on word count
    let query: string;
    let params: any[];
    
    if (words.length > 1) {
      // Multi-word: more specific matching (AND logic)
      // Match codes where name contains ALL words
      const conditions = words.map((_, i) => `LOWER(name) LIKE $${i + 1}`).join(' AND ');
      const wordPatterns = words.map(w => `%${w}%`);
      
      query = `
        WITH matched_codes AS (
          SELECT 
            code,
            name,
            CASE 
              WHEN code ~ '^[A-Z][0-9]{2}\\.[0-9]' THEN SUBSTRING(code FROM 1 FOR 3)
              ELSE code
            END as head_code
          FROM icd10_master
          WHERE 
            ${conditions}
            AND validation_status = 'official'
          ORDER BY code
        )
        SELECT 
          head_code as "headCode",
          MIN(name) as "headName",
          COUNT(*) as count
        FROM matched_codes
        WHERE head_code ~ '^[A-Z][0-9]{2}$'
        GROUP BY head_code
        ORDER BY head_code
      `;
      params = wordPatterns;
    } else {
      // Single word: broader matching (general search)
      query = `
        WITH matched_codes AS (
          SELECT 
            code,
            name,
            CASE 
              WHEN code ~ '^[A-Z][0-9]{2}\\.[0-9]' THEN SUBSTRING(code FROM 1 FOR 3)
              ELSE code
            END as head_code
          FROM icd10_master
          WHERE 
            LOWER(name) LIKE $1
            AND validation_status = 'official'
          ORDER BY code
        )
        SELECT 
          head_code as "headCode",
          MIN(name) as "headName",
          COUNT(*) as count
        FROM matched_codes
        WHERE head_code ~ '^[A-Z][0-9]{2}$'
        GROUP BY head_code
        ORDER BY head_code
      `;
      params = [`%${searchTerm.toLowerCase()}%`];
    }

    const result = await pool.query(query, params);
    return result.rows;
  } catch (error) {
    console.error('Error fetching ICD-10 categories:', error);
    throw error;
  }
}

/**
 * Get detailed subcodes for a specific HEAD code
 * Example: "J12" → J12.0, J12.1, J12.2, J12.3, J12.8, J12.9
 */
export async function getICD10Details(headCode: string): Promise<ICD10Detail[]> {
  try {
    const query = `
      SELECT 
        code,
        name
      FROM icd10_master
      WHERE 
        code LIKE $1
        AND code ~ '^[A-Z][0-9]{2}\\.[0-9]'
        AND validation_status = 'official'
      ORDER BY code
    `;

    const result = await pool.query(query, [`${headCode}.%`]);
    return result.rows;
  } catch (error) {
    console.error('Error fetching ICD-10 details:', error);
    throw error;
  }
}

/**
 * Get ICD-10 hierarchy (categories + details) based on search term
 */
export async function getICD10Hierarchy(searchTerm: string) {
  try {
    const categories = await getICD10Categories(searchTerm);
    
    // Get details for each category
    const hierarchyPromises = categories.map(async (category) => {
      const details = await getICD10Details(category.headCode);
      return {
        ...category,
        details
      };
    });

    const hierarchy = await Promise.all(hierarchyPromises);
    return hierarchy;
  } catch (error) {
    console.error('Error fetching ICD-10 hierarchy:', error);
    throw error;
  }
}

/**
 * Search ICD-10 codes with fuzzy matching
 */
export async function searchICD10Codes(searchTerm: string, limit: number = 50): Promise<ICD10Code[]> {
  try {
    const query = `
      SELECT 
        id,
        code,
        name,
        source,
        validation_status,
        created_at
      FROM icd10_master
      WHERE 
        LOWER(name) LIKE $1
        OR LOWER(code) LIKE $1
      ORDER BY 
        CASE 
          WHEN code LIKE $1 THEN 1
          WHEN LOWER(name) LIKE $2 THEN 2
          ELSE 3
        END,
        code
      LIMIT $3
    `;

    const result = await pool.query(query, [
      `%${searchTerm.toLowerCase()}%`,
      `${searchTerm.toLowerCase()}%`,
      limit
    ]);
    
    return result.rows;
  } catch (error) {
    console.error('Error searching ICD-10 codes:', error);
    throw error;
  }
}

/**
 * Get specific ICD-10 code by code
 */
export async function getICD10ByCode(code: string): Promise<ICD10Code | null> {
  try {
    const query = `
      SELECT 
        id,
        code,
        name,
        source,
        validation_status,
        created_at
      FROM icd10_master
      WHERE code = $1
      LIMIT 1
    `;

    const result = await pool.query(query, [code]);
    return result.rows[0] || null;
  } catch (error) {
    console.error('Error fetching ICD-10 by code:', error);
    throw error;
  }
}
