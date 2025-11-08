/*
  # AI-CLAIM Lite Analysis Storage

  1. New Tables
    - `analyses`
      - `id` (uuid, primary key)
      - `diagnosis` (text) - Input diagnosis
      - `procedure` (text) - Input tindakan/procedure
      - `medication` (text) - Input obat/medication
      - `result` (jsonb) - AI analysis results
      - `created_at` (timestamptz) - Timestamp
  
  2. Security
    - Enable RLS on `analyses` table
    - Add policy for public access (since no auth required for lite version)
*/

CREATE TABLE IF NOT EXISTS analyses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  diagnosis text NOT NULL,
  procedure text NOT NULL,
  medication text NOT NULL,
  result jsonb NOT NULL,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access"
  ON analyses
  FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Allow public insert access"
  ON analyses
  FOR INSERT
  TO public
  WITH CHECK (true);